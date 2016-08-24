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

# This bot extends gene items in Wikidata with gene-disease relationship information from the GWAS Catalog-sourced
# downloadable dump from Phenocarta. Currently, the bot attempts to write to all genes contained in the dump file, 
# and uses the genetic association property with references.

# Get Wikidata IDs for all Entrez genes in Wikidata.
ncbi_gene_wikidata_ids = dict()
print("Retrieving all terms with a Disease Ontology ID in Wikidata (WDQ)")
wdqQuery = "CLAIM[351]"
ncbi_gene_in_wikidata = PBB_Core.WDItemList(wdqQuery, wdprop="351")
for geneItem in ncbi_gene_in_wikidata.wditems["props"]["351"]:
            ncbi_gene_wikidata_ids[str(geneItem[2])] = geneItem[0]

gnsym_gemma_ids = dict() # maps gene symbols to Gemma/Phenocarta-specific gene IDs, for reference URLs

# Retrieve gene-disease relationships from Phenocarta.
source =  "http://www.chibi.ubc.ca/Gemma/phenocarta/LatestEvidenceExport/AnnotationsByDataset/GWAS_Catalog.tsv"
result = requests.get(source, stream=True)
lineNum = 0;
for line in result.iter_lines():
    lineNum += 1
    # Separating each tuple into distinct fields.
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
        # Current gene from dump exists in Wikidata
        #if (values["Gene Symbol"] == "APOL2"):
        if str(values["Gene NCBI"]) in ncbi_gene_wikidata_ids.keys():
            print("Gene ID in Wikidata...")
            values["gene_wdid"] = 'Q' + str(ncbi_gene_wikidata_ids[str(values["Gene NCBI"])])
            print(values["gene_wdid"])
            doids = fields[6].split(";")                
            for doid_url in doids:
                print("starting new doid")
                print(doid_url)
                doid = doid_url.split("_")[1]
                print(doid)
                sparql = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
                # Retrieve Wikidata item from DO ID
                sparql.setQuery("""

                    PREFIX wd: <http://www.wikidata.org/entity/> 
                    PREFIX wdt: <http://www.wikidata.org/prop/direct/>

                    SELECT * WHERE {
                        ?diseases wdt:P699 "DOID:""" + doid + """\"
                    }

                """)
                sparql.setReturnFormat(JSON)
                results = sparql.query().convert()
                pprint.pprint(results)
                # The current Disease Ontology term exists in Wikidata
                if len(results['results']['bindings'])!=0:    
                    disease_wdid = results['results']['bindings'][0]['diseases']['value'].split("/")[4]
                    if results['results']['bindings'][0]['diseases']['value']:
                        login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword()) # put back in when using Jenkins: os.environ['wikidataApi']
                        # Only hit the API endpoint if we do not already have the gene symbol to Gemma ID mapping
                        if not (values["Gene Symbol"] in gnsym_gemma_ids):
                            gemmaGeneIds =  "http://sandbox.chibi.ubc.ca/Gemma/rest/phenotype/find-candidate-genes?phenotypeValueUris="+doid_url
                            result = requests.get(gemmaGeneIds, stream=True).json()
                            for item in result:
                                gnsym_gemma_ids[item['officialSymbol']] = item['id']
                        # not doing for now, until duplicate detection exists (for using qual)
                        # writing diseases to genes
                        refURL = PBB_Core.WDUrl(value='http://chibi.ubc.ca/Gemma/phenotypes.html?phenotypeUrlId=DOID_'+doid+'&geneId='+str(gnsym_gemma_ids[values["Gene Symbol"]]), prop_nr='P854', is_reference=True)
                        refURL2 = PBB_Core.WDUrl(value=values["Web Link"], prop_nr='P854', is_reference=True)
                        refImported = PBB_Core.WDItemID(value='Q22330995', prop_nr='P143', is_reference=True)
                        refImported.overwrite_references = True
                        refStated = PBB_Core.WDItemID(value='Q22978334', prop_nr='P248', is_reference=True)
                        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
                        refRetrieved.overwrite_references = True
                        gnasscn_reference = [[refURL, refURL2, refStated, refImported, refRetrieved]]    
                        qualifier = PBB_Core.WDItemID(value='Q1098876', prop_nr='P459', is_qualifier=True)                
                        value = PBB_Core.WDItemID(value=disease_wdid, prop_nr="P2293", references=gnasscn_reference, qualifiers=[qualifier], check_qualifier_equality=False)    
                        # Get a pointer to the Wikidata page on the gene under scrutiny
                        wd_gene_page = PBB_Core.WDItemEngine(wd_item_id=values["gene_wdid"], data=[value], server="www.wikidata.org", domain="genes", append_value=['P2293'])
                        wd_gene_page.log('INFO', 'line ' + str(lineNum) + ' ' + values["Gene Symbol"] + ' ' + values["Phenotype Names"] + ' ' + wd_gene_page.write(login))
                        
                        # writing genes to diseases
                        refURL = PBB_Core.WDUrl(value='http://chibi.ubc.ca/Gemma/phenotypes.html?phenotypeUrlId=DOID_'+doid+'&geneId='+str(gnsym_gemma_ids[values["Gene Symbol"]]), prop_nr='P854', is_reference=True)
                        refURL2 = PBB_Core.WDUrl(value=values["Web Link"], prop_nr='P854', is_reference=True)
                        refImported = PBB_Core.WDItemID(value='Q22330995', prop_nr='P143', is_reference=True)
                        refImported.overwrite_references = True
                        refStated = PBB_Core.WDItemID(value='Q22978334', prop_nr='P248', is_reference=True)
                        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
                        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
                        refRetrieved.overwrite_references = True
                        gnasscn_reference = [[refURL, refURL2, refStated, refImported, refRetrieved]]    
                        qualifier = PBB_Core.WDItemID(value='Q1098876', prop_nr='P459', is_qualifier=True)                
                        value = PBB_Core.WDItemID(value=values["gene_wdid"], prop_nr="P2293", references=gnasscn_reference, qualifiers=[qualifier], check_qualifier_equality=False)    
                        # Get a pointer to the Wikidata page on the disease under scrutiny
                        wd_dis_page = PBB_Core.WDItemEngine(wd_item_id=disease_wdid, data=[value], server="www.wikidata.org", domain="genes", append_value=['P2293'])
                        wd_dis_page.log('INFO', 'line ' + str(lineNum) + ' ' + values["Gene Symbol"] + ' ' + values["Phenotype Names"] + ' ' + wd_dis_page.write(login))                        
                    else:
                        print("Disease " + values["Phenotype Names"] + " for gene " + values["Gene Symbol"] + " not found in Wikidata.")
                        PBB_Core.WDItemEngine.log('WARNING', 'line ' + str(lineNum) + ' ' + values["Phenotype Names"] + " for gene " + values["Gene Symbol"] + " not found in Wikidata.")
                else:
                    print("Disease " + values["Phenotype Names"] + " for gene " + values["Gene Symbol"] + " not found in Wikidata.")
                    PBB_Core.WDItemEngine.log('WARNING', 'line ' + str(lineNum) + ' ' + values["Phenotype Names"] + " for gene " + values["Gene Symbol"] + " not found in Wikidata.")                            
        else:
            print("Gene " + values["Gene Symbol"] + " not found in Wikidata.")
            PBB_Core.WDItemEngine.log('WARNING', 'line ' + str(lineNum) + ' ' + values["Gene Symbol"] + " not found in Wikidata.")
