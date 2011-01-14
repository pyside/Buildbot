#!/usr/bin/python

# Copy this script to /usr/bin/git_clone

import sys
import time
import shutil
import os

callargs = sys.argv
callargs[0] = 'git'
module_dir = callargs[-1]

for i in range(10):
    retcode = os.system(' '.join(callargs))
    if retcode == 0:
        break
    shutil.rmtree(module_dir, True)
    time.sleep(1)

sys.exit(retcode)

