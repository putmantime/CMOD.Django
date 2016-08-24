import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ProteinBoxBot_Core")
import PBB_Core
import requests
from SPARQLWrapper import SPARQLWrapper, JSON
import pprint


__author__ = 'andra'


uniprotWikiDataIds = []
sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
sparql.setQuery("""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX reference: <http://www.wikidata.org/prop/reference/>
SELECT DISTINCT ?uniprotId WHERE {
  ?protein wdt:P279 wd:Q8054 .
  ?protein wdt:P352 ?uniprotId .
  ?protein wdt:P703 wd:Q5 .
  ?protein p:P702 ?encBy .
  ?encBy prov:wasDerivedFrom ?derivedFrom .
  ?derivedFrom reference:P248 wd:Q2629752  .
}""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results["results"]["bindings"]:
    # print(result["uniprotId"]["value"])
    uniprotWikiDataIds.append(result["uniprotId"]["value"])
# pprint.pprint(uniprotWikiDataIds)

r = requests.get("http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+taxonomy%3a+%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0a++++PREFIX+xsd%3a+%3chttp%3a%2f%2fwww.w3.org%2f2001%2fXMLSchema%23%3e%0d%0a++++SELECT+DISTINCT+*%0d%0a++++WHERE%0d%0a++++%7b%0d%0a%09%09%3fprotein+a+up%3aProtein+.%0d%0a++++++++%3fprotein+up%3areviewed+%22true%22%5e%5exsd%3aboolean+.%0d%0a++%09%09%3fprotein+rdfs%3alabel+%3fprotein_label+.%0d%0a++++++++%3fprotein+up%3aorganism+taxonomy%3a9606+.%0d%0a++++%7d&format=srj")
prot_results = r.json()
uniprot_ids = []
f = open('./rerun.log', 'w')

for protein in prot_results["results"]["bindings"]:
      item = dict()
      item["id"] = protein["protein"]["value"].replace("http://purl.uniprot.org/uniprot/", "")
      item["label"] = protein["protein_label"]["value"]
      if item["id"] not in uniprotWikiDataIds:
          uniprot_ids.append(item["id"])
          f.write(item["id"]+"\n")
print(len(uniprot_ids))
f.close()

