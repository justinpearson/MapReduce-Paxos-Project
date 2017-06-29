#!/bin/bash

set -e 
set -x

KEY="jppucsbcs171-2.pem"
USR="ubuntu"

PYTHON="python3"

IP_PUBLIC="128.111.84.235"

NODE1="10.2.249.107"
NODE2="10.2.249.117"
NODE3="10.2.249.123"

CLI1=" $NODE1 5000"
MAP1A="$NODE1 5001"
MAP1B="$NODE1 5002"
RED1=" $NODE1 5003"
PAX1=" $NODE1 5004"

CLI2=" $NODE2 5000"
MAP2A="$NODE2 5001"
MAP2B="$NODE2 5002"
RED2=" $NODE2 5003"
PAX2=" $NODE2 5004"

CLI3=" $NODE3 5000"
MAP3A="$NODE3 5001"
MAP3B="$NODE3 5002"
RED3=" $NODE3 5003"
PAX3=" $NODE3 5004"

# Note: to run with debugger:
# xterm -geometry 55x24+000+000  -e /bin/bash -l -c "python -m pdb ./cli.py $PORT_NODE1_CLI $PORT_NODE1_MAP1 $PORT_NODE1_MAP2 $PORT_NODE1_RED $PORT_NODE1_PAX" &

# Note: enable debugging in debug.py:  DEBUG = True

# Node 1
ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE1 "./kill-open-sockets.sh"   # Close residually-open sockets.
xterm -geometry 55x24+000+000  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE1 ./cli.py $CLI1 $MAP1A $MAP1B $RED1 $PAX1" &
xterm -geometry 55x24+340+000  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE1 ./mapper.py 1 $MAP1A" &
xterm -geometry 55x24+680+000  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE1 ./mapper.py 2 $MAP1B" &
xterm -geometry 55x24+1020+000 -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE1 ./reducer.py $RED1" &
xterm -geometry 55x24+1360+000 -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE1 ./paxosreplicator.py $PAX1 $PAX2 $PAX3" &

# Node 2
ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE2 "./kill-open-sockets.sh"   # Close residually-open sockets.
xterm -geometry 55x24+000+345  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE2 ./cli.py $CLI2 $MAP2A $MAP2B $RED2 $PAX2" &
xterm -geometry 55x24+340+345  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE2 ./mapper.py 1 $MAP2A" &
xterm -geometry 55x24+680+345  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE2 ./mapper.py 2 $MAP2B" &
xterm -geometry 55x24+1020+345 -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE2 ./reducer.py $RED2" &
xterm -geometry 55x24+1360+345 -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE2 ./paxosreplicator.py $PAX2 $PAX1 $PAX3" &

# Node 3
ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE3 "./kill-open-sockets.sh"   # Close residually-open sockets.
xterm -geometry 55x24+000+690  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE3 ./cli.py $CLI3 $MAP3A $MAP3B $RED3 $PAX3" &
xterm -geometry 55x24+340+690  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE3 ./mapper.py 1 $MAP3A" &
xterm -geometry 55x24+680+690  -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE3 ./mapper.py 2 $MAP3B" &
xterm -geometry 55x24+1020+690 -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE3 ./reducer.py $RED3" &
xterm -geometry 55x24+1360+690 -e /bin/bash -l -c "ssh -Y -t -i $KEY $USR@$IP_PUBLIC ssh -Y -t -i $KEY $USR@$NODE3 ./paxosreplicator.py $PAX3 $PAX1 $PAX2" &


# Node 1 hard-coded for local testing:
#ssh -t -i jppucsbcs171-2.pem ubuntu@128.111.84.235 ssh -t -i jppucsbcs171-2.pem ubuntu@10.2.249.107 ./kill-open-sockets.sh
#ssh -t -i jppucsbcs171-2.pem ubuntu@128.111.84.235 ssh -t -i jppucsbcs171-2.pem ubuntu@10.2.249.107 python3 -m pdb ./cli.py  10.2.249.107 5000 10.2.249.107 5001 10.2.249.107 5002  10.2.249.107 5003  10.2.249.107 5004
#ssh -t -i jppucsbcs171-2.pem ubuntu@128.111.84.235 ssh -t -i jppucsbcs171-2.pem ubuntu@10.2.249.107 python3 -m pdb ./mapper.py 1 10.2.249.107 5001
#ssh -t -i jppucsbcs171-2.pem ubuntu@128.111.84.235 ssh -t -i jppucsbcs171-2.pem ubuntu@10.2.249.107 python3 -m pdb ./mapper.py 2 10.2.249.107 5002
#ssh -t -i jppucsbcs171-2.pem ubuntu@128.111.84.235 ssh -t -i jppucsbcs171-2.pem ubuntu@10.2.249.107 python3 -m pdb ./reducer.py  10.2.249.107 5003

echo "waiting..."
wait

