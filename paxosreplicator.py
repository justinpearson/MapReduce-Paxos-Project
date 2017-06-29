#!/usr/bin/env python3

import sys, time, queue, threading, json, pickle
from collections import Counter
from PaxosNode import PaxosNode 
from debug import debug
import network

class UnknownMessageType(Exception): pass


#########################################################

q = queue.Queue()

def main():

    myAddr      =  (sys.argv[1], int(sys.argv[2]))
    otherAddrs  = [(sys.argv[i],int(sys.argv[i+1])) for i in range(3,len(sys.argv),2)] # allow any number of other PRMs.

    p = PaxosReplicator(myAddr,otherAddrs)

    # Need another thread to listen for Paxos replies. 
    # Otherwise, if we block here until PaxosReplicator.replicate() returns, we'll wait forever 
    # because he's waiting to rx from other Paxos nodes.
    def parser(b):
        q.put(pickle.loads(b))
        return b'Enqueued msg!'

    threading.Thread(target=network.worker, daemon=True, args=[myAddr,parser]).start()

    p.run()

#########################################################



class LogValue(object):
    """ File name and wordcounts:
    self.filename = 'Pride and Prejudice.txt', 
    self.counts = {'a':10, 'the': 12,...}
    Q: Why make a whole class LogValue instead of just a dict?
    A: Can't just be a dict because dicts are unhashable -- error in collections.Counter. Ugh.
    """
    def __init__(self,filename,wordcounts):
        self.filename = filename
        self.wordcounts = wordcounts

    def __str__(self):
        # Summarize the string if it's too long.
        x = sorted(self.wordcounts.items())
        if len(x)>10:
            c = x[:3] + ['...'] + x[-3:]
        else:
            c = x
        return '<Logvalue: {}, counts={} >'.format(self.filename,c)

    def __eq__(self,other):
        return isinstance(other, type(self)) \
                and self.filename==other.filename \
                and self.wordcounts==other.wordcounts

    def __hash__(self):
        return hash((self.filename,tuple(sorted(self.wordcounts.items()))))
   

#########################################################

class PaxosReplicator(object):
    """
    Coordinates the Multi-Paxos algorithm between other PaxosReplicator instances,
    and takes commands from the Command-Line Interface (cli.py).
    """
    def __init__(self,myAddr,otherAddrs):
        self.running = True

        self.myAddr = myAddr
        self.otherAddrs = otherAddrs
        self.num_elems = 3 # there are 3 entries in our multi-paxos log.

        # For each log element that we need to reach consensus on,
        # make a PaxosNode, arrange to have its outgoing msgs
        # tagged with its element index, and give it a function
        # it can use to communicate with the other nodes' PaxosNodes 
        # that correspond to that particular array element.
        #
        # Note the incredibly shitty "i=i" expr in the lambda. 
        # Without it, the value i resolves to the max value of all i's in the range.
        # (This is bad.)
        self.paxosNodes = []
        for i in range(self.num_elems):
            p = PaxosNode(  nodeid=(self.myAddr,i),
                            otherAddrs=[(o,i) for o in otherAddrs],
                            sendfn=lambda d,i=i: network.send(d['to'][0],{'paxos':True,'elem':i,'msg':d}) # [0]: to get the IP addr from the (addr,elementindex) nodeid
                         )
            self.paxosNodes.append(p)


    def get_log(self):
        return [p.v for p in self.paxosNodes]
        # [
        #   LogValue('Pride and Prejudice', Count('a':100,'the':42,...)),
        #   LogValue('Animal Farm', Count(...)),
        #  ...
        # ]


    def run(self):
        while True:
            d = q.get()
            if 'cmd' in d and d['cmd']=='k': break
            self.rx(d)


    def rx(self,d):
        if 'cmd' in d:
            # A message from the CLI.
            cmd = d['cmd']
            if cmd=='replicate':
                self.replicate(d['filename'])
            elif cmd=='stop':
                self.stop()
            elif cmd=='resume':
                self.resume()
            elif cmd=='total':
                self.total(d['logpositions'])
            elif cmd=='print':
                self.print()
            elif cmd=='merge':
                self.merge(d['logpositions'])
            else:
                print('Not familiar with the command "{}", sry lol'.format(cmd))
        elif 'paxos' in d:
            # A message from some Paxos node. Route to my corresponding Paxos node.
            if self.running:
                self.paxosNodes[d['elem']].rx(d['msg'])
        else:
            raise UnknownMessageType(d)


    def replicate(self,f):
        """replicate the file with
        other computing nodes. Notice that the PRM owns 
        the log with all its log objects.

        As shown in Figure 1, the PRM replicates the outputs in a log to
        achieve the same order in all the computing nodes. 
        It is important to replicate log objects in the same order so 
        that clients get the exact same results when they query the
        log in different computing nodes. The details of querying
        the log is explained in the client API in Section 3. 
        The PRM is configured with a port number and it receives
        a filename to replicate (e.g. f1_reduced). The PRM converts
        the file into a log object that has the following attributes: 
        filename and word dictionary. The PRM then tries to replicate the 
        log object in the next available log index using Paxos protocol. If 
        another PRM is competing for the same log position, a replicate 
        command can fail. Therefore, the PRM has to retry replicating 
        the log object in the following log positions until it succeeds.
        """
        if self.running: 
            print("Gonna read file {} and replicate its contents across the Paxos Nodes...".format(f))
        else:
            print("I'm not running, try 'resume' at CLI plz!")
            return

        if f is None:
            # Special value for "I just woke up, get me up-to-date."
            v = None
        else:
            # Normal operation.
            counts = json.load(open(f,'r'))
            v = LogValue(filename=f,wordcounts=counts)  # the value we want to replicate across the other Paxos nodes

        print("Doing Multi-Paxos on LogValue:",v)
        # Multi-paxos: insert v into the next available log entry and simultaneously reach consensus on it with the other Paxos nodes.
        success = False
        for i,p in enumerate(self.paxosNodes): # For each slot in the log,
            if p.v is not None: continue  # skip locations that have already reached consensus 
            attempts = 2
            while p.v is None and attempts > 0:
                debug('Hm, paxosnode={} has value v={} (None). Initiating Paxos {} more times to get v={} in elem {}...'.format(p,p.v,attempts,v,i))
                p.initiate_paxos(v)  # propose v.
                t0 = time.time()
                while time.time()-t0 < 1:  # for 1 sec, check the msg Q and service paxos msgs from it.
                    while not q.empty():
                        d = q.get()
                        if 'paxos' not in d:
                            q.put(d) # whoops, a CLI cmd. Put it back. (Shit, now it's out of order... TODO)
                        else:
                            self.rx(d)
                    time.sleep(.1)
                attempts -= 1
            if p.v == v: 
                debug('Inserted v={} at position {} in log! Great success.'.format(v,i))
                success = True
                break
            else:
                debug('Looks like someone else put val {} at pos {} in the log instead of our v={}, trying next position...'.format(p.v,i,v))
            if success: break 
            
        if success:
            print('Good news, our value {} was accepted in position {} in the log!'.format(v,i))
        else:
            print("Sorry dude, for some reason we couldn't get our value {} in the log. WTF?".format(v))
            
        print("My local log is currently:")
        self.print()
        

    def stop(self):
        '''moves the PRM to the stopped state. When the PRM in the stopped
        state, it does not handle any local replicate commands. In addition, it
        drops any log object replicating messages sent by other PRMs in other
        nodes. This is used to emulate failures and how Paxos can still achieve
        progress in the presence of N/2 − 1 failures.'''        
        print('Disabling paxos...')
        self.running = False

    def resume(self):
        '''resumes the PRM back to the active state. A PRM in the
        active state should actively handle local replicate commands 
        as well as log object replicating messages received by other PRMs.'''

        print('Enabling paxos...')
        self.running = True
        print('Proposing a dummy value to update what I missed...')
        self.replicate(None)



    # DATA QUERY CALLS
    #￼The CLI sends a query to the PRM, and the PRM prints
    # the answers to these queries in its stdout. There is no
    # need to pass the results back to the CLI. The supported data query calls are:


    def total(self,logpositions):
        '''sums up the counts of all the words in all the log positions pos1 pos2,...
        (and prints it?)'''
        log = self.get_log()
        print(sum(sum(log[p].wordcounts.values()) for p in logpositions if p < len(log) and log[p] is not None))

    def print(self):
        '''prints the filenames of all the log objects.'''        
        for i,logval in enumerate(self.get_log()):
            print("\nLOG ENTRY {}: {}".format(i,logval))

    def merge(self,logpositions):
        '''apply the reduce function in log objects in positions pos1 pos2. 
        In other words, it adds up the occurrence of words in log objects
        in positions pos1 and pos2 and prints each word with its corresponding count.'''
        c = Counter()
        log = self.get_log()
        [ c.update(log[p].wordcounts) for p in logpositions if p < len(log) and log[p] is not None ]
        print([(k,v) for k,v in sorted(c.items())])


    # END DATA QUERY CALLS


if __name__ == '__main__':
    main()