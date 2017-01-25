#!/usr/bin/env python3
"""

glob.py
Moves photos and videos from scattered places into a single directory tree
organized by year and month like:

/2016/01 - Jan
/2016/02 - Feb

Syntax: glob [--skip-mismatched-dates] <source directory> <target directory>

Fixes conflicting file names
Can skip files where EXIF date time does not match file creation date time
TODO: Handle duplicates

"""
import argparse
from media import Target


class App:
    def __init__(self):
        pass

    def main(self):
        parser = argparse.ArgumentParser(
            description='Organize media files into a target directory tree.',
            epilog='Awesome?')
        parser.add_argument('source_dir', metavar='source_dir', type=str,
                            help='directory with media files')
        parser.add_argument('target_dir', metavar='target_dir', type=str,
                            help='directory to organize media files into')
        parser.add_argument('--run', action='store_true', required=False,
                            help='actually run and move or modify media files')
        parser.add_argument('--verbose', action='store_true', required=False,
                            help='generate lots of verbosity')
        # Note that the project may be passing command line args via the
        # project 
        args = parser.parse_args()

        target = Target(args.target_dir, args.run, args.verbose)
        target.move_files_to_new_places(args.source_dir)
        print("Done")


# ----------
app = App()
app.main()
# ----------
