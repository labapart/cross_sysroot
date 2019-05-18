#!/usr/bin/env python3

import argparse
import logging
import os
import sys

import pkg_resources

from . import package_database

try:
    pkg_version = pkg_resources.require("biosency-final-test")[0].version
except pkg_resources.ResolutionError:
    pkg_version = "Unknown Version"


def parse_args(command_line=None):
    parser = argparse.ArgumentParser(prog="cross-sysroot",
                                     description='Build package list for Linux Distribution.')
    parser.add_argument('--version', action='version', version=pkg_version)
    parser.add_argument('--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('--distribution', choices=['debian', 'ubuntu'],
                        help='Linux distribution')
    parser.add_argument('--distribution-version', type=str, required='--distribution' in sys.argv,
                        help='Linux distribution')
    parser.add_argument('--distribution-url', type=str, help='Linux distribution URL')
    parser.add_argument('--architecture', choices=['amd64', 'arm64', 'armhf', 'armel'],
                        required='--distribution' in sys.argv, help='CPU Architecture')
    parser.add_argument('--build-root', type=str, required='--distribution' in sys.argv,
                        help='Location to store the Linux Distribution package.')
    parser.add_argument('package_list_file', type=str,
                        help='File containing the list of packages (and their versions)')

    if command_line:
        return parser.parse_args(command_line)

    return parser.parse_args()


def main(args):
    logger = logging.getLogger()
    ch = logging.StreamHandler()
    logger.addHandler(ch)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(levelname)s: %(message)s')
    ch.setFormatter(formatter)

    if args.verbose:
        logger.setLevel(logging.DEBUG)
        ch.setLevel(logging.DEBUG)

    # Use default distribution URL if not specified
    if args.distribution_url is None:
        if args.distribution == "debian":
            args.distribution_url = "http://ftp.uk.debian.org/debian/"
        elif args.distribution == "ubuntu":
            args.distribution_url = "http://gb.archive.ubuntu.com/ubuntu/"

    if not os.path.isdir(args.build_root):
        os.makedirs(args.build_root)

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


def command_line_entrypoint():
    command_line_args = parse_args()
    try:
        main(command_line_args)
    except package_database.PackageNotFound as e:
        logging.error("Package not found: %s", e.package_name)


if __name__ == '__main__':
    command_line_entrypoint()
