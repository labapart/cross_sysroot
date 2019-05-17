import os
import parser
import shutil
import sys
import tempfile

from cross_sysroot import cross_sysroot

current_path = os.path.dirname(__file__)


#
# Try to retrieve packages for Debian ARM64
#
def test_simple():
    # Create temporary directory
    temp_dir_path = tempfile.mkdtemp()

    args = cross_sysroot.parse_args([
        '--verbose',
        '--distribution', 'debian',
        '--distribution-version', 'stable',
        '--architecture', 'arm64',
        '--build-root', temp_dir_path,
        os.path.join(current_path, 'requirements-debian-jessie-arm64.txt')
        ])
    cross_sysroot.main(args)

    # Remove temporary directory
    shutil.rmtree(temp_dir_path)
