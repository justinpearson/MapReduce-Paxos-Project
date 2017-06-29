#!/bin/bash

set -e 
set -x


CLI1=" 127.0.0.1 5000"
MAP1A="127.0.0.1 5001"
MAP1B="127.0.0.1 5002"
RED1=" 127.0.0.1 5003"
PAX1=" 127.0.0.1 5004"

CLI2=" 127.0.0.1 5005"
MAP2A="127.0.0.1 5006"
MAP2B="127.0.0.1 5007"
RED2=" 127.0.0.1 5008"
PAX2=" 127.0.0.1 5009"

CLI3=" 127.0.0.1 5010"
MAP3A="127.0.0.1 5011"
MAP3B="127.0.0.1 5012"
RED3=" 127.0.0.1 5013"
PAX3=" 127.0.0.1 5014"

# Note: 2 levels of debugging:
# 1: pdb:
# xterm -geometry 55x24+000+000  -e /bin/bash -l -c "python -m pdb ./cli.py $PORT_NODE1_CLI $PORT_NODE1_MAP1 $PORT_NODE1_MAP2 $PORT_NODE1_RED $PORT_NODE1_PAX" &
# 2: extra print stmts: enable debugging in debug.py:  DEBUG = True

# Node 1
xterm -geometry 55x24+000+000  -e /bin/bash -l -c "./cli.py $CLI1 $MAP1A $MAP1B $RED1 $PAX1" &
xterm -geometry 55x24+340+000  -e /bin/bash -l -c "./mapper.py 1 $MAP1A" &
xterm -geometry 55x24+680+000  -e /bin/bash -l -c "./mapper.py 2 $MAP1B" &
xterm -geometry 55x24+1020+000 -e /bin/bash -l -c "./reducer.py $RED1" &
xterm -geometry 55x24+1360+000 -e /bin/bash -l -c "./paxosreplicator.py $PAX1 $PAX2 $PAX3" &

# Node 2
xterm -geometry 55x24+000+345  -e /bin/bash -l -c "./cli.py $CLI2 $MAP2A $MAP2B $RED2 $PAX2" &
xterm -geometry 55x24+340+345  -e /bin/bash -l -c "./mapper.py 1 $MAP2A" &
xterm -geometry 55x24+680+345  -e /bin/bash -l -c "./mapper.py 2 $MAP2B" &
xterm -geometry 55x24+1020+345 -e /bin/bash -l -c "./reducer.py $RED2" &
xterm -geometry 55x24+1360+345 -e /bin/bash -l -c "./paxosreplicator.py $PAX2 $PAX1 $PAX3" &

# Node 3
xterm -geometry 55x24+000+690  -e /bin/bash -l -c "./cli.py $CLI3 $MAP3A $MAP3B $RED3 $PAX3" &
xterm -geometry 55x24+340+690  -e /bin/bash -l -c "./mapper.py 1 $MAP3A" &
xterm -geometry 55x24+680+690  -e /bin/bash -l -c "./mapper.py 2 $MAP3B" &
xterm -geometry 55x24+1020+690 -e /bin/bash -l -c "./reducer.py $RED3" &
xterm -geometry 55x24+1360+690 -e /bin/bash -l -c "./paxosreplicator.py $PAX3 $PAX1 $PAX2" &

echo "waiting..."
wait

