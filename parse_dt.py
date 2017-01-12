#!/usr/bin/env python
# encoding: utf-8

import sys
import os

def parse_dt(path):
    rooms = file(path).read().split('\nS\n')
    for r in rooms:
        
        try:
            r = r.split('#')[1]
            vnum = r.split('\n')[0].strip()
            name = r.split('\n')[1][:-1].strip()
            desc = r.split('\n~')[0].split('~\n')[1].strip()
            bv = r.split('\n~')[1].split()[1].strip()
            
            if bv.find('b0') > -1:
                print vnum[:-2], vnum, name
                #print vnum, name, bv
                #print desc
                #print ''
        except:
            pass

for i in sys.argv[1:]:
    parse_dt(i)

