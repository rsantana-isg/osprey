import os
import shutil
import subprocess
import tempfile
from distutils.spawn import find_executable
from numpy.testing.decorators import skipif

try:
    import mixtape
    HAVE_MIXTAPE = True
except:
    HAVE_MIXTAPE = False

OSPREY_BIN = find_executable('osprey')


@skipif(not HAVE_MIXTAPE, 'this test requires mixtape')
def test_1():
    cwd = os.path.abspath(os.curdir)
    dirname = tempfile.mkdtemp()

    try:
        os.chdir(dirname)
        subprocess.check_call([OSPREY_BIN, 'skeleton', '-t', 'mixtape',
                              '-f', 'config.yaml'])
        subprocess.check_call([OSPREY_BIN, 'worker', 'config.yaml', '-n', '1'])
        assert os.path.exists('osprey-trials.db')

    finally:
        os.chdir(cwd)
        shutil.rmtree(dirname)