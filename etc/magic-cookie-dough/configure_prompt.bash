# shellcheck source=attributes.bash
. "$ETC_DIR/magic-cookie-dough/attributes.bash"

# In a default Debian 12 ~/.bashrc, the \$ isn't highlighted.  Avoid
# introducing a blank before it by extending the highlighting to
# include \$ and putting the blank attribute byte after the \$, where
# there is normally a space.
PS1=${attr_reverse_underline}'\W\$'${attr_normal}
