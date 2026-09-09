# This script fragment is used by twinax_bashrc_example, but may
# instead be sourced from your own ~/.bashrc.

# These may be defined with unwanted --color=auto options:
for alias in egrep fgrep grep ls; do
    if [[ -v BASH_ALIASES[$alias] ]]; then
	unalias $alias
    fi
done
