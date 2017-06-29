#!/usr/bin/env python3

import sys, time
from debug import debug
import network

##########################################################


def main():
    # PORT = int(sys.argv[1]) if len(sys.argv)>1 else 5000

    MY_ADDR     = (sys.argv[1], int(sys.argv[2]  ))
    MAP1_ADDR   = (sys.argv[3], int(sys.argv[4]  ))
    MAP2_ADDR   = (sys.argv[5], int(sys.argv[6]  ))
    RED_ADDR    = (sys.argv[7], int(sys.argv[8]  ))
    PAXOS_ADDR  = (sys.argv[9], int(sys.argv[10] ))

    # PORT, PORT_M1, PORT_M2, PORT_RED, PORT_PAXOS = [int(p) for p in sys.argv[1:]]

    print("Hi from CLI on port",MY_ADDR)

    prev = None # previous cmd

    # When a msg comes back to me from the mapper, reducer, or PRM, 
    # I'm expecting it to reply with a certain string.
    def replyfn(b):
        if b == b'Done!':
            debug('He seems to be done!')
        elif b == b'Enqueued msg!':
            debug("He says he'll do it. Not waiting for him!")
        elif b == b'Killed me.':
            debug('He said I killed him.')
        else:
            debug("Hm, he replied with something I didn't expect: {}".format(b))

    while True:
        cmdline = input('Cmd: ')
        if len(cmdline.strip()) == 0 and prev is not None: cmdline = prev  # blank line repeats prev cmd
        tokens = cmdline.split()
        cmd = tokens[0]
        d = {'cmd':cmd}

        if cmd=='help' or cmd=='h':
            print("""
                • map filename
                • reduce filename1 filename2 ...
                • replicate filename
                • stop
                • resume
                • total pos1 pos2 ...
                • print
                • merge pos1 pos2
                • cat filename1 filename2 ...
                """)
            continue

        elif cmd=='map':
            '''splits the file based on its size into 2 equal parts. 
            The split has to cut the file in a space character, not in the middle of a word. 
            Then it maps each half to a mapper using message passing.'''
            if len(tokens)<2:
                print('USAGE: map filename')
                continue
            f = tokens[1]
            s = open(f,'r').read()
            n = len(s)
            i = n//2
            while i<n: # break between words
                if s[i] == ' ': break
                i += 1
            d1 = {'filename':f, 'offset':0, 'size':i}
            d2 = {'filename':f, 'offset':i, 'size':n-i}
            network.send(MAP1_ADDR,d1)
            network.send(MAP2_ADDR,d2)

        elif cmd=='reduce':
            '''sends a message (using sockets) to the reducer with the 
            provided filenames. The reducer has to reduce the intermediate 
            files to a final reduced file.'''
            if len(tokens)<2:
                print('USAGE: reduce f_I_1 f_I_2')
                continue
            fs = tokens[1:]
            d = {'filenames':fs}
            network.send(RED_ADDR,d)

        elif cmd=='replicate':
            '''sends a message to the PRM to replicate the file with
            other computing nodes. Notice that the PRM owns 
            the log with all its log objects.'''
            if len(tokens)<2:
                print('USAGE: replicate f_reduced')
                continue
            f = tokens[1]
            d.update({'filename':f})
            network.send(PAXOS_ADDR,d)

        elif cmd=='stop':
            '''moves the PRM to the stopped state. When the PRM in the stopped
            state, it does not handle any local replicate commands. In addition, it
            drops any log object replicating messages sent by other PRMs in other
            nodes. This is used to emulate failures and how Paxos can still achieve
            progress in the presence of N/2 − 1 failures.'''
            network.send(PAXOS_ADDR,d)

        elif cmd=='resume':
            '''resumes the PRM back to the active state. A PRM in the
            active state should actively handle local replicate commands 
            as well as log object repli- cating messages received by other PRMs.'''
            network.send(PAXOS_ADDR,d)


        # DATA QUERY CALLS
        #￼The CLI sends a query to the PRM, and the PRM prints
        # the answers to these queries in its stdout. There is no
        # need to pass the results back to the CLI. The supported data query calls are:

        elif cmd=='total':
            '''sums up the counts of all the word in all the log positions pos1 pos2,...'''
            logpositions = [int(i) for i in tokens[1:]]
            if len(logpositions) == 0:
                print('USAGE: total logpos1 logpos2 ...')
                continue
            d.update({'logpositions':logpositions})
            network.send(PAXOS_ADDR,d)

        elif cmd=='print':
            '''prints the filenames of all the log objects.'''
            network.send(PAXOS_ADDR,d)

        elif cmd=='merge':
            '''apply the reduce function in log objects in positions pos1 pos2. 
            In other words, it adds up the occurrence of words in log objects
            in positions pos1 and pos2 and prints each word with its corresponding count.'''
            logpositions = [int(i) for i in tokens[1:]]
            if len(logpositions) == 0:
                print('USAGE: merge logpos1 logpos2 ...')
                continue
            d.update({'logpositions':logpositions})
            network.send(PAXOS_ADDR,d)

        # Justin-specific commands

        elif cmd=='cat':
            if len(tokens)<2:
                print('USAGE: cat filename1 filename2 ...')
                continue
            fs = tokens[1:]
            for f in fs:
                print('File "{}":'.format(f))
                print(open(f,'r').read())
                print('')

        elif cmd=='kill' or cmd=='k':
            [ network.send(p,d) for p in [MAP1_ADDR,MAP2_ADDR,RED_ADDR,PAXOS_ADDR] ]
            break

        elif cmd=='q':
            break

        else:
            print('Not familiar with the command "{}", sry lol'.format(cmd))

        prev = cmdline
    print('Bye bye!')

#####################################################


if __name__ == '__main__':
    main()