aptcron
=======

**aptcron** is a simple script that sends out E-Mails of available updates in
your APT index. It is designed to be fully configurable via files in the
`/etc/aptcron.d/` directory, so you can easily deploy configuration via your own
Debian packages.

Configuration options include:

* Update your APT index before creating the list of updates.
* Only list updates it hasn't already seen in the previous run.
* Delay execution to a random time within a configurable timeframe.
* Configure E-Mail Subject/From/To including runtime variables.
* Use an external SMTP mail server (including authentication and STARTTLS).

Mails are sent to root on localhost by default. They include an `X-AptCron: Yes`
and an `X-AptCron-Host: $hostname` header for easy filtering.

Requirements
------------

**aptcron** is written in Python and runs with Python2.7+, including
Python3.2+. The only library required is python-apt, which you can install with
`apt get install python-apt` (or python3-apt). If you want to use the
`--random-time` parameter (see below), you need a running `at` daemon.

The script sends out E-Mails with available updates (this is its primary
purpose, after all), so you need an SMTP-server available.

Installation
------------

APT-repositories for the package will be available very soon.

If you want to upload a Debian package to your own custom APT repository, this
repository is ready to be built with `git-buildpackage`. 

Configuration
-------------

The script can run fine without any configuration parameter. 

The behaviour can be configured either via the command-line (which always takes
precedence) or via configuration files, it will parse, in order:
`/etc/aptcron.conf`, `/etc/aptcron.d/*.conf`, `./aptcron.conf` and
`./aptcron.d/*.conf`. Files in `*.d` directories are parsed in alphabetic order.
**aptcron** will merge all configuration files together, so you can split your
configuration into as many files as you like.

Almost all configuration can be given in the config files or via the
command-line, where they have to be prefixed with `--`. The script runs fine
without any configuration directive at all, if you are happy with the defaults.
The syntax and defaults can be seen in this example:

    [DEFAULT]
    # If set to 'yes', aptcron won't update the index:
    no-update: no
    # If set to 'yes', aptcron only lists updates it hasn't seen previously:
    only-new: no
    # Do not send mail, just print to stdout:
    no-mail: yes
    # Set to "yes" to send an E-Mail even if no packages are found:
    force: no
    # Random delay: If you give a timerange (e.g. '2:00-8:00' or '-8:00',
    # execute aptcron at a random time within the given time.
    random-time: no

    # E-Mail: Configure how the E-Mail you will receive looks like.
    #         You can customize values using python formatting, available keys
    #         are: {host}, {shorthost} (leftmost part of the host) and {num}
    #         (number of packages).
    # The From: header used (default: root@{host}).
    mail-from: root@{host}
    # The To: header used (default: root@{host}).
    mail-to: root@{host}
    # The subject used.
    mail-subject: [aptcron] {shorthost}: {num} APT updates

    # SMTP: SMTP-related options.
    # The SMTP server/port:
    smtp-host: localhost
    smtp-port: 25
    # SMTP user/password (default: no authentication):
    smtp-user: 
    smtp-password:
    # Wether to use STARTTLS. Set to "yes" to use it if available, "force" will fail
    # if STARTTLS is not available, "no" will not use STARTTLS at all:
    smtp-starttls: force

A few parameters that can only be given via the command-line (for obvious
reasons):

    --config CONFIG       Use an alternative config-file.
    --section SECTION     Read section SECTION from the config files (default:
                          DEFAULT)
    --random-time [RANGE] Launch aptcron.py sometime in the given RANGE, e.g.
                          '2:00-8:00'. If no RANGE is given, execute sometime
                          between now and midnight.

The `--random-time` argument will cause **aptcron** to queue itself using the
`at` daemon. You can view execution time using the `atq` command.

Cron configuration
------------------

**aptcron** is designed to be run by cron. The `debian/` directory includes the
cron.d-files installed by the `aptcron-*-time` packages.
