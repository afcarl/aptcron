#!/usr/bin/env python

from __future__ import print_function

import argparse
import os
import sys

import apt

parser = argparse.ArgumentParser(
    description="List APT updates via cron, optionally installing them.")
parser.add_argument('--no-update', dest='update', default=True, action='store_false',
                    help="Do not update package index before listing updates.")
parser.add_argument('--install', default=False, action='store_true',
                    help="Install all upgrades as well.")
args = parser.parse_args()

if os.getuid() != 0:
    print("aptcron requires root-privileges to run.", file=sys.stderr)
    sys.exit(1)

# initialize cache:
cache=apt.Cache()

# update the APT cache.
if args.update:
    cache.update()

# list upgradeable packages
cache.open(None)
cache.upgrade()
for pkg in cache.get_changes():
    print('* %s: %s -> %s' % (pkg.name, pkg.versions[1].version, pkg.versions[0].version))
