#!/bin/bash

echo "There are $(lsof -i | egrep "^python3" | wc -l ) open python3 sockets:"
lsof -i | egrep "^python3"

if [[ "$?" -eq "0" ]]  # grep found something
    then

    for f in $(lsof -i | egrep "^python3" | cut -d" " -f 2)
    do 
        echo "Killing python3 process $f with open port..."
        kill $f
    done

fi