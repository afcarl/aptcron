#!/usr/bin/env python

from __future__ import print_function

import os
import sys

import apt

if os.getuid() != 0:
    print("aptcron requires root-privileges to run.", file=sys.stderr)
    sys.exit(1)

# initialize cache:
cache=apt.Cache()
cache.update()

# list upgradeable packages
cache.open(None)
cache.upgrade()
for pkg in cache.get_changes():
    print('* %s: %s -> %s' % (pkg.name, pkg.versions[1].version, pkg.versions[0].version))
