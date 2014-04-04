SHELL=/bin/bash
0 0     * * *   root    at -f /usr/bin/touch $(($RANDOM \% 24)):$(($RANDOM \% 60))
