__author__ = 'andra'

# This is maintenance bot and merges all occurances where 2 items exit on Wikidata
# where the uniprot_id, the ensemblP, pdb, refseqp and species = Human are identical
# It is a first fix for issue 56: https://bitbucket.org/sulab/wikidatabots/issues/56/multiple-duplicates-of-human-proteins

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

SELECT DISTINCT ?protein ?protein2 {
?protein wdt:P279 wd:Q8054 ;
         wdt:P352 ?uniprot ;
         wdt:P680 ?mf ;
         wdt:P681 ?cc ;
         wdt:P682 ?bp ;
         wdt:P703 wd:Q5 .
?protein2 wdt:P279 wd:Q8054 ;
         wdt:P352 ?uniprot ;
         wdt:P680 ?mf ;
         wdt:P681 ?cc ;
         wdt:P682 ?bp ;
          wdt:P703 wd:Q5 .
FILTER (?protein != ?protein2)
                   }
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# pprint.pprint(results)
processed = []
counter = 0
for result in results["results"]["bindings"]:
  try:
    if result["protein"]["value"] not in processed and result["protein2"]["value"]:
        counter = counter + 1
        print(result["protein"]["value"],  result["protein2"]["value"])
        protein1 = result["protein"]["value"].replace("http://www.wikidata.org/entity/", "")
        protein2 = result["protein2"]["value"].replace("http://www.wikidata.org/entity/", "")
        if int(protein1[1:]) > int(protein2[1:]):
            mergefrom = protein1
            mergeto = protein2
        else:
            mergefrom = protein2
            mergeto = protein1

        processed.append(result["protein"]["value"])
        processed.append(result["protein2"]["value"])

        PBB_Core.WDItemEngine.merge_items(mergefrom, mergeto , logincreds)
  except Exception as e:
      print(traceback.format_exc())
print(counter)