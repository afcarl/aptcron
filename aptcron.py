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

# Parse command line arguments:
parser = argparse.ArgumentParser(
    description="List APT updates via cron, optionally installing them.")
parser.add_argument('--no-update', action='store_true',
                    help="Do not update package index before listing updates.")
parser.add_argument('--only-new', action='store_true',
                    help="Only list new package updates.")
parser.add_argument(
    '--section', default='DEFAULT',
    help="Read section SECTION from the config files (default: %(default)s).")
parser.add_argument(
    '--force', action='store_true',
    help="Print something even if no packages are found so an email is always sent.")
parser.add_argument('--config', help="Use an alternative config-file.")
args = parser.parse_args()

# Read configuration files:
config = configparser.ConfigParser({
    'update': 'yes',
    'only-new': 'no',
    'force': 'no',
})
if args.config:
    configfiles = [args.config]
else:
    configfiles = ['/etc/aptcron.conf', ] + sorted(glob.glob('/etc/aptcron.d/*.conf'))
    configfiles += ['aptcron.conf', ] + sorted(glob.glob('aptcron.d/*.conf'))
config.read(configfiles)

# Overrides anything settings given at the command line:
if args.no_update:
    config.set(args.section, 'update', 'no')
if args.only_new:
    config.set(args.section, 'only-new', 'yes')
if args.force:
    config.set(args.section, 'force', 'yes')

if os.getuid() != 0:
    print("aptcron requires root-privileges to run.", file=sys.stderr)
    sys.exit(1)

# initialize cache:
cache=apt.Cache()

# update the APT cache:
if config.getboolean(args.section, 'update'):
    cache.update()

# list upgradeable packages
cache.open(None)
cache.upgrade()

packages = [(p.name, p.versions[1].version, p.versions[0].version) for p in cache.get_changes()]

seen = []
if config.getboolean(args.section, 'only-new') and os.path.exists(SEEN_CACHE):
    seen = pickle.load(open(SEEN_CACHE))
    packages = [p for p in packages if p not in seen]

if packages:
    print("Available updates:")
elif config.getboolean(args.section, 'force'):
    print("No packages found.")

for name, new, old in packages:
    print('* %s: %s -> %s' % (name, new, old))

if config.getboolean(args.section, 'only-new'):
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    pickle.dump(seen + packages, open(SEEN_CACHE, 'w'))
