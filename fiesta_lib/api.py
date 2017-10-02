# -*- coding: utf-8 -*-

"""
This file contains API calls and Data
"""

import six

from sys import version_info
from termcolor import colored

from .data import *

__version__ = "1.0.0"
__all__ = ["run_console", "run", "GlobalParameters"]


# --------------------------------------------------------------------------
#
# Command line options
#
# --------------------------------------------------------------------------
def run_console(config):
    """
    :param config: GlobalParameters option instance
    :type config: `GlobalParameters`

    :raises: TypeError
    """
    if not isinstance(config, GlobalParameters):
        raise TypeError("Expected GlobalParameters, got '%s' instead" % type(config))

    #six.print_(colored("[*]", "blue"), "Starting fiesta execution")
    run(config)
    #six.print_(colored("[*]", "blue"), "Done!")

# ----------------------------------------------------------------------
#
# API call
#
# ----------------------------------------------------------------------
def run(config):
    """
    :param config: GlobalParameters option instance
    :type config: `GlobalParameters`

    :raises: TypeError
    """
    if not isinstance(config, GlobalParameters):
        raise TypeError("Expected GlobalParameters, got '%s' instead" % type(config))
    # --------------------------------------------------------------------------
    # Checks Python version
    # --------------------------------------------------------------------------
    if version_info.major < 3:
        raise RuntimeError("You need Python 3.x or higher to run fiesta")

    # --------------------------------------------------------------------------
    # Main Fiesta Code
    # --------------------------------------------------------------------------
    from fiesta_lib.libs.fiesta import Fiesta
    f = Fiesta()
    if not f.configure( config.config ):
        return False
    if config.curses:
        f.set_curses()
    f.set_verbose( config.verbose )
    f.search( config.search )
    return True
