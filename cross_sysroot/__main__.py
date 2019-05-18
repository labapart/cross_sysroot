import logging

from . import cross_sysroot, package_database

logger = logging.getLogger()


def main():
    command_line_args = cross_sysroot.parse_args()
    try:
        cross_sysroot.main(command_line_args)
    except package_database.PackageNotFound as e:
        logger.error("Package not found: %s", e.package_name)


main()
