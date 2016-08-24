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
import PBB_Core
import PBB_Debug
import PBB_login
import PBB_settings
import requests
import traceback
import copy
import sys
import mygene_info_settings
from time import gmtime, strftime
import time
import pprint

try:
    import simplejson as json
except ImportError as e:
    import json
import humanprotein

if len(sys.argv) == 1:
    print("Please provide an Uniprot ID")
    print("Example: python singleGeneBot.py P12345")
    sys.exit()

start = time.time()
logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
uniprotwikidataids = dict()
genesymbolwdmapping = dict()

print('Getting all proteins with a uniprot ID in Wikidata...')
inwikidata = PBB_Core.WDItemList("CLAIM[703:5] AND CLAIM[352]", "352")
for proteinItem in inwikidata.wditems["props"]["352"]:
    uniprotwikidataids[str(proteinItem[2])] = proteinItem[0]

print("Getting all human proteins in Wikidata...")
gene_symbol_mapping = PBB_Core.WDItemList("CLAIM[353] AND CLAIM[703:5]", "353")
for genesymbol in gene_symbol_mapping.wditems["props"]["353"]:
    genesymbolwdmapping[str(genesymbol[2])] = genesymbol[0]

try:
    up = str(sys.argv[1])
    '''
    Get protein annotations from Uniprot
    '''
    r = requests.get(
        "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+%3funiprot+%3fplabel+%3fecName+%3fupversion+%0d%0a+++++++(group_concat(distinct+%3fencodedBy%3b+separator%3d%22%3b+%22)+as+%3fencoded_by)%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09VALUES+%3funiprot+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f" +
        up +
        "%3e%7d%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.+%0d%0a+++++++OPTIONAL+%7b%3funiprot+up%3aencodedBy+%3fgene+.%0d%0a%09++++%3fgene+skos%3aprefLabel+%3fencodedBy+.%7d%0d%0a++++++++optional%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++%3fupAlias+up%3aecName+%3fecName+.%7d%0d%0a++++++++%0d%0a++++++++OPTIONAL%7b+%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++%7b%3fupAlias+up%3afullName+%3falias+.%7d+UNION%0d%0a++++++++%7b%3fupAlias+up%3ashortName+%3falias+.%7d%7d%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3fupAlias+%3funiprot+%3fencodedBy+%3fplabel+%3fecName+%3fupversion&format=srj")

    protein = r.json()
    if len(protein["results"]["bindings"])==0:
        raise Exception("Communication error on " + up)

    '''
    Get go annotations from Uniprot
    '''
    r2 = requests.get(
        "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e+%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e+%0d%0aSELECT+DISTINCT+%3fprotein+%3fgo+%3fgoLabel+%3fparentLabel%0d%0aWHERE%0d%0a%7b%0d%0a++%09%09VALUES+%3fprotein+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f" +
        str(up) +
        "%3e%7d%0d%0a%09%09%3fprotein+a+up%3aProtein+.%0d%0a++%09%09%3fprotein+up%3aclassifiedWith+%3fgo+.+++%0d%0a++++++++%3fgo+rdfs%3alabel+%3fgoLabel+.%0d%0a++++++++%3fgo+rdfs%3asubClassOf*+%3fparent+.%0d%0a++++++++%3fparent+rdfs%3alabel+%3fparentLabel+.%0d%0a++++++++optional+%7b%3fparent+rdfs%3asubClassOf+%3fgrandParent+.%7d%0d%0a++++++++FILTER+(!bound(%3fgrandParent))%0d%0a%7d&format=srj")

    print('Getting all human genes with a ncbi gene ID in Wikidata...')
    entrezWikidataIds = dict()
    wdqQuery = "CLAIM[703:5] AND CLAIM[351]"

    InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="351")
    '''
    Below a mapping is created between entrez gene ids and wikidata identifiers.
    '''
    for geneItem in InWikiData.wditems["props"]["351"]:
        entrezWikidataIds[str(geneItem[2])] = geneItem[0]
    go_terms = r2.json()
    protein["goTerms"] = go_terms
    protein["logincreds"] = logincreds
    protein["id"] = up
    protein["start"] = start
    protein["geneSymbols"] = genesymbolwdmapping
    protein["entrezWikidataIds"] = entrezWikidataIds
    protein_class = humanprotein.HumanProtein(protein)

except Exception as e:
    print(traceback.format_exc())
    PBB_Core.WDItemEngine.log('ERROR',
                                          '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                                              main_data_id=up,
                                              exception_type=type(e),
                                              message=e.__str__(),
                                              wd_id='-',
                                              duration=time.time() - start
                                          ))
