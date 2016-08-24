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

import re
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import PBB_settings
import copy
from time import gmtime, strftime


class orthologClass(object):
    def __init__(self, object):
        self.logincreds = object["logincreds"]
        self.source = object["source"]
        self.ortholog = object["ortholog"]
        self.species = object["speciesWdID"]
        
        # Prepare references
        refStatedInHomologeneBuild = PBB_Core.WDItemID(value='Q20976936', prop_nr='P248', is_reference=True)
        refImportedFromHomologen = PBB_Core.WDItemID(value='Q468215', prop_nr='P143', is_reference=True)

        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        
        homologene_reference =  [[refStatedInHomologeneBuild, refImportedFromHomologen, refRetrieved]]
        
        # Prepare qualifiers
        humanQualifier = PBB_Core.WDItemID(value='Q5', prop_nr='P703', is_qualifier=True)
        mouseQualifier = PBB_Core.WDItemID(value='Q83310', prop_nr='P703', is_qualifier=True)    

        # Prepare the items to add
        if self.species == "Q5":
            orthologValue = PBB_Core.WDItemID(value=self.ortholog, prop_nr='P684', references=homologene_reference, qualifiers=[humanQualifier])
        elif self.species == "Q83310":
            orthologValue = PBB_Core.WDItemID(value=self.ortholog, prop_nr='P684', references=homologene_reference, qualifiers=[mouseQualifier])
                 
        wdPage = PBB_Core.WDItemEngine(wd_item_id=self.source, data=[orthologValue], server="www.wikidata.org", domain="genes")
        print(wdPage.wd_json_representation)
        wdPage.write(self.logincreds)

        

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

humanEntrezWikidataIds = dict()
mouseEntrezWikidataIds = dict()

print("Getting all human genes in Wikidata")
InWikiData = PBB_Core.WDItemList("CLAIM[703:5] AND CLAIM[351]", "351")
for geneItem in InWikiData.wditems["props"]["351"]:
    humanEntrezWikidataIds[str(geneItem[2])] = geneItem[0]

print("Getting all mouse genes in Wikidata")
InWikiData = PBB_Core.WDItemList("CLAIM[703:83310] AND CLAIM[351]", "351")
for geneItem in InWikiData.wditems["props"]["351"]:
    mouseEntrezWikidataIds[str(geneItem[2])] = geneItem[0]
    
homologene = open("/tmp/homologene.data", "r")
humanOrthologs = dict()
mouseOrthologs = dict()

for line in homologene:
    for line in homologene:
        fields = line.split('\t')
        if fields[1]=="9606":
            humanOrthologs[fields[0]] = fields[2]
        if fields[1]=="10090":
            mouseOrthologs[fields[0]] = fields[2]

for ortholog in humanOrthologs.keys():
  try:
    if ortholog in mouseOrthologs.keys():
        if ((humanOrthologs[ortholog] in humanEntrezWikidataIds.keys()) and
           (mouseOrthologs[ortholog] in mouseEntrezWikidataIds.keys())) :
            print("{} \t {} \tQ{}) \t {} \tQ{}".format(ortholog, humanOrthologs[ortholog], humanEntrezWikidataIds[humanOrthologs[ortholog]], 
                                                mouseOrthologs[ortholog], mouseEntrezWikidataIds[mouseOrthologs[ortholog]]))
            humanOrtholog = dict()
            mouseOrtholog = dict()
            humanOrtholog["logincreds"] = logincreds
            mouseOrtholog["logincreds"] = logincreds
            humanOrtholog["ortholog"] = "Q"+str(humanEntrezWikidataIds[humanOrthologs[ortholog]])
            humanOrtholog["speciesWdID"] = "Q5"
            humanOrtholog["source"] = "Q"+str(mouseEntrezWikidataIds[mouseOrthologs[ortholog]])
            HumanOrthoLogClass = orthologClass(humanOrtholog)
            mouseOrtholog["ortholog"] = "Q"+str(mouseEntrezWikidataIds[mouseOrthologs[ortholog]])
            mouseOrtholog["speciesWdID"] = "Q83310"
            mouseOrtholog["source"] = "Q"+str(humanEntrezWikidataIds[humanOrthologs[ortholog]]) 
            MouseOrthoLogClass = orthologClass(mouseOrtholog)
  except Exception as e:
              PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id='',
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='-',
                        duration=""
                    ))


