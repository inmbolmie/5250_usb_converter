# This script fragment is used by twinax_bashrc_example, but may
# instead be sourced from your own ~/.bashrc.

# If 5250_terminal.py is started under X, since $DISPLAY is still set,
# running "emacs" will by default start it in the X session where
# 5250_terminal.py is running rather than in the TTY.  This alias
# works around that.  Another option would be to unset $DISPLAY.
alias emacs="emacs -nw"
