# Run aptcron sometime in the morning (between 3:00 am and 8:00 am)
SHELL=/bin/bash

# m h dom mon dow user  command
0 2     * * *   root    echo aptcron | at $(($RANDOM \% 5 + 3)):$(($RANDOM \% 60)) > /dev/null
