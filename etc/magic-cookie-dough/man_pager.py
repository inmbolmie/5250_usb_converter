#!/usr/bin/env python3

"""Use this script as the pager for 'man' so that man's prompt takes
effect.  See configure_less.bash for details.

"""

import codecs
import errno
import os
import pty
import signal
import subprocess
import sys

LESS_COMMAND = "less"


def main():
    env = os.environ
    less = env.get("LESS")
    orig = env.get("MAN_ORIG_LESS")
    if less is not None and orig is not None and less.endswith(orig):
        env["LESS"] = orig + " " + less[: -len(orig)]
    else:
        print("Environment variables not set as expected")
        # Continue rather than aborting as the behavior without the
        # workaround is okay.  This probably means the above message
        # will disappear too quickly though.

    os.execvpe(
        LESS_COMMAND,
        # man seems to pass no command-line parameters, but forward
        # them anyway.
        [LESS_COMMAND] + sys.argv[1:],
        env,
    )


main()
