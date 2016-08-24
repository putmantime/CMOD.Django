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

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import PBB_login
import PBB_settings
from SPARQLWrapper import SPARQLWrapper, JSON
import json
import pprint
import traceback

human_genes_query = '''
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX p: <http://www.wikidata.org/prop/>
    PREFIX v: <http://www.wikidata.org/prop/statement/>
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX reference: <http://www.wikidata.org/prop/reference/>
    SELECT DISTINCT ?gene WHERE {
       ?gene wdt:P279 wd:Q7187 .
       ?gene p:P351 ?ncbigeneId .
       ?gene wdt:P703 wd:Q5 .
    }
'''
sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
sparql.setQuery(human_genes_query)
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
for result in results["results"]["bindings"]:
 try:
    gene = result["gene"]["value"].replace("http://www.wikidata.org/entity/", "")
    print("gene: "+gene)
    # pprint.pprint(result["gene"]["value"].replace("http://www.wikidata.org/entity/", ""))
    genePage = PBB_Core.WDItemEngine(gene, server="www.wikidata.org", domain="genes")
    geneJson = genePage.get_wd_json_representation()
    # pprint.pprint(geneJson["sitelinks"])
    if "P688" in geneJson["claims"].keys():
      for item in geneJson["claims"]["P688"]:
        protein = 'Q'+str(item["mainsnak"]["datavalue"]["value"]["numeric-id"])
        proteinPage = PBB_Core.WDItemEngine(protein, server="www.wikidata.org", domain="proteins")
        proteinJson = proteinPage.get_wd_json_representation()
        if len(proteinJson["sitelinks"].keys()) > 0 and "enwiki" not in proteinJson["sitelinks"].keys():
            pprint.pprint(proteinJson["sitelinks"])
            need2write = False
            for sitelink in proteinJson["sitelinks"].keys():
                genePage.set_sitelink(site=sitelink, title=proteinJson["sitelinks"][sitelink]["title"], badges=proteinJson["sitelinks"][sitelink]["badges"])
                proteinPage.set_sitelink(site=sitelink, title='')
                need2write = True

            if need2write:
                proteinPage.write(logincreds)
                genePage.write(logincreds)
                print("JAJAJAJAJA")


            print("Protein: "+ protein)
            print(geneJson)
    # sys.exit()
 except:
     print(traceback.format_exc())
     pass


