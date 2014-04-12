# Run aptcron at a random time of day using the "at" command.
# The time range is configured with the random-time setting in /etc/aptcron.d/

# m h dom mon dow   user    command
0 0   * * *         root    aptcron
