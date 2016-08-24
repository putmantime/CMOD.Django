#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Authors: 
  Andra Waagmeester (andra' at ' micelio.be)

This file is part of ProteinBoxBot.

ProteinBoxBot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ProteinBoxBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProteinBoxBot.  If not, see <http://www.gnu.org/licenses/>.
'''

__author__ = 'Andra Waagmeester'
__license__ = 'GPL'

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import PBB_login
import PBB_settings
import PBB_Functions
import urllib
import urllib3
import certifi
import copy
import requests
import sys
try:
    import simplejson as json
except ImportError as e:
    import json

InWikiData = PBB_Core.WDItemList("CLAIM[699]", "699")
# PBB_Debug.prettyPrint(InWikiData)

file = open('/tmp/doCounts.tsv', 'r')
processedItems = [] 
for lijn in file.readlines():
    processedItems.append(lijn.split('\t')[1])
    

target = open('/tmp/doCounts.tsv', 'a')
for diseaseItem in InWikiData.wditems["props"]["699"]:
    # print diseaseItem
  if not "DOID:"+ diseaseItem[2] in processedItems:
    url = 'https://www.wikidata.org/w/api.php'
    params = {
        'action': 'wbgetentities',
        'sites': 'enwiki',
        # 'languages': 'en',
        'ids': 'Q'+str(diseaseItem[0]),
        'format': 'json'
    }

    reply = requests.get(url, params=params)

    wd_reply = json.loads(reply.text, "utf-8")['entities']['Q'+str(diseaseItem[0])]
    #PBB_Debug.prettyPrint(wd_reply)
    label = wd_reply["labels"]["en"]["value"].replace(u'\xfc', '')
    if 'sitelinks' in wd_reply:
        if 'enwiki' in wd_reply['sitelinks']:
            print str(label)+"\tDOID:"+ diseaseItem[2]+"\t https://en.wikipedia.org/wiki/"+wd_reply['sitelinks']['enwiki']['title'].replace(" ", "_")
            target.write(str(label)+"\tDOID:"+ diseaseItem[2]+"\t https://en.wikipedia.org/wiki/"+wd_reply['sitelinks']['enwiki']['title'].replace(u"\u2013", "-").replace(" ", "_")+"\n")
        else:
            print str(label)+"\tDOID:"+ diseaseItem[2]+"\t na"
            target.write(str(label)+"\tDOID:"+ diseaseItem[2]+"\t na\n")
    else:
        print str(label)+"\tDOID:"+ diseaseItem[2]+"\t na"
        target.write(str(label)+"\tDOID:"+ diseaseItem[2]+"\t na\n")
    # sys.exit()