#!/usr/bin/env python3

class UnknownPaxosMessageType(Exception): pass

from collections import Counter
import time
from debug import debug

# Implement Paxos.

# IMPORTANT: Notice that there is no networking stuff in this file.
# This is for ease of debugging. 
# You simply give a PaxosNode a 'send' function that takes a dict with
# keys 'to' and 'from', where 'to' is one of the addrs in otherAddrs (was was passed in to the constructor)
# and 'from' is an addr that other PaxosNodes can reach you at thru their own 'send' function calls.
# Also, it is up to you to call PaxosNode.rx() with the appropriate args. See paxosreplicator.py for an example.
# This allows you to test this module without worrying about shitty things like 
# network connections. You can just arrange for the PaxosNodes to directly call each others' rx functions 
# by giving them a special 'send' function.

####################################################


# IMPORTANT: Lamport uses natural numbers for proposal numbers. 
# He leaves as an implementation detail the problem of choosing them uniquely. 
# We do it like this. We assume each proposer has a unique identifier
# 'id' and a local proposal number 'c', both natural numbers. 
# We represent a proposal number 'n' as the tuple (c,id). 
# The ordering works like this: (a,b) < (c,d) iff (a<c or (a==c and b<d)). 
# This is precisely how Python orders tuples. 
# However, "explicit is better than implicit", 
# so we define the Num class and define a total ordering on it. 

# http://stackoverflow.com/questions/18005172/get-the-object-with-the-max-attributes-value-in-a-list-of-objects        
from functools import total_ordering

@total_ordering
class Num(object):
    def __init__(self,ctr=None,pid=None):
        self.c  = ctr if ctr is not None else 0
        self.id = pid if pid is not None else 0

    def __lt__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return (self.c < other.c) or (self.c == other.c and self.id < other.id)

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return (self.c == other.c) and (self.id == other.id)

    def __str__(self):
        return '<Num ctr={} , pid={}>'.format(self.c,self.id)

    def __hash__(self):
        return hash((self.c,self.id))

    def __add__(self,n):
        return Num(self.c + n, self.id)


# A Proposal is just a Num and a proposed value. 
# We define a total ordering on the Proposal for ease of 
# finding things like the "highest-numbered proposal" using
# the built-in 'max' function.

@total_ordering
class Proposal(object):
    def __init__(self,n=None,v=None):
        self.n = n if n is not None else Num()
        self.v = v if v is not None else None  # can't be 'BLANK VALUE' because want just-awoken folks to be able to get up-to-date by proposing 'None' and we require that non-consensus nodes reply with None to communicate that they haven't reached consensus.

    def __lt__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.n < other.n

    def __eq__(self, other):
        if not isinstance(other, type(self)): return NotImplemented
        return self.n == other.n

    def __str__(self):
        return '<Proposal n={} , v={}>'.format(self.n,self.v)

    def __hash__(self):
        return hash((self.n,self.v))


#############################################################

class PaxosNode(object):
    """docstring for PaxosNode"""
    def __init__(self, nodeid, otherAddrs, sendfn):
        self.send = sendfn

        # Proposer
        self.vdefault = None 
        self.id = nodeid
        self.P_acceptors = [self.id] + otherAddrs
        # must rx > this many responses to my 'prepare reqs' from A's to have buy-in from majority of A's:
        self.MAJORITY = (0+len(self.P_acceptors))/2.0  # (of acceptors) WARNING: assumes self is already in the list of acceptors        
        self.prepare_responses = {}

        # Acceptor
        self.highest_accepted_proposal = None  # Warning: This must be None, not Proposal(); need to remember if an acceptor hasn't heard any proposals yet.
        self.highest_responded_prepreq = Num(ctr=0,pid=self.id)
        self.A_learners = [self.id] + otherAddrs 

        # Learner
        self.L_accepted_values = {}
        self.v = None


    def __str__(self):
        return '\n   <PaxosNode id={} VALUE = {} max-resp-prepreq={} max-acc-prop={} >\n'.format(
                self.id,
                self.v,
                self.highest_responded_prepreq,
                self.highest_accepted_proposal
                )

    def initiate_paxos(self,v):
        debug('PAXOS NODE id={}: Initiating Paxos algorithm! Default v={}'.format(self.id,v))
        self.P_propose(v)

    def rx(self,d):
        t = d['type']
        if t == 'prepare request':
            self.A_rx_prepare_request(d)
        elif t == 'accept request':
            self.A_rx_accept_request(d)
        elif t == 'prepare response':
            self.P_rx_prepare_response(d)
        elif t == 'decision':
            self.L_rx_decision(d)
        else:
            raise UnknownPaxosMessageType(d)

    ###########################################
    # Proposer methods:

    def P_propose(self,v):

        debug('P{}: New proposal. V={}'.format(self.id,v))
        self.vdefault = v

        # Phase 1a. A proposer selects a proposal number n and sends 
        # a prepare request with number n to a majority of acceptors.


        # Increment my existing highest Num. Dedicate myself to promoting the new value.
        n = self.highest_responded_prepreq + 1
        self.prepare_responses[n] = {}  # I may have multiple prepare-requests in the air, 
                                        # each with different n. Group their responses by n.

        # Don't have to explicitly vote for myself, I'm in my own list of acceptors and learners.

        for to in self.P_acceptors:
            debug('P{}: proposing n={} to A={}'.format(self.id, n, to))
            d = {
                'from': self.id,
                'to': to,
                'type': 'prepare request',
                'n':n
                }
            if to == self.id:
                self.A_rx_prepare_request(d)
            else:
                self.send(d)
            
    def P_rx_prepare_response(self,d):

        # Phase 2a. If the proposer receives a response to its prepare requests 
        # (numbered n) from a majority of acceptors, then it sends an accept
        # request to each of those acceptors for a proposal numbered n with
        # a value v, where v is the value of the highest-numbered proposal 
        # among the responses, or is any value if the responses reported no proposals.

        debug('P{}: rxd prepresp from {} with n={}, p={}'.format(self.id,d['from'],d['n'],d['p']))

        n = d['n'] 
        if n not in self.prepare_responses:
            print("!!!!!!!!!P{}: Shouldn't happen: Somehow I rxd a repsonse to a prepare-request with an n I didn't send: {}".format(self.id,d))

        self.prepare_responses[n][d['from']] = d  # for this n, remember who voted for what.

        if len(self.prepare_responses[n]) > self.MAJORITY:  # if we get a majority response for this n, good.
            debug('P{}: For n={}, I have prepresps from {} > majority={}!'.format(self.id,n,len(self.prepare_responses[n]),self.MAJORITY))
            # Fetch the 'real' proposals - the non-None proposals from each prepare response. Also, disallow proposals that propose the value 'None'.
            # This allows us to get a node up-to-date just by trying to propose the value 'None', without risking reaching consensus 
            # on 'None' if the network has not yet reached consensus.
            # IOW, a proposal isn't considered if it's None, or if it's non-None but its proposed value is None.
            proposals = [r['p'] for r in self.prepare_responses[n].values() if not (r['p'] is None or (r['p'] is not None and r['p'].v is None))]
            if len(proposals) > 0:
                highest_numbered_proposal = max(proposals)
                v = highest_numbered_proposal.v
                debug('P{}: Highest-numbered proposal\'s val in prepresps is v={}'.format(self.id,v))
            else:
                debug('P{}: No vals in prepresps, I pick v={}'.format(self.id,self.vdefault))
                v = self.vdefault

            p = Proposal(n,v)

            for to in self.prepare_responses[n].keys():  # to each Acceptor I've heard from
                debug('P{}: txing accept req to A={} with proposal={}'.format(self.id,to,p))
                r = {
                    'from': self.id,
                    'to': to,
                    'type': 'accept request',
                    'p': p
                    }
                if to == self.id:  # my own self-vote
                    self.A_rx_accept_request(r)
                else:

                    self.send(r)


    ###########################################
    # Acceptor methods:

    def A_rx_prepare_request(self,d):

        # Phase 1b. If an acceptor receives a prepare request with number n 
        # greater than that of any prepare request to which it has already responded, 
        # then it responds to the request with (1) a promise not to accept 
        # any more proposals numbered less than n and (2) with the 
        # highest-numbered proposal (if any) that it has accepted.

        debug('A{}: rxd prepreq {}. My max responded prepreq={}, max accprop={}.'.format(
            self.id,d['n'],self.highest_responded_prepreq,self.highest_accepted_proposal))

        if d['n'] > self.highest_responded_prepreq:
            debug('A{}: New prepreq beats mine. Responding to prepreq...'.format(self.id))
            self.highest_responded_prepreq = d['n']
            r = {
                'from': self.id,
                'to': d['from'],
                'type': 'prepare response',
                'p': self.highest_accepted_proposal,
                'n': d['n']
                }
            if r['to'] == self.id:
                # Just call it directly instead of going over the network.
                self.P_rx_prepare_response(r)
            else:
                self.send(r)
        else:
            debug('A{}: New prepreq is too old. Discarding.'.format(self.id))


    def A_rx_accept_request(self,d):

        # Phase 2b. If an acceptor receives an accept request for 
        # a proposal numbered n, it accepts the proposal unless it 
        # has already responded to a prepare request having a number greater than n.
        #
        # ie, if self.highest_responded_prepreq <= n, then accept the proposal in the 'accept request'.

        debug('A{}: rxd accept req p={}, my highest-resp-prepreq={}.'.format(
            self.id,
            d['p'],
            self.highest_responded_prepreq))
        
        if self.highest_responded_prepreq <= d['p'].n:
            debug('A{}: Accepting!'.format(self.id))
            self.highest_accepted_proposal = d['p'] # accept the proposal

            # Phase 3. (Learning a Chosen Value) To learn that a value has been chosen, 
            # a learner must find out that a proposal has been accepted by
            # a majority of acceptors. The obvious algorithm is to have each acceptor, 
            # whenever it accepts a proposal, respond to all learners, sending them the proposal. 

            debug('A{}: Telling my learners:'.format(self.id))
            for l in self.A_learners:
                debug('A{}: telling Learner l={} about my acceptance of proposal p={}'.format(self.id,l,self.highest_accepted_proposal))
                r = {
                    'from': self.id,
                    'to': l,
                    'type': 'decision',
                    'p': self.highest_accepted_proposal
                    }
                if r['to'] == self.id:
                    self.L_rx_decision(r)
                else:
                    self.send(r)
        else:
            debug('A{}: Rxd accept req w/ too-old proposal. Ignoring.'.format(self.id))


    ###########################################
    # Learner methods:


    def L_rx_decision(self,d):

        # Phase 3. (Learning a Chosen Value) To learn that a value has been chosen, 
        # a learner must find out that a proposal has been accepted by
        # a majority of acceptors.

        # Q: Since a learner is only contacted by an acceptor once the acceptor accepts 
        # a proposal, and that only happens once the proposer has marshaled a majority of acceptors,
        # then it seems that a learner, upon rxing a 'decision' from an acceptor, can conclude
        # that this value has been accepted by a majority of acceptors, and that it needn't 
        # wait to receive 'decision' msgs from a majority of acceptors. As soon as it rxs
        # a single 'decision' msg, it can write that value to self.v.

        # Q: If we wait for a majority of 'decide' msgs, and some get dropped, a L won't 
        # learn the decided value. Is that wrong?
        # A: Maybe. I'll wait for a majority anyway.
        

        debug('L{}: Acceptor{} decided proposal p={}'.format(self.id,d['from'],d['p']))

        self.L_accepted_values[d['from']] = d['p'].v

        debug('BTW, heres L_accepted_values:')
        for k,v in self.L_accepted_values.items():
            debug('from:',k,'logvalue:',v)

        # If a majority of Acceptors agree, set our value.

        if len(self.L_accepted_values) == 0: return

        v,c = Counter(self.L_accepted_values.values()).most_common(1)[0]
        if c > self.MAJORITY:
            debug('L{}: majority of As accepted val={}!'.format(self.id,v))
            self.v = v
        else:
            debug("L{}: Most common val={} appears {} times < MAJORITY={}. Learner can't accept yet.".format(
                self.id,v,c,self.MAJORITY) )
