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
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?wditem ?label WHERE {
   ?wditem wdt:P351 ?entrez .
   ?wditem skos:altLabel ?label .
   filter (regex(str(?label), "^entrez:", "i"))
}
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results["results"]["bindings"]:
  try:
        counter = counter + 1
        print(result["wditem"]["value"])
        wditem = result["wditem"]["value"].replace("http://www.wikidata.org/entity/", "")

        wdPage = PBB_Core.WDItemEngine(wditem, server="www.wikidata.org", domain="gene")
        aliases = wdPage.get_aliases()
        clean_aliases = []
        for alias in aliases:
            if not 'entrez:' in alias["value"]:
                clean_aliases.append(alias["value"])
        wdPage.set_aliases(clean_aliases, append=False)
        wdPage.write(logincreds)

  except Exception as e:
      print(traceback.format_exc())
print(counter)