# Run aptcron sometime in the morning (between 2:00 am and 8:00 am) using the
# "at" command.
# The time range is configured with the random-time setting in /etc/aptcron.d/

# m h dom mon dow   user    command
55 1  * * *         root    aptcron
