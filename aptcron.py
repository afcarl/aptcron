#!/usr/bin/env python

import apt

cache=apt.Cache()
#cache.update()
cache.open(None)
cache.upgrade()
for pkg in cache.get_changes():
    print('* %s: %s -> %s' % (pkg.name, pkg.versions[1].version, pkg.versions[0].version))
