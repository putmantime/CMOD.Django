import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import MicrobeBotWDFunctions as wdo
import MicrobeBotResources as mbr
import time
import json
import re
import pprint
import ast
__author__ = 'timputman'




enzymes = open('/Users/timputman/wikdata_repo/CMOD_APP/enz_out_test.txt', 'r')
count = 0


def mol2qid(moldict):
    mols = []
    for key, value in moldict.items():
        wd= wdo.WDSparqlQueries(prop='P683', string=value)
        mols.append(wd.wd_prop2qid())
    return [x for x in mols if x != 'None']









for i in enzymes:
    i = i.strip()
    enz = ast.literal_eval(i)
    substrateids = mol2qid(enz['Substrates'])
    productids = mol2qid(enz['Products'])

    #pprint.pprint(enz)
    print('subs', substrateids)
    print('prods', productids)