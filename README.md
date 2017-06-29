# MapReduce / Paxos class project

A class project that implements MapReduce and Multi-Paxos on a cloud computing infrastructure.

## Table of Contents

- [Video overview of project](#video-of-project)
- What is this project?
- What does the code do?
- How do I run it?
- [Course details](#course-details)
- Contact me



## Video of project

Besides this documentation, I made a video of this project in 3 parts:

[0:00 Description of the problem setup](https://youtu.be/4J92zbRWlzk)
[9:40 Code demo](https://youtu.be/4J92zbRWlzk?t=9m40s)
[14:36 Explanation of code architecture](https://youtu.be/4J92zbRWlzk?t=14m36s)

![](Images/paxos-project-on-youtube.png)





## What is this project?

The project implements the MapReduce parallel computing algorithm and the Multi-Paxos distributed consensus algorithm.

![](mapreduce-multipaxos-overview-annotated.png)

The code runs on 3 nodes (which may be computers in the cloud or processes running on your local computer); each node is commanded by a human through a command-line interface (CLI). Each node has a large text file on disk and uses MapReduce to parallelize the computation of a word tally of its text file. Then each node uses Multi-Paxos to distribute its tally to its two neighbors in the form of a replicated log. When it completes, each computer has an array of 3 word tallies, one for each text file. Paxos ensures that the arrays are all identical.

For the class project, we ran our code on three small Linux instances in the Eucalyptus Cloud Computing infrastructure (similar to AWS). However, you can also run the code locally as described below

Each node runs five processes: a command-line interface, two mappers, a reducer, and a Paxos replication module (PRM). The PRM implements Multi-Paxos to replicate the reducer's output across all three PRMs.

- For the full problem statement from the class, please see `docs/mapreducereplicate.pdf`.
- For background on Paxos, see my video "Paxos in Pictures": <https://youtu.be/UUQ8xYWR4do>
- For a video description of the problem statement: <https://youtu.be/4J92zbRWlzk>




## Quick demo of Paxos

If you just want a quick test of the Paxos library without running the whole demo, run `test_paxos.py`, which exercises only `PaxosNode.py`. 

The `test_paxos.py` file is very short. It sets up 3 nodes as Python objects and establishes a very simple communication mechanism between them.

```python

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
            print(p)            # Their values are all "None"

        p1.initiate_paxos("P1's awesome value")

        print("AFTER P1:")
        for p in [p1,p2,p3]:
            print(p)            # Their values are all "P1's awesome value"

        # Once they've reached consensus, the agreed-upon
        # value can never change. See:

        p2.initiate_paxos("How about P2 gets a turn?")

        print("AFTER P2:")
        for p in [p1,p2,p3]:
            print(p)           # Their values are still "P1's awesome value"


    if __name__ == '__main__':
        main()
```



## Code demo

For a full code demo please see the video:

- [9:40 Code demo](https://youtu.be/4J92zbRWlzk?t=9m40s)

The basic idea is to use each of the 3 nodes' CLIs to (1) launch MapReduce jobs and (2) distribute their results with Paxos. 

The Paxos part of the code works like this:

![](step1.png)

![](step2.png)

![](step3.png)

![](step4.png)


For more details, please see the code demo.




## Running the code


### Running the code locally

0. Ensure you have `xterm` installed.  On a Mac, install XQuartz from the XQuartz official website at <https://www.xquartz.org/>.
1. Run `run-locally.sh`, which spawns 15 processes in individual `xterm` windows for the CLI, 2 mappers, reducer, and PRM on each of 3 nodes.



### Running the code in the cloud

For the course project, we used the Eucalyptus cloud computing infrastructure (see the Eucalyptus login page at <https://eucalyptus.cloud.eci.ucsb.edu>. The dashboard looks like this:

![alt txt](Images/eucalyptus-ssh-into-3.png)

**Important:** The scripts `copy-to-euc.sh` and `run-eucalyptus.sh` reference an ssh key named `jppucsbcs171-2.pem` that's used to log in to cloud computers. You should replace these references with the name of your own ssh key.


0. Edit `copy-to-euc.sh` to use the IP addresses of your particular cloud instances. Also edit the name of the SSH key.
1. Run `copy-to-euc.sh`, which copies the project files to the three Eucalyptus nodes. (Note: It wipes out whatever was on those nodes!)
2. Edit `run-eucalyptus.sh` to use the IP addresses of your cloud machines.
3. Run `run-eucalyptus.sh`, which starts 15 xterm windows -- one for each of the 3 nodes and 5 components (CLI, 2 mappers, reducer, PRM). 


Once the 15 xterm windows are up, you can type into the terminal windows in the leftmost column: these 3 xterm windows are the three nodes' CLIs. Type 'h' for a list of valid commands. Type 'k' to kill all processes on a node.




## Course details

- CS 171: Distributed Systems
- Professor Amr El Abbadi
- Spring quarter 2017
- University of California, Santa Barbara
- [CS 171 course website on Piazza](https://piazza.com/class/j0gbt8opotz2rh)



## Contact

[http://justinppearson.com](http://justinppearson.com)



