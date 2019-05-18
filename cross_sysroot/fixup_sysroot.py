import logging
import os
import re

pkconfig_line_is_prefix = re.compile(r"^prefix=(.*)\n$")

logger = logging.getLogger(__name__)


def fix_symbolic_link(root, path, file_path):
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


def fixup_sysroot(root):
    # r=root, d=directories, f = files
    for r, d, f in os.walk(root):
        # Remove unused argument
        del d

        for file in f:
            file_path = os.path.join(r, file)

            fix_symbolic_link(root, r, file_path)
            # patch_pkg_config(root, r, file_path)
