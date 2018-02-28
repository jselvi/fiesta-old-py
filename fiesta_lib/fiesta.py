# -*- coding: utf-8 -*-

import argparse
import logging

logging.basicConfig(format="[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


# ----------------------------------------------------------------------
def main():

    from .api import run_console, GlobalParameters
    import yaml

    examples = '''
Examples:

    * Attack the web application defined in CONFIG using a SEARCH (or not):
        %(tool_name)s google.yaml mysearchterm
    '''  % dict(tool_name="fiesta")

    parser = argparse.ArgumentParser(description='FIESTA (Form Information Exposed via Size Transmitted Attack)', epilog=examples, formatter_class=argparse.RawTextHelpFormatter)

    # Main options
    parser.add_argument("config", metavar="CONFIG")
    parser.add_argument("search", metavar="SEARCH", nargs="?")
    parser.add_argument("-v", "--verbosity", dest="verbose", action="count", help="verbosity level: -v, -vv, -vvv.", default=0)
    parser.add_argument("-c", "--curses", dest="curses", action="store_true", help="Curses output", default=False)
    parser.add_argument("--dev", dest="dev", action="store_true", help="Developer mode", default=False)

    parsed_args = parser.parse_args()

    # Configure global log
    log.setLevel(abs(5 - parsed_args.verbose) % 5)

    # Read from YAML
    try:
        stream = open(parsed_args.config, "r", encoding='utf-8')
        yconfig = yaml.load(stream)
    except Exception as e:
        log.critical("[!] Unhandled exception: %s" % str(e))
        return

    # Add "dev" parameter to config
    yconfig['config']['dev'] = parsed_args.dev

    # Set Global Config
    config = GlobalParameters(parsed_args)
    config.config = yconfig['config']

    try:
        run_console(config)
    except KeyboardInterrupt:
        log.warning("[*] CTRL+C caught. Exiting...")
    # DEBUG
    #except Exception as e:
    #    log.critical("[!] Unhandled exception: %s" % str(e))

if __name__ == "__main__" and __package__ is None:
    # --------------------------------------------------------------------------
    #
    # INTERNAL USE: DO NOT MODIFY THIS SECTION!!!!!
    #
    # --------------------------------------------------------------------------
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(1, parent_dir)
    import fiesta_lib
    __package__ = str("fiesta_lib")
    # Checks Python version
    if sys.version_info.major < 3:
        print("\n[!] You need a Python version greater than 3.x\n")
        exit(1)

    del sys, os

    main()
