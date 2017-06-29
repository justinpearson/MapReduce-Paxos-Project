#!/usr/bin/env python3

from PaxosNode import PaxosNode 

def main():

    def send(d,p1,p2,p3):
        if d['to'] == 'a': p1.rx(d)
        if d['to'] == 'b': p2.rx(d)
        if d['to'] == 'c': p3.rx(d)
    
    p1 = PaxosNode('a',['b','c'],lambda d: send(d,p1,p2,p3))
    p2 = PaxosNode('b',['a','c'],lambda d: send(d,p1,p2,p3))
    p3 = PaxosNode('c',['a','b'],lambda d: send(d,p1,p2,p3))

    print("BEFORE:")
    for p in [p1,p2,p3]:
        print(p)

    p1.initiate_paxos("P1's awesome value")

    print("AFTER P1:")
    for p in [p1,p2,p3]:
        print(p)

    # Once they've reached consensus, the agreed-upon
    # value can never change. See:

    p2.initiate_paxos("How about P2 gets a turn?")

    print("AFTER P2:")
    for p in [p1,p2,p3]:
        print(p)



if __name__ == '__main__':
    main()