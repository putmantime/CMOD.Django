import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../ProteinBoxBot_Core")
import PBB_Core
import mygene_info_settings
import requests


__author__ = 'andra'

r = requests.get(mygene_info_settings.getGenesUrl().format("human"))
ncbi_genes = r.json()

ncbiGeneWikidataIds = dict()
wdqQuery = "CLAIM[703:5] AND CLAIM[351]"
InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="351")
'''
Below a mapping is created between entrez gene ids and wikidata identifiers.
'''
for geneItem in InWikiData.wditems["props"]["351"]:
    ncbiGeneWikidataIds[str(geneItem[2])] = geneItem[0]
counter = 0
for gene in ncbi_genes["hits"]:
    if str(gene["entrezgene"]) not in ncbiGeneWikidataIds.keys():
        print("warning: missing in wikidata: "+ '\t'+str(gene["entrezgene"]) + '\t'+ gene["name"])
    else:
        print("info: "+ '\t'+str(gene["entrezgene"]) + '\t'+ gene["name"]+"\texists in wikidata:")


