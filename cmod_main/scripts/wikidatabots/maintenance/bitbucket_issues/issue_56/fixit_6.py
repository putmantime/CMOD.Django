__author__ = 'andra'

# This is a maintenance bot which removes all occurences where a protein is incorrectly being encoded by another protein

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

SELECT DISTINCT ?protein {
?protein wdt:P702 ?otherprotein .
?otherprotein wdt:P279 wd:Q8054 .
}
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# pprint.pprint(results)
counter = 0
for result in results["results"]["bindings"]:
  try:
        counter = counter + 1
        print(result["protein"]["value"])
        protein = result["protein"]["value"].replace("http://www.wikidata.org/entity/", "")
        data2add = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P702')]
        wdPage = PBB_Core.WDItemEngine(protein, data=data2add, server="www.wikidata.org",
                                           domain="proteins")
        wdPage.write(logincreds)

  except Exception as e:
      print(traceback.format_exc())
print(counter)