# Run aptcron.
#
# NOTE: The actual time of execution will depend on the configuration files in
#       /etc/aptcron.d/: If the random-time is given, it will execute sometime
#       in that timerange, if not, aptcron will execute right away.

# m h dom mon dow user  command
0 0     * * *   root    aptcron
