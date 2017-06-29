#!/usr/bin/env python3

import sys, pickle, json
from collections import Counter
from debug import debug
import network
import os


def main():
    ME = sys.argv[1]  
    MY_ADDR = (sys.argv[2], int(sys.argv[3]))
    
    def parser(b):
        d = pickle.loads(b)
        if 'cmd' in d and d['cmd']=='k': raise network.KillMe()
        filename = d['filename']
        offset = d['offset']
        size = d['size']
        Map(ME,filename,offset,size)
        return b'Done!'

    network.worker(MY_ADDR,parser)


def Map(mapid,filename,offset,size):
    """
    A mapper receives a text filename F (e.g. file1.txt), 
    an offset O (e.g. 0), and a size S(e.g. 1000). 
    Then, it opens the file whose name is F, 
    reads the text starting from offset O, with the size S. 
    The mapper splits the text on spaces into words, 
    converts each word to an orders pair 〈word,1〉, 
    and writes that to an output file named 
    {F}_{I}_{mapper_id} where F is the original filename, 
    I means intermediate, and mapper_id is 
    the id of the current mapper.
    """
    print('Mapping file {}, offset={}, size={}...'.format(filename,offset,size))
    s = open(filename,'r').read(offset+size)[offset:]
    debug('Read string:')
    debug('\"{}\"'.format(s))
    words = [w.strip() for w in s.split()]
    # counts = Counter(words)    # According to the assignment, the mapper should only output <w,1> for w in words.
    counts = [(w,1) for w in words]
    path,inname = os.path.split(filename)
    outname = '{}_I_{}'.format(inname,mapid)
    out = os.path.join(path,outname)
    json.dump(counts,open(out,'w'))
    print('Mapped to file',out)


if __name__ == '__main__':
    main()