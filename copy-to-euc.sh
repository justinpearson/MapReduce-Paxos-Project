#!/bin/bash

# For IP addrs, see:
# https://eucalyptus.cloud.eci.ucsb.edu/instances

echo "---> Note: the first time you have new instances, must manually ssh into all of them."

set -e # bail if fail
set -x # echo

USR="ubuntu"

# May 22, 2017:
IP_PUBLIC="128.111.84.235"
IP_PRIVATES="10.2.249.107 10.2.249.117 10.2.249.123"

KEY="jppucsbcs171-2.pem"


# NUKE AND PAVE:

ssh -t -i $KEY $USR@$IP_PUBLIC rm -rf "*"
scp -i $KEY -r . $USR@$IP_PUBLIC:~/
for IP in $IP_PRIVATES
do
    ssh -t -i $KEY $USR@$IP_PUBLIC ssh -t -i $KEY $USR@$IP rm -rf "*"   
    ssh -t -i $KEY $USR@$IP_PUBLIC scp -i $KEY -r . $USR@$IP:~/
done
