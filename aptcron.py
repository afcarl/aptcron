#!/usr/bin/env python

from __future__ import print_function

import argparse
import glob
import os
import pickle
import sys

import apt

# constants:
CACHE_DIR = '/var/cache/aptcron'
SEEN_CACHE = '%s/seen' % CACHE_DIR
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

# python version dependent imports:
if PY3:
    import configparser
else:
    import ConfigParser as configparser

config = configparser.ConfigParser({
    'update': 'yes',
    'only-new': 'no',
})

# add global config files
configfiles = ['/etc/aptcron.conf', ] + sorted(glob.glob('/etc/aptcron.d/*.conf'))
configfiles += ['aptcron.conf', ] + sorted(glob.glob('aptcron.d/*.conf'))
print(configfiles)
config.read(configfiles)

# cli parser:
parser = argparse.ArgumentParser(
    description="List APT updates via cron, optionally installing them.")
parser.add_argument('--no-update', action='store_true',
                    help="Do not update package index before listing updates.")
parser.add_argument('--only-new', action='store_true',
                    help="Only list new package updates.")
args = parser.parse_args()

if args.no_update:
    config.set('DEFAULT', 'update', 'no')
if args.only_new:
    config.set('DEFAULT', 'only-new', 'yes')

if os.getuid() != 0:
    print("aptcron requires root-privileges to run.", file=sys.stderr)
    sys.exit(1)

# initialize cache:
cache=apt.Cache()

# update the APT cache:
if config.getboolean('DEFAULT', 'update'):
    cache.update()

# list upgradeable packages
cache.open(None)
cache.upgrade()

packages = [(p.name, p.versions[1].version, p.versions[0].version) for p in cache.get_changes()]

seen = []
if config.getboolean('DEFAULT', 'only-new') and os.path.exists(SEEN_CACHE):
    seen = pickle.load(open(SEEN_CACHE))
    packages = [p for p in packages if p not in seen]

if packages:
    print("Available updates:")

for name, new, old in packages:
    print('* %s: %s -> %s' % (name, new, old))

if config.getboolean('DEFAULT', 'only-new'):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    pickle.dump(seen + packages, open(SEEN_CACHE, 'w'))
