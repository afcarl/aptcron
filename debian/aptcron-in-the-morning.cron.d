# Run aptcron sometime in the morning (between 2:00 am and 8:00 am) using the
# "at" command.

# m h dom mon dow   user    command
55 1  * * *         root    aptcron --random-time 2:00-8:00
