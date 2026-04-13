# shellcheck source=attributes.bash
. "$ETC_DIR/magic-cookie-dough/attributes.bash"


function error()
{
    echo "$(basename "${BASH_SOURCE[0]}"):" "$@"
}


# less version 590 for example doesn't handle UTF-8 characters in the
# prompt properly.  Only add them when this (relatively recent) fix is
# present:
#   v668  10/6/24   Fix UTF-8 chars in prompt.
if ! IFS=" " read -r -a version <<< "$(less --version 2>/dev/null)"; then
    error "less not found or returned an error"
    return
fi
if [[ ${version[0]} != less ]]; then
    error "unexpected 'less --version' output"
    return
fi
if [[ ${version[1]} -lt 668 ]]; then
    error "less is too old for UTF-8 prompts"
    return
fi

# If 'pager' is less (most likely via a symlink), make sure it's also
# of a suitable version, since it will use the same environment
# variable.
IFS=" " read -r -a version <<< "$(pager --version 2>/dev/null)"
if [[ $? -eq 0 && ${version[0]} == less && ${version[1]} -lt 668 ]]; then
    error "pager is less and is too old for UTF-8 prompts"
    return
fi

# Add reverse attributes to the default prompts.
#
# The default short prompt sometimes evaluates to a string of length
# zero, in which case less will fall back to prompting with a colon
# (without highlighting).  The magic cookies prevent that fallback
# from being triggered, but if the prompt consists only of the two
# cookies, it will be invisible.  As a workaround, append an
# unconditional, unhighlighted colon to the short prompt.
export LESS=" \
  --prompt=s${attr_reverse}?n?f%f .?m(%T %i of %m) ..?e(END) ?x- Next\: %x..%t${attr_normal}\:\$  \
  --prompt=m${attr_reverse}?n?f%f .?m(%T %i of %m) ..?e(END) ?x- Next\: %x.:?pB%pB\\%:byte %bB?s/%s...%t${attr_normal}\$  \
  --prompt=M${attr_reverse}?f%f .?n?m(%T %i of %m) ..?ltlines %lt-%lb?L/%L. :byte %bB?s/%s. .?e(END) ?x- Next\: %x.:?pB%pB\%..?c (column %c).%t${attr_normal}\$  \
  --prompt=h${attr_reverse}HELP -- ?eEND -- Press g to see it again:Press RETURN for more., or q when done${attr_normal}\$  \
  --prompt==${attr_reverse}?f%f .?m(%T %i of %m) .?ltlines %lt-%lb?L/%L. .byte %bB?s/%s. ?e(END) :?pB%pB\%..?c (column %c).%t${attr_normal}\$  \
  --prompt=w${attr_reverse}Waiting for data${attr_normal}\$"

# By default, less outputs the magic cookie dough characters as
# e.g. "<U+F5220>", presumably because it detects that they're
# "unsuitable for display (e.g., unassigned code points)" as per its
# man page.  This solution is from
# https://stackoverflow.com/questions/72541931, and causes such
# characters to be output normally anyway.
#
# If viewing files containing non-ASCII characters via
# 5250_terminal.py, it might in some cases be better to expand less's
# definition of "unsuitable for display" to include all characters not
# in the terminal's code page and display their code points, but this
# would probably be quite difficult to do accurately.
export LESSUTFBINFMT="*n%C"

# Add reverse attributes to the default 'man' prompt.
export MANLESS="${attr_reverse}Manual page \$MAN_PN ?ltline %lt?L/%L.:byte %bB?s/%s..?e (END):?pB %pB\%.. (press h for help or q to quit)${attr_normal}"

# man prepends its prompt (whether the default or the one set via
# $MANLESS) and other parameters for less to $LESS, which means the
# standard less prompts with magic cookie dough set above override
# man's prompt.  This wrapper script around less moves man's
# parameters to the end of $LESS.
export MANPAGER="\"$ETC_DIR/magic-cookie-dough/man_pager.py\""

# Git normally sets LESS=FRX, but won't do so if LESS is already set,
# so work around that.
export GIT_PAGER="less -FRX"
