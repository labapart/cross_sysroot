"""Fix sysroot that might have broken symbolic link/reference."""

import logging
import os
import re

pkconfig_line_is_prefix = re.compile(r"^prefix=(.*)\n$")

logger = logging.getLogger(__name__)


def fix_symbolic_link(root, path, file_path):
    """Fix symbol link file that does point to an absolute address not valid in the context of sysroot."""
    if os.path.islink(file_path):
        linkto = os.readlink(file_path)
        linkto_fullpath = os.path.join(path, linkto)
        if linkto.startswith("/"):
            new_source = os.path.join(root, linkto[1:])
            if os.path.isfile(new_source):
                logger.info("Fix link for %s (from %s)", new_source, file_path)
                os.remove(file_path)
                os.symlink(new_source, file_path)
            else:
                logger.error("\tBROKEN-1:%s", new_source)
        elif not os.path.isfile(linkto_fullpath):
            logger.error("\tBROKEN-2: %s", linkto_fullpath)


def patch_pkg_config(root, path, file_path):
    """Patch package configuration file '.pc' to use the correct path."""
    # Remove unused argument
    del path

    if not file_path.endswith('.pc'):
        return

    with open(file_path, "r+") as f:
        pkg_config_data = ""

        line = f.readline()
        while line:
            is_prefix = pkconfig_line_is_prefix.findall(line)
            if is_prefix:
                line = "prefix=%s%s\n" % (root, is_prefix[0])

            pkg_config_data += line
            line = f.readline()

        f.seek(0)
        f.write(pkg_config_data)
        f.truncate()


def fixup_sysroot(sysroot):
    """Fixup sysroot that might have broken symbolic link."""
    for root, directories, files in os.walk(sysroot):
        # Remove unused argument
        del directories

        for file in files:
            file_path = os.path.join(root, file)

            fix_symbolic_link(sysroot, root, file_path)
            # patch_pkg_config(sysroot, root, file_path)
