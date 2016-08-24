__author__ = 'andra'


import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import pprint
import traceback

from SPARQLWrapper import SPARQLWrapper, JSON

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
sparql.setQuery("""
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>

SELECT distinct * WHERE {
  ?goItem1 wdt:P686 ?go1 .
  ?goItem2 wdt:P686 ?go1 .
  FILTER (?goItem1 != ?goItem2)
  }
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# pprint.pprint(results)
processed = []
counter = 0
for result in results["results"]["bindings"]:
  try:
    if result["goItem1"]["value"] not in processed and result["goItem2"]["value"]:
        counter = counter + 1
        print(result["goItem1"]["value"],  result["goItem2"]["value"])
        goItem1 = result["goItem1"]["value"].replace("http://www.wikidata.org/entity/", "")
        goItem2 = result["goItem2"]["value"].replace("http://www.wikidata.org/entity/", "")
        if int(goItem1[1:]) > int(goItem2[1:]):
            mergefrom = goItem1
            mergeto = goItem2
        else:
            mergefrom = goItem2
            mergeto = goItem1

        processed.append(result["goItem1"]["value"])
        processed.append(result["goItem2"]["value"])

        PBB_Core.WDItemEngine.merge_items(mergefrom, mergeto , logincreds)
  except Exception as e:
      print(traceback.format_exc())
print(counter)