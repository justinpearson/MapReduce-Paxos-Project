#!/usr/bin/env python3

import sys, json, pickle
from collections import Counter
from debug import debug
import network
import os


def main():
    MY_ADDR = (sys.argv[1], int(sys.argv[2]))
    network.worker(MY_ADDR,parser)

def parser(b):
    d = pickle.loads(b)
    if 'cmd' in d and d['cmd']=='k': raise network.KillMe()
    filenames = d['filenames']
    reduce(filenames)
    return b'Done!'

def reduce(fs):
    """
    A reduce receives a message consists of multiple
    intermediate filenames(e.g. f1_I_1,f1_I_2). Then it reads
    these files and merge the counts for each word. It could
    be implemented using a dictionary where a word is a keys
    and its count is the corresponding value. If a word is
    not in the dictionary, it is inserted to the dictionary
    with a count of 1 in its first occurrence. A word count
    is incremented every time it occurs.  A reducer should
    output keys and their corresponding count to a file named
    {filename}_{reduced} where filename is the original input
    filename.
    """
    print("Reducing:",fs)
    counts = Counter()
    for f in fs:
        # The assignment says the mapper should simply lists the words:
        # [["It", 1], ["was", 1], ["a", 1], ["dark", 1], ... ]
        # Therefore the reducer needs to tally these words.
        # I think it would be more realistic if the mapper did some 
        # actual work and then the reducer would aggregate the
        # mappers' results.
        words = [tup[0] for tup in json.load(open(f,'r'))]  # Turn to list of just words.
        counts.update(Counter(words))
    path,fname = os.path.split(fs[0])
    prefix = fname.split('_')[0]
    outname = prefix+'_reduced'
    out = os.path.join(path,outname)
    json.dump(counts,open(out,'w'))
    print('Reduced to',out)


if __name__ == '__main__':
    main()    