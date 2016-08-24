__author__ = 'andra'

from SPARQLWrapper import SPARQLWrapper, JSON
import requests
import xml.etree.cElementTree as ET
import pprint
import time

def getDoValue(doClass, doNode):
    namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
    return doClass.findall(doNode, namespaces)

doWikiDataIds = []
doids = []
sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
sparql.setQuery("""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX statement: <http://www.wikidata.org/prop/statement/>

SELECT DISTINCT ?do WHERE {
   VALUES ?rank { wikibase:DeprecatedRank wikibase:NormalRank }
   ?diseases p:P699 ?doid .
   ?doid statement:P699 ?do .
   ?doid wikibase:rank ?rank .
}
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()
for result in results["results"]["bindings"]:
    # print(result["uniprotId"]["value"])
    doWikiDataIds.append(result["do"]["value"].strip())
    # print(result["do"]["value"])


r = requests.get("http://purl.obolibrary.org/obo/doid.owl")
docontent = ET.fromstring(r.text)
namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

for doClass in docontent.findall('.//owl:Class', namespaces):
    doid = getDoValue(doClass, './/oboInOwl:id')[0].text
    if doid.strip not in doWikiDataIds:
        doids.append(doid.replace('\'', '').strip())
sdoids = set(sorted(doids))
sdoInWikidata = set(sorted(doWikiDataIds))
missing = set(doids).difference(set(doWikiDataIds))

for item in missing:
    print(item)

print(len(missing))



