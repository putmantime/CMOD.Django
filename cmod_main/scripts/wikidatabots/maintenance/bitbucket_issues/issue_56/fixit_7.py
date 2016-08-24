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

SELECT ?gene ?uniprot ?protein_aff ?total WHERE {
  {
  SELECT distinct ?uniprot (count(?uniprot) as ?total) WHERE {
    ?gene wdt:P703 wd:Q5 ;
          wdt:P279 wd:Q7187 ;
          wdt:P688 ?protein .
    ?protein wdt:P352 ?uniprot ;
             wdt:P279 wd:Q8054 ;
             wdt:P703 wd:Q5 .
    }
    Group BY ?uniprot
  }

  ?protein_aff wdt:P352 ?uniprot .
  ?gene wdt:P688 ?protein_aff ;
        wdt:P703 wd:Q5 .

  FILTER (?total > 1)
 }
 ORDER BY ?gene
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# pprint.pprint(results)
counter = 0
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