
#include  <util/parity.h>

//WATCH OUT!!
//For receiving we are processing the INVERTED Manchester signal
//For sending we generate the NON-INVERTED Manchester signal, direct and delayed 250ms
//  so the half-bit values are inverted between them

//Start sequence is 16 half bits: 0101010101000111
//  then each frame is 32 half bits, starting in 0b01, next 22 data half-bits in the middle and finally 2 half-bits even parity plus 6 half bits fill 0b101010
const word sequenceStart = 0b0101010101000111;

//End of multi-frame reception, sequence and mask
const word sequenceEnd = 0x8070;
const word maskEnd = 0x8077;

//Frame alignment, sequence and mask
const word sequenceFrameOdd = 0x8000;
const word sequenceFrameEven = 0x0007;
const word maskFrame = 0x8007;

//For detection of incorrect intrabit transitions
const word checkTransitions = 0xFFFF;


//TESTING VALUES for testing plugging RX-DAT-INV to constant data or external fuction generators
//const word sequenceEnd = 0x0;
//const word sequenceFrame = 0x0;
//const word sequenceStart = 0b1111111111111111;
//const word sequenceStart = 0b0000000000000000;
//const word sequenceStart = 0b0101010101010101;
//const word checkTransitions = 0x0;

//Max numebr of consecutive frames that can be received
const int MAX_FRAMES_RX = 256;

//All cycles values are calculated for a 600Mhz core clock
const int WAIT_CYCLES_RX = 30000; //Time we wait for a response frame after transmission
const int WAIT_CYCLES_RX_PENDING_TX = 5000; //Wait time for a response frame if not reception expected
const int WAIT_CYCLES_RX_SAMPLE = 85; //Cycles between signal samples, approx 8Mhz for 75 cycles (125ns) but can be increased slightly to reduce the probability of incorrect sampling due to clock drift
const int WAIT_CYCLES_TX = 300; //Half-bit duration for transmission
const int WAIT_CYCLES_TX_DLY = 150;  //Delay for TX-DATA-DLY, approx 250ns

//The Teensy LED is the speed problem indicator, if it lights on something is being processed very slowly and delaying signal sampling
const int PIN_OVERFLOW = 13;

//Output pins to twinax drivers
const int PIN_TX_ACT = 4;
const int PIN_OUT = 5;
const int PIN_OUT_DLY = 6;

//Input from twinax receiver
const int PIN_IN = 7;

//Enable dverbose debug over serial connection, not recommended for stable operation
const int ENABLEDEBUG = 0;


//Initialize things
void setup()
{
  // Open serial communications and wait for port to open:
  Serial.begin(57600);
  while (!Serial) {
    ; // wait for serial port to connect.
  }
  //Serial.println("[DEBUG] Starting...");

  //Shit to initialize cycle count readings
  ARM_DEMCR    |= ARM_DEMCR_TRCENA;
  ARM_DWT_CTRL |= ARM_DWT_CTRL_CYCCNTENA;
  ARM_DWT_CYCCNT = 0;

  //Set pin modes
  pinMode(PIN_OVERFLOW, OUTPUT);
  pinMode(PIN_IN, INPUT);
  pinMode(PIN_TX_ACT, OUTPUT);
  pinMode(PIN_OUT, OUTPUT);
  pinMode(PIN_OUT_DLY, OUTPUT);

  digitalWrite(PIN_OVERFLOW, LOW);
  digitalWrite(PIN_OUT, HIGH);
  digitalWrite(PIN_OUT_DLY, HIGH);

}


//Function utilities
//
//
//

//Transmits a half-bit value
int transmit(boolean value, unsigned long lastCycles)
{
  //Serial.println(value, DEC);
  //We have to put the signal in the pin PIN_OUT, activate transmission PIN_TX_ACT and put with a 250ns delay transmitted bit in PIN_OUT_DLY
  //Remember that this is the NON-INVERTED signal so the values are the opposite as those from reception branch
  unsigned long  cyclesCurrent = ARM_DWT_CYCCNT;

  while (cyclesCurrent - lastCycles < WAIT_CYCLES_TX)
  {
    cyclesCurrent = ARM_DWT_CYCCNT;
  }

  unsigned long  cyclesTx = ARM_DWT_CYCCNT;
  //Direct signal
  digitalWriteFast(PIN_OUT, !value);
  //Activate transmission
  digitalWriteFast(PIN_TX_ACT, HIGH);
  cyclesCurrent = cyclesTx;
  while (cyclesCurrent - cyclesTx < WAIT_CYCLES_TX_DLY)
  {
    cyclesCurrent = ARM_DWT_CYCCNT;
  }
  //Delayed signal
  digitalWriteFast(PIN_OUT_DLY, !value);

  return cyclesTx;
}



//Delays processing for the specified number of clock cycles
void delayCycles(unsigned long cycles)
{
  unsigned long  cyclesInicio = ARM_DWT_CYCCNT;
  unsigned long  cyclesCurrent = cyclesInicio;
  while (cyclesCurrent - cyclesInicio < cycles)
  {
    cyclesCurrent = ARM_DWT_CYCCNT;
  }
}


//End a transmission and leave the bus in steady state
void endTx(unsigned long lastCycles)
{

  unsigned long  cyclesCurrent = ARM_DWT_CYCCNT;
  while (cyclesCurrent - lastCycles < WAIT_CYCLES_TX)
  {
    cyclesCurrent = ARM_DWT_CYCCNT;
  }
  unsigned long  cyclesTx = ARM_DWT_CYCCNT;
  cyclesCurrent = cyclesTx;
  //Direct signal
  digitalWriteFast(PIN_OUT, LOW);

  while (cyclesCurrent - cyclesTx < WAIT_CYCLES_TX_DLY)
  {
    cyclesCurrent = ARM_DWT_CYCCNT;
  }
  cyclesTx = ARM_DWT_CYCCNT;
  cyclesCurrent = ARM_DWT_CYCCNT;
  //Delayed signal
  digitalWriteFast(PIN_OUT_DLY, LOW);

  while (cyclesCurrent - cyclesTx < WAIT_CYCLES_TX * 25)
  {
    cyclesCurrent = ARM_DWT_CYCCNT;
  }
  //Disable transmission
  digitalWriteFast(PIN_TX_ACT, LOW);

}


//MAIN LOOP
void loop() // run over and over
{

  uint8_t sampleRead;
  int consecutiveSamples = 0;
  uint8_t sampleActive = HIGH;
  word sequenceStartReceived = 0;
  boolean receptionIsActive = false;
  unsigned int halfBitsData = 0;
  unsigned int halfBitsDataEven = 0;
  unsigned int halfBitsDataOdd = 0;
  unsigned int halfBitsDataTx[300];
  unsigned int halfBitsDataCheckTx[300];
  int halfBitsDataReceived = 0;

  unsigned long  cyclesPrevious;
  unsigned long  cyclesCurrent = ARM_DWT_CYCCNT;
  word bufferRX[300];
  int index = 0;
  int indexTx = 0;
  boolean waitForResponse = false;

  while (true)
  {
    //noInterrupts();
    //Check receive line

    //Enable interrupts for serial port
    interrupts();

    int length = 480;
    char buffer [480];
    char termChar = '\n';
    int numCharsRecv = 0;
    //boolean eotxPending = false;



    //Reception from serial port
    //
    //
    //
    if (Serial.available())
    {
      //noInterrupts();

      //eotxPending = true;
      int numCharsRecv = Serial.readBytesUntil(termChar, buffer, length);
      if (numCharsRecv)
      {
        buffer[numCharsRecv] = '\0';
        String mystring(buffer);

        if (ENABLEDEBUG) Serial.print("[DEBUG] RECEIVED : ");
        if (ENABLEDEBUG) Serial.print(numCharsRecv, DEC);
        if (ENABLEDEBUG) Serial.print(" CHARS ");

        //Serial.print(mystring);
        waitForResponse = true;

        //Process buffer to decode and split into frames
        int i = 0;
        index = 0;
        while (i < numCharsRecv)
        {
          bufferRX[index] = (buffer[i] & 0x3f) | ((buffer[i + 1] & 0x1F) << 6);
          if (ENABLEDEBUG) Serial.print(" DECODED : ");
          if (ENABLEDEBUG) Serial.print(bufferRX[index], BIN );

          i += 2;
          index++;
        }
        if (ENABLEDEBUG) Serial.println("");
        digitalWriteFast(PIN_OVERFLOW, LOW);
      }

      else
      {
        digitalWriteFast(PIN_OVERFLOW, HIGH);
      }

    }

    //bufferRX[0] = 0b00110000110;
    //bufferRX[1] =  0;


    //End serial reception

    //Start of timing-critical stuff, so we disable interruptions
    noInterrupts();

    //Variable to set if we need to tx [EOF] at the end of this processing cycle
    boolean signalEndTx = false;



    //Transmit data to the 5250 if pending data
    //
    //
    //
    if (index > 0)
    {
      //Transmitting start sequence
      //0b0101010101000111 in sequenceStart
      int lastClock = 0;

      for (int i = 0; i < 16; i++)
      {
        lastClock = transmit(bitRead(sequenceStart, 15 - i), lastClock);
      }


      //Data transmission
      for (int i = 0; i < index; i++)
      {
        //Conditioning buffer with sync, fill and parity
        //sync
        bufferRX[i] <<= 1;
        bitWrite(bufferRX[i], 0, 1);

        //fill
        bitWrite(bufferRX[i], 12, 0);
        bitWrite(bufferRX[i], 13, 0);
        bitWrite(bufferRX[i], 14, 0);
        bitWrite(bufferRX[i], 15, 0);

        //parity
        int parityBit = 0;
        //if ((bufferRX[i] & 1) == 0)
        if ((parity_even_bit(bufferRX[i]) && ! parity_even_bit(bufferRX[i] >> 8))  ||  (!parity_even_bit(bufferRX[i]) && parity_even_bit(bufferRX[i] >> 8)))
        {
          parityBit = 1;
        }
        bitWrite(bufferRX[i], 12, parityBit);

        //Transmission for each bit
        for (int j = 0; j < 16; j++)
        {
          //First half bit, reversed
          lastClock = transmit(!bitRead(bufferRX[i], j), lastClock);

          //Second half bit
          lastClock = transmit(bitRead(bufferRX[i], j), lastClock);
        }
      }

      index = 0;

      endTx(lastClock);

      //We have transmitted something, so we need to generate later [EOTX] over the serial port
      signalEndTx = true;

    }
    //End of transmission to 5250







    //reception from 5250
    //
    //
    //
    //
    halfBitsDataEven = 0;
    halfBitsDataOdd = 0;
    unsigned long   cyclesReception = ARM_DWT_CYCCNT;
    cyclesCurrent = ARM_DWT_CYCCNT;
    cyclesPrevious = cyclesCurrent;

    //We wait max WAIT_CYCLES_RX for a response, unless rx is already active
    while (receptionIsActive || (waitForResponse  && (cyclesCurrent -  cyclesReception < WAIT_CYCLES_RX)))
    {

      //End earlier if no response expected
      if (! receptionIsActive && Serial.available() && ((cyclesCurrent -  cyclesReception) >= WAIT_CYCLES_RX_PENDING_TX))
      {
        break;
      }


      cyclesCurrent = ARM_DWT_CYCCNT;

      if (cyclesCurrent - cyclesPrevious >= WAIT_CYCLES_RX_SAMPLE)
      {
        //Processing has been too slow, light LED and inform
        digitalWriteFast(PIN_OVERFLOW, HIGH);
        Serial.print("[DEBUG] ERROR, PROCESSING TOO SLOW ");
        Serial.println(cyclesCurrent - cyclesPrevious, DEC);
      }

      //Wait till it's time to get another sample from RX-DAT-INV
      while (cyclesCurrent - cyclesPrevious < WAIT_CYCLES_RX_SAMPLE)
      {
        cyclesCurrent = ARM_DWT_CYCCNT;
      }

      //Sample RX-DAT-INV
      sampleRead = digitalReadFast(PIN_IN);



      cyclesPrevious = cyclesCurrent;




      //Manage samples. If we get three or four consecutive samples at the same level we have a new half-bit
      //Otherwise we have a sync error
      switch (consecutiveSamples)
      {

        case 0:
          //New half-bit
          sampleActive = sampleRead;
          consecutiveSamples++;
          break;

        case 1:
          //second sample
          if (sampleActive != sampleRead)
          {
            //Out of sync!
            sampleActive = sampleRead;
            consecutiveSamples = 1;
          }
          else
          {
            consecutiveSamples++;
          }
          break;
        case 2:

          //third sample
          if (sampleActive != sampleRead)
          {
            //Out of sync!
            sampleActive = sampleRead;
            consecutiveSamples = 1;
          }
          else
          {

            consecutiveSamples++;
            //New half-bit!
            if (!receptionIsActive)
            {
              //Add half-bit to start sequence detection
              sequenceStartReceived <<= 1;
              sequenceStartReceived += sampleActive;

            }
            else
            {

              //Already got start sequence, add to received data, odd or even half bits
              halfBitsDataReceived++;
              halfBitsData <<= 1;
              halfBitsData += sampleActive;

              //If we are starting a frame wait till the first even half bit is 0
              if (halfBitsDataReceived == 2 && sampleActive == 0) {
                halfBitsDataReceived = 0;
                halfBitsDataEven = 0;
                halfBitsDataOdd = 0;
                halfBitsData = 0;
                break;
              }

              if ((halfBitsDataReceived % 2) == 0)
              {
                halfBitsDataEven <<= 1;
                halfBitsDataEven += sampleActive;
              }
              else
              {
                halfBitsDataOdd <<= 1;
                halfBitsDataOdd += sampleActive;
              }

              if (halfBitsDataReceived == 32)
              {
                //We have received a full frame
                halfBitsDataTx[indexTx] = halfBitsDataEven;
                halfBitsDataCheckTx[indexTx] = halfBitsDataOdd;
                indexTx++;
                halfBitsDataReceived = 0;
                halfBitsData = 0;
                halfBitsDataEven = 0;
                halfBitsDataOdd = 0;
              }
            }
          }
          break;

        case 3:
          //fourth and last value of half-bit
          if (sampleActive != sampleRead)
          {
            sampleActive = sampleRead;
            consecutiveSamples = 1;
          }
          else
          {
            consecutiveSamples = 1;
          }
          break;
      }



      //Check if we have received start sequence
      if (!receptionIsActive)
      {

        if ((sequenceStartReceived & 0xFFFF) == sequenceStart)
        {
          //Signal that we are now sampling the data frame
          receptionIsActive = true;
          //Reset holder
          sequenceStartReceived = 0;
        }
      }

      else
      {
        //Check if we have stop sequence (Address 7)
        if (indexTx > 0 && (halfBitsDataTx[indexTx - 1] & maskEnd) == sequenceEnd)
        {
          //No more reception
          receptionIsActive = false;
          waitForResponse = false;
        }


        //Now some error checking
        /*
          //Parity error detection, commented out as it is too slow to run without overclocking
          if (indexTx > 0)
          {
          unsigned int parityBit=0;
          word toCheck = halfBitsDataTx[indexTx-1] <<1 >>5;
            //if ((toCheck & 1) == 0)

            unsigned int check1 = parity_even_bit(toCheck);
            unsigned int check2 = parity_even_bit(toCheck >> 8);

            if ((check1 && ! check2)  ||  (!check1 && check2))
            {
             parityBit=1;//TBD
            }

            if (bitRead(halfBitsDataTx[indexTx-1], 3) != parityBit)
            {
              //Parity error, light LED
              Serial.println("[DEBUG] PARITY ERROR");
              digitalWriteFast(PIN_OVERFLOW, HIGH);
              receptionIsActive=false;
              waitForResponse=false;
            }
          }
        */

        //Detect too many frames (unlikely)
        if (indexTx > MAX_FRAMES_RX)
        {
          digitalWriteFast(PIN_OVERFLOW, HIGH);
          Serial.println("[DEBUG] MAX FRAMES ERROR");
          receptionIsActive = false;
          waitForResponse = false;
          indexTx = 0;
        }

        //Detection of incorrect frame alignment, light LED
        if (indexTx > 0 && (halfBitsDataTx[indexTx - 1] & maskFrame) != sequenceFrameOdd)
        {
          digitalWriteFast(PIN_OVERFLOW, HIGH);
          Serial.println("[DEBUG] SYNC ERROR ODD");
          receptionIsActive = false;
          waitForResponse = false;
          indexTx = 0;
        }

        if (indexTx > 0 && (halfBitsDataCheckTx[indexTx - 1] & maskFrame) != sequenceFrameEven)
        {
          digitalWriteFast(PIN_OVERFLOW, HIGH);
          Serial.println("[DEBUG] SYNC ERROR EVEN");
          receptionIsActive = false;
          waitForResponse = false;
          indexTx = 0;
        }

        /*Detect incorrect intrabit transitions, commented out as it is too slow to run without overclocking
          if (indexTx > 0 && (halfBitsDataTx[indexTx-1] ^ halfBitsDataCheckTx[indexTx-1]) != checkTransitions)
          {
          digitalWriteFast(PIN_OVERFLOW, HIGH);
          Serial.println("ERROR TRANSICIONES");
          Serial.println(indexTx,DEC);
          receptionIsActive=false;
          waitForResponse=false;
          }*/

      }

    }

    waitForResponse = false;
    //End reception from 5250






    //Transmission to serial
    //
    //
    //
    if (indexTx > 0)
    {
      interrupts();

      if (ENABLEDEBUG) Serial.print("[DEBUG] SENDING : ");
      if (ENABLEDEBUG) Serial.println(indexTx, DEC);

      for (int i = 0; i < indexTx; i++) {
        //halfBitsDataTx[i] = 0b1011100001111000;
        //0b1011100001111000

        byte firstByte = 0x40 | ((halfBitsDataTx[i] >> 9) & 0x3F ) ;
        byte secondByte = 0x40 | (( halfBitsDataTx[i] >> 4) & 0x1F ) ;

        if (ENABLEDEBUG) {
          Serial.print("[DEBUG] EVEN ");
          for (int j = 0; j < 16; j++)
          {
            if (halfBitsDataTx[i] < pow(2, j))
              Serial.print("0");
          }

          Serial.println(halfBitsDataTx[i], BIN);

          Serial.print("[DEBUG]  ODD ");

          for (int j = 0; j < 16; j++)
          {
            if (halfBitsDataCheckTx[i] < pow(2, j))
              Serial.print("0");
          }
          Serial.println(halfBitsDataCheckTx[i], BIN);
        }

        Serial.print((char)firstByte);
        Serial.print((char)secondByte);
        Serial.println("");

      }

      indexTx = 0;
    }

    if (signalEndTx)
    {
      //Signal end of trnsmission
      Serial.println("[EOTX]");
    }

    //End of transmission to Serial
    //And start of another processing cycle till the end of the universe

  }
}
