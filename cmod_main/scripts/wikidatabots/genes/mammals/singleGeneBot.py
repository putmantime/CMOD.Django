#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author:Andra Waagmeester (andra@waagmeester.net)

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
# Load the path to the PBB_Core library
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import PBB_settings

# Resource specific
import gene
import time
import traceback


start = time.time()

speciesInfo = dict()
speciesInfo["human"] = dict()
speciesInfo["9606"] = dict()
speciesInfo["mouse"] = dict()
speciesInfo["10090"] = dict()
speciesInfo["rat"] = dict()

speciesInfo["human"]["taxid"] = "9606"
speciesInfo["human"]["wdid"] = "Q5"
speciesInfo["human"]["name"] = "human"
speciesInfo["human"]["release"] = "Q20950174"
speciesInfo["human"]["genome_assembly"] = "Q20966585"
speciesInfo["human"]["genome_assembly_previous"] = "Q21067546"
speciesInfo["9606"]["taxid"] = "9606"
speciesInfo["9606"]["wdid"] = "Q5"
speciesInfo["9606"]["name"] = "human"
speciesInfo["9606"]["release"] = "Q20950174"
speciesInfo["9606"]["genome_assembly"] = "Q20966585"
speciesInfo["9606"]["genome_assembly_previous"] = "Q21067546"

speciesInfo["mouse"]["taxid"] = "10090"
speciesInfo["mouse"]["wdid"] = "Q83310"
speciesInfo["mouse"]["name"] = "mouse"
speciesInfo["mouse"]["release"] = "Q20973051"
speciesInfo["mouse"]["genome_assembly"] = "Q20973075"
speciesInfo["mouse"]["genome_assembly_previous"] = "Q20973075"
speciesInfo["10090"]["taxid"] = "10090"
speciesInfo["10090"]["wdid"] = "Q83310"
speciesInfo["10090"]["name"] = "mouse"
speciesInfo["10090"]["release"] = "Q20973051"
speciesInfo["10090"]["genome_assembly"] = "Q20973075"
speciesInfo["10090"]["genome_assembly_previous"] = "Q20973075"

speciesInfo["rat"]["taxid"] = "10114"
speciesInfo["rat"]["wdid"] = "Q36396"
speciesInfo["rat"]["name"] = "rat"
speciesInfo["rat"]["release"] = "Q19296606"

if len(sys.argv) == 1:
    print("Please provide an ncbi gene ID")
    print("Example: python singleGeneBot.py 628")
    sys.exit()


logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
entrezWikidataIds = dict()
wdqQuery = "CLAIM[351]"
InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="351")
'''
Below a mapping is created between entrez gene ids and wikidata identifiers.
'''
for geneItem in InWikiData.wditems["props"]["351"]:
    entrezWikidataIds[str(geneItem[2])] = geneItem[0]

uniprotwikidataids = dict()
print('Getting all proteins with a uniprot ID in Wikidata...')
inwikidata = PBB_Core.WDItemList("CLAIM[352]", "352")
for proteinItem in inwikidata.wditems["props"]["352"]:
    uniprotwikidataids[str(proteinItem[2])] = proteinItem[0]
try:

    object=dict()
    object["entrezgene"] = str(sys.argv[1])
    # object["entrezgene"] = str(line.rstrip())
    if str(object["entrezgene"]) in entrezWikidataIds.keys():
        object["wdid"] = 'Q' + str(entrezWikidataIds[str(object["entrezgene"])])
    else:
        object["wdid"] = None

    tempvar = dict()
    tempvar["speciesInfo"] = speciesInfo
    object["logincreds"] = logincreds
    object["uniprotwikidataids"] = uniprotwikidataids
    object["speciesInfo"] = tempvar["speciesInfo"]
    object["start"] = start
    geneClass = gene.mammal_gene(object)
    print(geneClass.wdid)
except:
      print("except")
      print(traceback.format_exc())
      pass