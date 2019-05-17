import logging

from cross_sysroot import cross_sysroot, package_database

command_line_args = cross_sysroot.parse_args()
try:
    cross_sysroot.main(command_line_args)
except package_database.PackageNotFound as e:
    logging.error("Package not found: %s", e.package_name)
