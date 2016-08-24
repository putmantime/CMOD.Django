#!usr/bin/env python
# -*- coding: utf-8 -*-

"""
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
"""

__author__ = 'Andra Waagmeester'
__license__ = 'GPL'

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")

from SPARQLWrapper import SPARQLWrapper, JSON
import pprint

sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
sparql.setQuery("""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wikibase: <http://wikiba.se/ontology#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>
PREFIX q: <http://www.wikidata.org/prop/qualifier/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT DISTINCT ?item ?item2 WHERE {
   ?item wdt:P637 ?id .
   ?item2 wdt:P637 ?id .
   FILTER (?item != ?item2)
 }
""")

sparql.setReturnFormat(JSON)
results = sparql.query().convert()
url = 'https://{}/w/api.php'.format("www.wikidata.org")
# pprint.pprint(results)
temp = []
teller = 0
for result in results['results']['bindings']:

    '''
    params = {
        'action': 'wbmergeitems',
        'fromid': 'en',
        'toid': search_term,
        'bot': 'true'
    }
    reply = requests.get(url, params=params)
    return reply.json()
    '''
    if result["item"]["value"] not in temp:
        print(result["item"]["value"], result["item2"]["value"])
        temp.append(result["item"]["value"])
        temp.append(result["item2"]["value"])
        teller = teller + 1

print(teller)