aptcron
=======

**aptcron** is a simple script that (optionally) updates your APT index
("apt-get update") and prints all new packages to stdout. It is designed to be
run by cron, which should take care of sending out emails to the root-user.

The script, cron-jobs and any configuration can be deployed with APT itself,
making it suitable for larger automatic deployments.

Requirements
------------

**aptcron** is written in Python and runs with Python2.7+, including
Python3.2+. The only library required is python-apt, which you can install with
`apt get install python-apt` (or python3-apt).

The script relies on cron sending out emails with the output of cronjobs, so
your server needs to be configured for that.

Installation
------------

APT-repositories for the package will be available very soon.

If you want to upload a Debian package to your own custom APT repository, this
repository is ready to be built with `git-buildpackage`. 

Configuration
-------------

This scripts behaviour can be configured either via the command-line (which
always takes precedence) or via configuration files, it will parse, in order:
`/etc/aptcron.conf`, `/etc/aptcron.d/*.conf`, `./aptcron.conf` and
`./aptcron.d/*.conf`. Files in `*.d` directories are parsed in alphabetic order.

For now this script has only two configuration directives, here is an example
configuration file:

    [DEFAULT]
    # If set to 'no', aptcron won't update the index before listing packages:
    update: yes
    
    # If set to 'yes', aptcron only lists updates it hasn't seen previously
    only-new: no

By default the the `DEFAULT` section is used, but you can use a different
section by specifying the `--section` commandline parameter. Note that in this
case, any settings from the `DEFAULT` section still take precedence over the
programs defaults.

If you are not happy with the list of config files, specify a single config
file to be used instead with the `--config` parameter.

Cron configuration
------------------

**aptcron** is designed to be run by cron. The `debian/` directory includes the
cron.d-files installed by the `aptcron-*-time` packages.
