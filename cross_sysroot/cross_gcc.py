"""Copy GCC cross-compiler sysroot into sysroot directory."""

import logging
import os
import shutil
import subprocess

logger = logging.getLogger(__name__)


def retrieve_gcc_sysroot(cross_gcc):
    """Retrieve sysroot used to build GCC."""
    p = subprocess.Popen([cross_gcc, '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _, err = p.communicate()

    for line in err.decode('utf-8').split('\n'):
        # Find the line that contains '--with-sysroot'
        if '--with-sysroot' in line:
            for expr in line.split(' '):
                if '--with-sysroot' in expr:
                    return expr.split('=')[1]

    raise RuntimeError("GCC does not have '--with-sysroot'")


# From: https://stackoverflow.com/a/12514470/6267288
def copytree(src, dst, symlinks=True, ignore=None):
    """Recursively copy directory/files."""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore, ignore_dangling_symlinks=True)
        else:
            shutil.copy2(s, d)


def copy_sysroot(args):
    """Copy cross-compiler GCC sysroot into the sysroot directory."""
    gcc_sysroot = retrieve_gcc_sysroot(args.cross_gcc)

    gcc_fullpath = shutil.which(args.cross_gcc)
    gcc_bin_path = os.path.dirname(gcc_fullpath)
    gcc_root_path = os.path.dirname(gcc_bin_path)

    gcc_sysroot_fullpath = os.path.join(gcc_root_path, gcc_sysroot[1:])

    logger.info("Copy GCC Sysroot from %s to %s", gcc_sysroot_fullpath, args.build_root)
    copytree(gcc_sysroot_fullpath, args.build_root)
