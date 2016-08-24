__author__ = 'andra'

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import traceback

from SPARQLWrapper import SPARQLWrapper, JSON

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
counter = 0
sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
sparql.setQuery("""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>
PREFIX q: <http://www.wikidata.org/prop/qualifier/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?item WHERE {
   ?item wdt:P686 ?go .
   ?item wdt:P351 ?entrez .
 }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results["results"]["bindings"]:
  try:
        counter = counter + 1
        print(result["gene"]["value"])
        gene = result["gene"]["value"].replace("http://www.wikidata.org/entity/", "")
        data2add = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P688')]
        wdPage = PBB_Core.WDItemEngine(gene, data=data2add, server="www.wikidata.org",
                                           domain="genes")
        wdPage.write(logincreds)

  except Exception as e:
      print(traceback.format_exc())
print(counter)
