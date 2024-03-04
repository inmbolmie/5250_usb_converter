#!/bin/bash
TERMINFO=etc/terminfo
mkdir -p $TERMINFO && tic -o $TERMINFO 5250converter.terminfo
