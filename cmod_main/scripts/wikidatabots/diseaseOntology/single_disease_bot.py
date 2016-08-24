__author__ = 'andra'

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
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import PBB_settings
import xml.etree.cElementTree as ET
import requests

# Resource specific
import DiseaseOntology
import DiseaseOntology_settings
import time
import pprint
try:
    import simplejson as json
except ImportError as e:
    import json

import traceback

start = time.time()
if len(sys.argv) == 1:
    print("Please provide an Disease Ontology ID")
    print("Example: python single_disease_bot.py 628")
    sys.exit()

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
content = ET.fromstring(requests.get(DiseaseOntology_settings.getdoUrl()).text)
doDate =  content.findall('.//oboInOwl:date', DiseaseOntology_settings.getDoNameSpaces())
doversion = content.findall('.//owl:versionIRI', DiseaseOntology_settings.getDoNameSpaces())
dateList = doDate[0].text.split(' ')[0].split(":")
searchTerm = "Disease ontology release "+dateList[2]+"-"+dateList[1]+"-"+dateList[0]

url = 'https://www.wikidata.org/w/api.php'
params = {
        'action': 'wbsearchentities',
        'format' : 'json' ,
        'language' : 'en',
        'type' : 'item',
        'search': searchTerm
    }
data = requests.get(url, params=params)
reply = json.loads(data.text, "utf-8")
if len(reply['search']) == 0:
    sys.exit("A new version of DO has been release, a full update is required")
else:
    doVersionID = reply['search'][0]['id']

doWikiData_id = dict()
DoInWikiData = PBB_Core.WDItemList("CLAIM[699]", "699")

for doClass in content.findall('.//owl:Class', DiseaseOntology_settings.getDoNameSpaces()):
          try:
              do_id = doClass.findall('.//oboInOwl:id', DiseaseOntology_settings.getDoNameSpaces())[0].text
              if do_id == sys.argv[1]:
                  disVars = []
                  disVars.append(doClass)
                  disVars.append(doVersionID)
                  disVars.append(doWikiData_id)
                  disVars.append(logincreds)
                  disVars.append(start)
                  diseaseClass = DiseaseOntology.disease(disVars)
                  print(sys.argv[1])

          except Exception as e:
              pass
