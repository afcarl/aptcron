#!/usr/bin/env python

from __future__ import print_function

import argparse
import glob
import os
import pickle
import random
import socket
import smtplib
import sys
import StringIO

from datetime import datetime
from datetime import timedelta
from email.mime.text import MIMEText
from subprocess import PIPE
from subprocess import Popen

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

hostname = socket.getfqdn()

# Parse command line arguments:
parser = argparse.ArgumentParser(
    description="List APT updates via cron, optionally installing them.")
parser.add_argument('--no-update', action='store_true',
                    help='Do not update the package index.')
parser.add_argument('--no-dist-upgrade', action='store_true',
                    help="No apt-get dist-upgrade (don't list packages with new dependencies).")
parser.add_argument('--only-new', action='store_true',
                    help="Only list new package updates.")
parser.add_argument('--no-mail', action='store_true',
                    help="Do not send mail, just print to stdout/stderr.")
parser.add_argument(
    '--force', action='store_true',
    help="Print something even if no packages are found so an email is always sent.")
parser.add_argument(
    '--section', default='DEFAULT',
    help="Read section SECTION from the config files (default: %(default)s).")
parser.add_argument('--config', help="Use an alternative config-file.")
parser.add_argument(
    '--random-time', metavar='RANGE', nargs='?', const='0:00-23:59',
    help="Launch %(prog)s sometime in the given RANGE, e.g. '2:00-8:00'. If no RANGE is "
         "given, execute sometime between now and midnight.")

mail_parser = parser.add_argument_group(
    'E-Mail', 'Configure how the E-Mail you will receive looks like.')
mail_parser.add_argument('--mail-from', metavar='FROM',
                         help='The From: header used (default: root@%s).' % hostname)
mail_parser.add_argument('--mail-to', metavar='TO',
                         help='The To: header used (default: root@%s).' % hostname)
mail_parser.add_argument('--mail-subject', metavar='SUBJECT', help='The subject used.')

smtp_parser = parser.add_argument_group('SMTP', 'SMTP-related options.')
smtp_parser.add_argument('--smtp-host', metavar='HOST',
                         help='The SMTP server to use (default: localhost).')
smtp_parser.add_argument('--smtp-port', metavar='PORT', type=int,
                         help='The SMTP port to use (default: 25).')
smtp_parser.add_argument('--smtp-user', metavar='USER',
                         help='The SMTP user to use (default: no user).')
smtp_parser.add_argument('--smtp-password', metavar='PWD',
                         help='The SMTP password to use (default: no password).')
smtp_parser.add_argument(
    '--smtp-starttls', choices=['no', 'yes', 'force'],
    help='Wether to use STARTTLS. "yes" will use it if available, "force" will fail if STARTTLS '
         'is not available (default: force).')
args = parser.parse_args()

# context for string formatting:
context = {
    'num': 'unknown',
    'host': hostname,
    'shorthost': hostname.split('.')[0],
}

# Read configuration files:
config = configparser.ConfigParser({
    'no-update': 'no',
    'no-dist-upgrade': 'no',
    'only-new': 'no',
    'force': 'no',
    'no-mail': 'no',

    'mail-from': 'root@%s' % hostname,
    'mail-to': 'root@%s' % hostname,
    'mail-subject': '[aptcron] {shorthost}: {num} APT updates',

    'smtp-host': 'localhost',
    'smtp-port': '25',
    'smtp-user': '',
    'smtp-password': '',
    'smtp-starttls': 'force',
})
if args.config:
    configfiles = [args.config]
else:
    configfiles = ['/etc/aptcron.conf', ] + sorted(glob.glob('/etc/aptcron.d/*.conf'))
    configfiles += ['aptcron.conf', ] + sorted(glob.glob('aptcron.d/*.conf'))
config.read(configfiles)

# Overrides anything settings given at the command line
cli_only_args = {'section', 'config', 'random_time'}
cli_args = {k: v for k, v in vars(args).items() if k not in cli_only_args and v}
for key, value in cli_args.items():
    if value is True:
        config.set(args.section, key.replace('_', '-'), 'yes')
    else:
        config.set(args.section, key.replace('_', '-'), value)


def timerange(start, end):
    stamp = start
    while stamp <= end:
        yield stamp
        stamp = stamp + timedelta(minutes=1)


def send_mail(config, args, stdout, stderr, context, code=0):
    # Actually send mail
    if config.getboolean(args.section, no_mail):
        print(sys.stdout.getvalue().strip(), file=stdout)
    else:
        try:
            body = sys.stdout.getvalue().strip()
            if not body:
                return

            msg = MIMEText(body)
            if code == 0:
                msg['Subject'] = config.get(args.section, 'mail-subject').format(**context)
            else:
                subj = '[aptcron] {shorthost}: Error while checking for updates'.format(**context)
                msg['Subject'] = subj
            msg['From'] = config.get(args.section, 'mail-from').format(**context)
            msg['To'] = config.get(args.section, 'mail-to').format(**context)
            msg['X-AptCron'] = 'yes'
            msg['X-AptCron-Host'] = context['host']

            s = smtplib.SMTP(config.get(args.section, 'smtp-host'),
                             config.getint(args.section, 'smtp-port'))

            starttls = config.get(args.section, 'smtp-starttls')
            if starttls in ('yes', 'force', ):
                try:
                    s.starttls()
                except smtplib.SMTPException:
                    if starttls == 'force':
                        raise RuntimeError("STARTTLS forced but not supported by SMTP-server.")

            user = config.get(args.section, 'smtp-user')
            password = config.get(args.section, 'smtp-password')
            if user and password:
                s.login(user, password)

            s.sendmail(msg['From'], [msg['To']], msg.as_string())
            s.quit()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('%s:%s: %s: %s' % (fname, exc_tb.tb_lineno, type(e).__name__, e))
            code = 2

    sys.exit(code)

# we wrap stdout/stderr to our own buffer so that any exceptions are caught
_stdout = sys.stdout
_stderr = sys.stderr
sys.stdout = StringIO.StringIO()
sys.stderr = sys.stdout

if os.getuid() != 0:
    print("aptcron requires root-privileges to run.")
    send_mail(config, args, _stdout, _stderr, context, code=1)

if args.random_time:
    now = datetime.now().replace(second=0, microsecond=0)
    start = now.replace(minute=now.minute + 3)
    end = now.replace(hour=23, minute=59)

    try:
        start_range, end_range = args.random_time.split('-')

        if start_range:
            start = datetime.strptime(start_range, '%H:%M')
            start = now.replace(hour=start.hour, minute=start.minute)
            if start < now:
                start = start.replace(minute=now.minute + 3)
        if end_range:
            end = datetime.strptime(end_range, '%H:%M')
            end = now.replace(hour=end.hour, minute=end.minute)
            if end < start:
                end = now.replace(hour=23, minute=59)
    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print('%s:%s: %s: %s' % (fname, exc_tb.tb_lineno, type(e).__name__, e))
        print('%s: Could not parse time range.' % args.random_time)
        send_mail(config, args, _stdout, _stderr, context, code=2)

    random.seed()
    time = random.choice(list(timerange(start, end)))

    aptcron = [parser.prog]
    cli_args = [('--%s' % k.replace('_', '-'), v) for k, v in vars(args).items()
                if k != 'random_time' and v != parser.get_default(k)]
    [aptcron.extend(arg) for arg in cli_args]

    p = Popen(['at', time.strftime('%H:%M')], stdin=PIPE, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate(input=' '.join(aptcron))

    sys.exit(0)

try:
    # initialize cache:
    cache = apt.Cache()

    # update the APT cache:
    if not config.getboolean(args.section, 'no-update'):
        cache.update()

    # list upgradeable packages
    cache.open(None)
    cache.upgrade(dist_upgrade=not config.getboolean(args.section, 'no-dist-upgrade'))

    packages = [(
        p.name,
        p.candidate.version if p.candidate else None,
        p.installed.version if p.installed else None,
    ) for p in cache.get_changes()]
    context['num'] = len(packages)  # update context with number of updates

    seen = []
    if config.getboolean(args.section, 'only-new') and os.path.exists(SEEN_CACHE):
        seen = pickle.load(open(SEEN_CACHE))
        packages = [p for p in packages if p not in seen]

    if packages:
        if config.getboolean(args.section, 'only-new') and seen:
            print("{num} available update(s), new since the last mail:\n".format(
                  num=context['num']))
        else:
            print("{num} available update(s):\n".format(num=context['num']))
    elif config.getboolean(args.section, 'force'):
        print("No packages found.")

    for name, new, old in packages:
        pkg = cache[name]
        if pkg.marked_delete:
            print('* %s: %s -> Will be removed' % (name, new))
        elif pkg.marked_install:
            print('* %s: %s -> Will be newly installed' % (name, new))
        elif pkg.marked_downgrade:
            print('* %s: %s -> %s - Will be newly downgraded' % (name, new, old))
        else:  # most common case: a simple package upgrade
            print('* %s: %s -> %s' % (name, new, old))

    if config.getboolean(args.section, 'only-new'):
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)
        if context['num'] == 0 and os.path.exists(SEEN_CACHE):  # no new packages at all!
            os.remove(SEEN_CACHE)
        else:
            pickle.dump(seen + packages, open(SEEN_CACHE, 'w'))

    if packages:
        print("\nPlease update all packages at your earliest convenience.")

    # finally send a mail on success
    send_mail(config, args, _stdout, _stderr, context)
except Exception as e:
    exc_type, exc_obj, exc_tb = sys.exc_info()
    fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    print('%s:%s: %s: %s' % (fname, exc_tb.tb_lineno, type(e).__name__, e))
    send_mail(config, args, _stdout, _stderr, context, code=1)
