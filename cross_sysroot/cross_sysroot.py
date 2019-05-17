#!/usr/bin/env python3

import argparse
import logging
import os

from . import package_database


def parse_args(command_line=None):
    parser = argparse.ArgumentParser(prog="cross-sysroot",
                                     description='Build package list for Linux Distribution.')
    parser.add_argument('--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('--distribution', choices=['debian', 'ubuntu'], required=True,
                        help='Linux distribution')
    parser.add_argument('--distribution-version', type=str, required=True,
                        help='Linux distribution')
    parser.add_argument('--distribution-url', type=str, help='Linux distribution URL')
    parser.add_argument('--architecture', choices=['amd64', 'arm64', 'armhf', 'armel'],
                        required=True, help='CPU Architecture')
    parser.add_argument('--build-root', type=str, required=True,
                        help='Location to store the Linux Distribution package.')
    parser.add_argument('package_list_file', type=str,
                        help='File containing the list of packages (and their versions)')

    if command_line:
        return parser.parse_args(command_line)

    return parser.parse_args()


def main(args):
    if args.verbose:
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

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
