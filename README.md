# `cross-sysroot` [![Build Status](https://travis-ci.org/labapart/cross_sysroot.svg?branch=master)](https://travis-ci.org/labapart/cross_sysroot)

`cross-sysroot` is a utility to generate `sysroot` for cross-compilation.

The tool expects the name of the targeted Linux distribution, its version, the targeted architecture and a file containing the list of the main required packages.  
The tool will solve package dependencies and extract them into a given `sysroot` path.

The generated `sysroot` can be used as an argument for the toolchain command line argument `--sysroot=`

* To install the utility: `pip3 install cross-sysroot`

* Command usage:

```
usage: cross-sysroot [-h] [--verbose] --distribution {debian,ubuntu}
                  --distribution-version DISTRIBUTION_VERSION
                  [--distribution-url DISTRIBUTION_URL] --architecture
                  {amd64,arm64,armhf,armel} --build-root BUILD_ROOT
                  package_list_file

Build package list for Linux Distribution.

positional arguments:
  package_list_file     File containing the list of packages (and their
                        versions)

optional arguments:
  -h, --help            show this help message and exit
  --verbose             Verbose mode
  --distribution {debian,ubuntu}
                        Linux distribution
  --distribution-version DISTRIBUTION_VERSION
                        Linux distribution
  --distribution-url DISTRIBUTION_URL
                        Linux distribution URL
  --architecture {amd64,arm64,armhf,armel}
                        CPU Architecture
  --build-root BUILD_ROOT
                        Location to store the Linux Distribution package.
```

* Example:

```
cross-sysroot --distribution debian --distribution-version stable --architecture arm64 --build-root /tmp/cross-sysroot tests/requirements-debian-jessie-arm64.txt
```

Notes about Development/CI
==========================

* Launch the python application from source tree: `PYTHONPATH=$PWD python3 -m cross_sysroot --help`

* Generate a new PIP package

* Run Python linter on the code:

    sudo apt-get install pylint3
    pylint3 cross_sysroot

* Run test in the source tree: `PYTHONPATH=$PWD pytest`

Development Information
=======================

Format of the Debian-based distribution repository
--------------------------------------------------

Location of `Packages.gz`:
- http://gb.archive.ubuntu.com/ubuntu/dists/trusty/main/binary-amd64/Packages.gz
- http://ftp.uk.debian.org/debian/dists/jessie/main/binary-amd64/Packages.gz

Content of `Packages.gz`:

```
(...)
Package: automake1.9
Priority: optional
Section: devel
Installed-Size: 1137
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Original-Maintainer: Eric Dorland <eric@debian.org>
Architecture: all
Version: 1.9.6+nogfdl-4ubuntu1
Provides: automaken
Depends: autoconf (>= 2.58), autotools-dev (>= 20020320.1)
Suggests: automake1.9-doc
Conflicts: automake (<< 1:1.4-p5-1), automake1.5 (<< 1.5-2), automake1.6 (<< 1.6.1-4)
Filename: pool/main/a/automake1.9/automake1.9_1.9.6+nogfdl-4ubuntu1_all.deb
Size: 338192
MD5sum: 5bc0b73852c50927a98ac4150cf2c585
SHA1: 8dbab4e448dd095f7ab9dc6defe308823cd1b16a
SHA256: 75358908ffe09e115d3971273c967306dd931b94edd846dbd6a762448e40cb56
Description: A tool for generating GNU Standards-compliant Makefiles
Description-md5: 16f7c6a70ae85327f4522569aa2e0cc9
Bugs: https://bugs.launchpad.net/ubuntu/+filebug
Origin: Ubuntu
Supported: 9m

Package: automoc
Priority: extra
Section: devel
Installed-Size: 122
Maintainer: Ubuntu Developers <ubuntu-devel-discuss@lists.ubuntu.com>
Original-Maintainer: Debian Qt/KDE Maintainers <debian-qt-kde@lists.debian.org>
Architecture: amd64
Version: 1.0~version-0.9.88-5build1
Depends: libc6 (>= 2.2.5), libgcc1 (>= 1:4.1.1), libqtcore4 (>= 4:4.8.0), libstdc++6 (>= 4.1.1), libqt4-dev
Filename: pool/main/a/automoc/automoc_1.0~version-0.9.88-5build1_amd64.deb
Size: 32888
(...)
```
