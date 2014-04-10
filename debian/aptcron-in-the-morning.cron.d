# Run aptcron sometime in the morning (between 3:00 am and 8:00 am)
SHELL=/bin/bash

# m h dom mon dow user  command
55 2     * * *   root    echo aptcron | at $(($RANDOM \% 5 + 3)):$(printf \%02d $(($RANDOM \% 60))) 2> /dev/null
