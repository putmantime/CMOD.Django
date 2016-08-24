__author__ = 'andra'

import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF, RDFS
import sys
import requests
graph = rdflib.Graph()

ubUrl = requests.get("http://purl.obolibrary.org/obo/uberon.owl")
print("ja")
graph.parse(data=ubUrl.text, format="application/rdf+xml")
print(len(graph))
print(list(graph)[:10])
cls = URIRef("http://www.w3.org/2002/07/owl#Class")
subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
for uberon in graph.subjects(RDF.type, cls):
    print(uberon)
    print(graph.label(URIRef(uberon)))
    for bla in graph.objects(URIRef(uberon), subcls):
        print(bla)
        print("======")

