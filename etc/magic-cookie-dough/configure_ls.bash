eval "$(dircolors "$ETC_DIR/magic-cookie-dough/dircolors")"

# When --color is in effect and file names are output in columns
# (e.g. with plain 'ls' as opposed to 'ls -l'), 'ls' isn't aware that
# the magic cookies in the dircolors file take up horizontal space, so
# it may output more than 80 characters on a line, especially when all
# the file names are short, e.g. in the root directory.  Tell 'ls'
# that the screen is narrower than it really is to account for the
# extra 2 characters per column.
# shellcheck disable=SC2139
alias ls="\"$ETC_DIR/magic-cookie-dough/ls_wrapper.py\" --color --width=66"
