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




import requests
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import PBB_settings
import PBB_Debug


added = open('alreadyadded.txt', 'r')
line = added.readline()
alreadyAdded = []
while (line != ""):
    alreadyAdded.append(line.strip())
    line = added.readline()

f1 = open('alreadyAdded.txt', 'a+')



mygeneinfo_url =  "http://mygene.info/v2/query?q=_exists_:wikipedia&fields=wikipedia,entrezgene&size=15000"
r = requests.get(mygeneinfo_url)

mappings = r.json()
PBB_Debug.prettyPrint(mappings)

# Get entrezgene - Wikidata mapping
entrezWikidataIds = dict()
wdqQuery = "CLAIM[351]"
InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="351")
logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

for geneItem in InWikiData.wditems["props"]["351"]:
    entrezWikidataIds[int(geneItem[2])] = geneItem[0]

for hit in mappings["hits"]:
    print(hit["entrezgene"])
    f1.write(str(hit["entrezgene"])+"\n")
    data2add = []
    try:
      if hit["entrezgene"] in entrezWikidataIds.keys() and hit["wikipedia"]["url_stub"].count("?")==0 and str(hit["entrezgene"]) not in alreadyAdded:
        print(entrezWikidataIds[hit["entrezgene"]])
        wdPage = PBB_Core.WDItemEngine('Q'+str(entrezWikidataIds[hit["entrezgene"]]),  data = data2add, server="www.wikidata.org", domain="genes")
        wdPage.set_sitelink(site="enwiki", title = hit["wikipedia"]["url_stub"])
        # PBB_Debug.prettyPrint(wdPage.get_wd_json_representation())
        try:
           wdPage.write(logincreds)
        except Exception as e:
            if len(str(e).split("[[")[1].split("|"))>0:
                page2rm_sitelink = (str(e).split("[[")[1].split("|")[0])
                wdProteinPage = PBB_Core.WDItemEngine(page2rm_sitelink,  data = data2add, server="www.wikidata.org", domain="proteins")
                wdProteinPage.set_sitelink(site="enwiki", title = "")
                print("Writing protein page without sitelink")
                wdProteinPage.write(logincreds)
                print("Writing gene page without sitelink")
                wdPage.write(logincreds)
            else:
                f = open('/tmp/exceptions_fixScript.txt', 'a+')
                f.write(str(e)+"\n")
                f.close()

    except:
        f = open('/tmp/exceptions_fixScript.txt', 'a+')
        f.write(str(hit["entrezgene"])+"Wasnt processed!\n")
        f.close()



