#!/usr/bin/env python3

"""Entrypoint file for 'cross_sysroot' module."""

import argparse
import logging
import os
import sys

import pkg_resources

from . import package_database, fixup_sysroot, cross_gcc

try:
    PKG_VERSION = pkg_resources.require("biosency-final-test")[0].version
except pkg_resources.ResolutionError:
    PKG_VERSION = "Unknown Version"


def parse_args(command_line=None):
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(prog="cross-sysroot",
                                     description='Build package list for Linux Distribution.')
    parser.add_argument('--version', action='version', version=PKG_VERSION)
    parser.add_argument('--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('--distribution', choices=['debian', 'ubuntu', 'raspbian'],
                        help='Linux distribution')
    parser.add_argument('--distribution-version', type=str, required='--distribution' in sys.argv,
                        help='Linux distribution')
    parser.add_argument('--distribution-url', type=str, help='Linux distribution URL')
    parser.add_argument('--architecture', choices=['amd64', 'arm64', 'armhf', 'armel'],
                        required='--distribution' in sys.argv, help='CPU Architecture')
    parser.add_argument('--build-root', type=str, required='--distribution' in sys.argv,
                        help='Location to store the Linux Distribution package.')
    parser.add_argument('--cross-gcc', type=str, default=None,
                        help='GCC Path used to build the cross application. \
                            When set, all GCC sysroot files are copied into the sysroot.')
    parser.add_argument('package_list_file', type=str,
                        help='File containing the list of packages (and their versions)')

    if command_line:
        return parser.parse_args(command_line)

    return parser.parse_args()


def main(args):
    """Main function for cross-sysroot python module."""
    logger = logging.getLogger()
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(formatter)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)

    # Use default distribution URL if not specified
    if args.distribution_url is None:
        if args.distribution == "debian":
            args.distribution_url = "http://ftp.uk.debian.org/debian/"
        elif args.distribution == "ubuntu":
            args.distribution_url = "http://gb.archive.ubuntu.com/ubuntu/"
        elif args.distribution == "raspbian":
            args.distribution_url = "http://archive.raspbian.org/raspbian/"

    if not os.path.isdir(args.build_root):
        os.makedirs(args.build_root)

    if args.cross_gcc:
        cross_gcc.copy_sysroot(args)

    # Load distribution database
    sql_conn = package_database.load_distribution_database(args)

    with open(args.package_list_file) as fin:
        for line in fin:
            package_name = line.strip()

            if package_name.startswith('#'):
                continue

            package_database.add_package(args, sql_conn, package_name)

    # resolve package dependencies
    package_database.resolve_dependencies(args, sql_conn)

    # Install all packages
    package_database.download_packages(args)

    # Fix symbolic link
    fixup_sysroot.fixup_sysroot(args.build_root)


def command_line_entrypoint():
    """Command line entrypoint."""
    command_line_args = parse_args()
    try:
        main(command_line_args)
    except package_database.PackageNotFound as exception:
        logging.error("Package not found: %s", exception.package_name)


if __name__ == '__main__':
    command_line_entrypoint()
