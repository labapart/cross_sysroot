from enum import Enum
import gzip
import logging
import os
import re
import sqlite3
import subprocess

try:
    from urllib.request import urlretrieve
except ImportError:
    from urllib import urlretrieve

logger = logging.getLogger(__name__)

# Contain list of package to download
m_packages_to_install = {}

# Dependencies to resolve
m_dependencies_to_resolve = []

package_version_regex = re.compile(r'(\S+) \((\S+) (\S+)\)')


class PackageVersion(Enum):
    NONE = 0
    EQUAL = 1
    LESS_THAN = 2
    LESS_THAN_AND_EQUAL = 3
    GREATER_THAN = 4
    GREATER_THAN_AND_EQUAL = 4


class PackageNotFound(Exception):

    def __init__(self, package_name):
        super(PackageNotFound, self).__init__(package_name)
        self.package_name = package_name


def load_distribution_database(args):
    # Re-initialize list of packages to install
    m_packages_to_install.clear()

    #
    # Create Database
    #
    sqlite_database_filepath = args.build_root + "/%s-%s-%s-Packages.db" % \
            (args.distribution, args.distribution_version, args.architecture)
    if os.path.isfile(sqlite_database_filepath):
        os.remove(sqlite_database_filepath)
    sql_conn = sqlite3.connect(sqlite_database_filepath)
    sql_cur = sql_conn.cursor()
    sql_cur.execute("CREATE TABLE Packages(ID integer primary key autoincrement, "
                    "Name, Version, Filename, Dependencies)")

    # Location of 'Packages.gz'
    distribution_packages_url = args.distribution_url + "dists/%s/main/binary-%s/Packages.gz" % \
            (args.distribution_version, args.architecture)
    logger.debug("distribution_packages_url:%s", distribution_packages_url)

    # Generate the file for the Linux Distribution Packages
    distribution_packages_local_file = args.build_root + "/%s-%s-%s-Packages.gz" % \
            (args.distribution, args.distribution_version, args.architecture)

    logger.info("Download file %s", distribution_packages_url)
    urlretrieve(distribution_packages_url, distribution_packages_local_file)
    logger.debug("Decompress file %s", distribution_packages_local_file)
    with gzip.open(distribution_packages_local_file, 'rb') as fp:
        line = fp.readline().strip().decode('utf8')
        while line:
            if line.startswith("Package:"):
                package_name = line[9:]
                line = fp.readline().strip().decode('utf8')

                package_dependency = None
                while line:
                    if line.startswith('Version:'):
                        package_version = line[9:]
                    elif line.startswith('Depends:'):
                        package_dependency = line[9:]
                    elif line.startswith('Filename:'):
                        package_filename = line[10:]
                    line = fp.readline().strip().decode('utf8')

                sql_cur.execute("INSERT INTO Packages "
                                "(Name, Version, Filename, Dependencies) VALUES (?,?,?,?)",
                                (package_name, package_version,
                                 package_filename, package_dependency))

                # End of file
                if line is None:
                    break

            line = fp.readline().strip().decode('utf8')

    sql_conn.commit()
    sql_cur.close()

    return sql_conn


def list_similar_package_name(sql_conn, package_name):
    sql_cur = sql_conn.cursor()

    logger.info("Look for similar package to '%s'", package_name)

    # Try to find closest package name
    sql_cur.execute("SELECT Name FROM Packages WHERE Name LIKE '%%%s%%'" % package_name)
    rows = sql_cur.fetchall()
    return rows


def add_package_dependencies(args, sql_conn, dependencies_str):
    logger.debug("Dependencies: %s", dependencies_str)

    dependencies = dependencies_str.split(',')

    for dependency in dependencies:
        logger.debug("\tCheck dependency: %s", dependency)
        # Check if the dependency contains '|', in this case we consider it as a
        # complex dependency that would solve later
        if '|' in dependency:
            m_dependencies_to_resolve.append(dependency)
        else:
            add_package_from_str(args, sql_conn, dependency)


def add_package_from_str(args, sql_conn, package_str):
    # Remove leading and trailing whitespace
    package_str = package_str.strip()

    # Check if depdency contains a version number
    result = package_version_regex.findall(package_str)

    if result:
        # In case there is a version
        package_name = result[0][0]
        version_type = result[0][1]
        version = result[0][2]
        add_package(args, sql_conn, package_name, version, version_type)
    else:
        # Case there is no version
        add_package(args, sql_conn, package_str)


def add_package(args, sql_conn, package_name, version=None, version_type=PackageVersion.NONE):
    # TODO: FixMe: For now we strip ':any' from the name
    package_name = package_name.replace(':any', '')

    # Check if the package is not already in the list
    if package_name in m_packages_to_install:
        return

    sql_cur = sql_conn.cursor()

    logger.debug("ADD(%s,%s,%s)", package_name, version, version_type)

    sql_cur.execute("SELECT Filename, Dependencies FROM Packages WHERE Name='%s'" % package_name)
    package_info = sql_cur.fetchone()

    if package_info:
        m_packages_to_install[package_name] = {"name": package_name, "filename": package_info[0]}

        if version:
            m_packages_to_install[package_name]['version'] = version
            m_packages_to_install[package_name]['version_type'] = version_type

        dependencies = package_info[1]
        if dependencies:
            add_package_dependencies(args, sql_conn, dependencies)
    else:
        similar_packages = list_similar_package_name(sql_conn, package_name)

        if similar_packages:
            raise RuntimeError("Cannot find '{0}' did you mean '{1}'".
                               format(package_name, similar_packages))
        else:
            raise PackageNotFound(package_name)


def resolve_dependencies(args, sql_conn):
    for dependency in m_dependencies_to_resolve:
        if '|' in dependency:
            unresolved_dependencies = dependency.split('|')
            logger.warning("Unresolved dependency '%s'. We choose '%s'",
                           dependency, unresolved_dependencies[0].strip())
            for unresolved_dependency in unresolved_dependencies:
                try:
                    add_package_from_str(args, sql_conn, unresolved_dependency)
                    return
                except PackageNotFound:
                    pass

            raise RuntimeError("Could not resolve dependency '{0}'".format(dependency))
        else:
            raise RuntimeError("Unsupported dependency '{0}'".format(dependency))


def download_package(args, local_packages_root, package):
    package_file = os.path.join(local_packages_root, package['name'] + '.deb')
    package_url = args.distribution_url + package['filename']
    logger.info("Download package %s", package_file)
    urlretrieve(package_url, package_file)
    subprocess.call(["dpkg", "-x", package_file, args.build_root])


def download_packages(args):
    local_packages_root = os.path.join(args.build_root, "packages")
    try:
        os.makedirs(local_packages_root)
    except OSError:  # In case the directory already exists
        pass

    for package in m_packages_to_install.values():
        download_package(args, local_packages_root, package)
