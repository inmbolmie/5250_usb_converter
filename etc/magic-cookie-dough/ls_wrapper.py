#!/usr/bin/env python3

"""Wrap 'ls' as a workaround for it outputting an extra "ENDCODE" (as
per man dir_colors(5)) at the start of the first line of its output
that contains a filename.  Other than discarding that one character,
this should behave identically to 'ls'.

"""

import codecs
import errno
import os
import pty
import signal
import subprocess
import sys

LS_COMMAND = "ls"


class Pty:
    def __init__(self, args):
        pid, master_fd = pty.fork()
        if pid == pty.CHILD:
            os.execvp(args[0], args)
        self.pid = pid
        self.master_fd = master_fd

    def read(self):
        return os.read(self.master_fd, 1024)

    def wait(self):
        os.close(self.master_fd)
        pid, status = os.waitpid(self.pid, 0)
        assert pid == self.pid
        return os.waitstatus_to_exitcode(status)


class Pipe:
    def __init__(self, args):
        self.proc = subprocess.Popen(
            args, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE
        )

    def read(self):
        return self.proc.stdout.read(1024)

    def wait(self):
        self.proc.stdout.close()
        return self.proc.wait()


def main():
    # Don't want KeyboardInterrupt, just want SIGINT to kill the process.
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    args = [LS_COMMAND] + sys.argv[1:]

    # Create a PTY to attach ls to if and only if our own stdout is a
    # TTY.  This way, when ls checks if its own stdout is a TTY, it
    # will see what we do.  Given this, for example '$ls' will output
    # in columns, and '$ls | cat' won't, regardless of whether '$ls'
    # is '/bin/ls' or this wrapper script.
    if os.isatty(sys.stdout.fileno()):
        child = Pty(args)
    else:
        child = Pipe(args)

    decoder = codecs.getincrementaldecoder("utf-8")("ignore")
    input_buffer = ""
    seen_first_file_line = False
    terminate = False
    while not terminate:
        try:
            binary = child.read()
        except OSError as e:
            if e.errno == errno.EIO:
                # This seems to be what happens when there's no more
                # output available from the PTY.
                break
        if len(binary) == 0:
            break

        input_buffer += decoder.decode(binary)
        while "\n" in input_buffer:
            line, input_buffer = input_buffer.split("\n", maxsplit=1)
            if not seen_first_file_line:
                if not line.startswith("total "):
                    seen_first_file_line = True
                    if line[0] == "\U000f5220":
                        # Drop extra normal attribute from start of first
                        # file line
                        line = line[1:]
            try:
                print(line)
            except BrokenPipeError:
                # Expected if there's a lot of output and it was piped
                # into e.g. 'head'.
                terminate = True
                break

    # Make our own exitcode the same as ls's
    exitcode = child.wait()
    if exitcode >= 0:
        sys.exit(exitcode)
    else:
        os.kill(os.getpid(), -exitcode)


main()
