# Run aptcron at a random time of day using the "at" command.

# m h dom mon dow   user    command
0 0   * * *         root    aptcron --random-time
