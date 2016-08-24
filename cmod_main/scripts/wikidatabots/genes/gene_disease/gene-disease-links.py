#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
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
'''

__author__ = 'Justin Leong, Andra Waagmeester'
__license__ = 'GPL'

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import requests
import copy
import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
from time import gmtime, strftime

# This bot extends gene items in Wikidata with gene disease relationship information from the OMIM-sourced
# downloadable dump in Phenocarta. Currently, the bot writes to the genes specified in the source code, 
# and uses the genetic association property with references.

# Get Wikidata Ids for all entrez genes in Wikidata.
ncbi_gene_wikidata_ids = dict()
print("Getting all terms with a Disease Ontology ID in WikiData (WDQ)")
wdqQuery = "CLAIM[351]"
ncbi_gene_in_wikidata = PBB_Core.WDItemList(wdqQuery, wdprop="351")
for geneItem in ncbi_gene_in_wikidata.wditems["props"]["351"]:
            ncbi_gene_wikidata_ids[str(geneItem[2])] = geneItem[0]

gnsym_gemma_ids = dict() # maps gene symbols to Gemma/Phenocarta-specific gene IDs, for reference URLs

# Retrieve gene-disease relationships from Phenocarta.
source =  "http://www.chibi.ubc.ca/Gemma/phenocarta/LatestEvidenceExport/AnnotationsByDataset/OMIM.tsv"
result = requests.get(source, stream=True)
for line in result.iter_lines():
    # First separate each tuple into distinct fields.
    values = dict()
    s = str(line)
    fields = s.split("\\t")
    if "#" not in fields[0]:
        values["Gene NCBI"] = fields[1]
        values["Gene Symbol"] = fields[2]
        values["Taxon"] = fields[3]
        values["Phenotype Names"] = fields[4]
        values["Relationship"] = fields[5]
        values["Phenotype URIs"] = fields[6]
        values["Pubmeds"] = fields[7]
        values["Web Link"] = fields[8]
        if (values["Gene Symbol"] == "NPHP4"):
            if str(values["Gene NCBI"]) in ncbi_gene_wikidata_ids.keys():
                print("Gene ID in Wikidata...")
                values["gene_wdid"] = 'Q' + str(ncbi_gene_wikidata_ids[str(values["Gene NCBI"])])
                print(values["gene_wdid"])
                doid = fields[6].split("_")[1]
                sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
            # Retrieve Wikidata item from DO ID.
                sparql.setQuery("""

                    PREFIX wd: <http://www.wikidata.org/entity/> 
                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>

                    SELECT * WHERE {
                        ?diseases wdt:P699 "DOID:""" + doid + """\"
                    }

                """)
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()

                disease_wdid = results['results']['bindings'][0]['diseases']['value'].split("/")[4]
                if results['results']['bindings'][0]['diseases']['value']:
                    login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), os.environ['wikidataApi'])
                    if not (values["Gene Symbol"] in gnsym_gemma_ids):
                        gemmaGeneIds =  "http://sandbox.chibi.ubc.ca/Gemma/rest/phenotype/find-candidate-genes?phenotypeValueUris="+values["Phenotype URIs"]
                        result = requests.get(gemmaGeneIds, stream=True).json()
                        for item in result:
                            gnsym_gemma_ids[item['officialSymbol']] = item['id']
                    
                    refURL = PBB_Core.WDUrl(value='http://chibi.ubc.ca/Gemma/phenotypes.html?phenotypeUrlId=DOID_'+doid+'&geneId='+str(gnsym_gemma_ids[values["Gene Symbol"]]), prop_nr='P854', is_reference=True)
                    refURL2 = PBB_Core.WDUrl(value=values["Web Link"], prop_nr='P854', is_reference=True)
                    refImported = PBB_Core.WDItemID(value='Q22330995', prop_nr='P143', is_reference=True)
                    refImported.overwrite_references = True
                    refStated = PBB_Core.WDItemID(value='Q22978334', prop_nr='P248', is_reference=True)
                    timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                    refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
                    refRetrieved.overwrite_references = True
                    gnasscn_reference = [[refURL, refURL2, refStated, refImported, refRetrieved]]                    
                    value = PBB_Core.WDItemID(value=disease_wdid, prop_nr="P2293", references=gnasscn_reference)

                # Get a pointer to the Wikidata page on the gene under scrutiny
                    wd_gene_page = PBB_Core.WDItemEngine(wd_item_id=values["gene_wdid"], data=[value], server="www.wikidata.org", domain="genes")
                    wd_json_representation = wd_gene_page.get_wd_json_representation()
                    #pprint.pprint(wd_json_representation)
                    #wd_json_representation2 = refURL.json_representation
                    wd_gene_page.write(login)
                else:
                    print("Disease " + values["Phenotype Names"] + " for gene " + values["Gene Symbol"] + " not found in Wikidata.")
            else:
                print("Gene " + values["Gene Symbol"] + " not found in Wikidata.")

