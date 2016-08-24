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


def search_wd(search_term):
    url = 'https://{}/w/api.php'.format("www.wikidata.org")
    params = {
        'action': 'wbsearchentities',
        'language': 'en',
        'search': search_term,
        'format': 'json'
    }
    reply = requests.get(url, params=params)
    return reply.json()


class MouseProteome():
    def __init__(self):
        self.start = time.time()
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        uniprotwikidataids = dict()
        genesymbolwdmapping = dict()

        print('Getting all proteins with a uniprot ID in Wikidata...')
        inwikidata = PBB_Core.WDItemList("CLAIM[703:83310] AND CLAIM[352]", "352")
        for proteinItem in inwikidata.wditems["props"]["352"]:
            uniprotwikidataids[str(proteinItem[2])] = proteinItem[0]

        print('Getting all mouse genes with a ncbi gene ID in Wikidata...')
        entrezWikidataIds = dict()
        print("wdq 1")
        wdqQuery = "CLAIM[703:83310] AND CLAIM[351]"
        InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="351")

        '''
        Below a mapping is created between entrez gene ids and wikidata identifiers.
        '''
        for geneItem in InWikiData.wditems["props"]["351"]:
            entrezWikidataIds[str(geneItem[2])] = geneItem[0]

        print("Getting all mouse proteins from Uniprot...")
        r0 = requests.get("http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e+%0d%0aPREFIX+taxonomy%3a+%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+xsd%3a+%3chttp%3a%2f%2fwww.w3.org%2f2001%2fXMLSchema%23%3e%0d%0aSELECT+DISTINCT+*%0d%0aWHERE%0d%0a%7b%0d%0a%09%09%3fprotein+a+up%3aProtein+.%0d%0a++++++++%3fprotein+up%3areviewed+%22true%22%5e%5exsd%3aboolean+.%0d%0a++%09%09%3fprotein+rdfs%3alabel+%3fprotein_label+.%0d%0a++++++++%3fprotein+up%3aorganism+taxonomy%3a10090+.%0d%0a%7d&format=srj")
        prot_results = r0.json()
        uniprot_ids = []
        for protein in prot_results["results"]["bindings"]:
            item = dict()
            item["id"] = protein["protein"]["value"].replace("http://purl.uniprot.org/uniprot/", "")
            item["label"] = protein["protein_label"]["value"]
            uniprot_ids.append(item)



        for up in uniprot_ids:
            try:
                #if up["id"] not in uniprotwikidataids:
                    '''
                    Get protein annotations from Uniprot
                    '''
                    #r = requests.get(
                    #    "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+%3funiprot+%3fplabel+%3fecName+%3fupversion+%0d%0a+++++++(group_concat(distinct+%3fencodedBy%3b+separator%3d%22%3b+%22)+as+%3fencoded_by)%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09VALUES+%3funiprot+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f" +
                    #    str(up["id"]) +
                    #    "%3e%7d%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.+%0d%0a++++++++%3funiprot+up%3aencodedBy+%3fgene+.%0d%0a%09%09%3fgene+skos%3aprefLabel+%3fencodedBy+.%0d%0a++++++++optional%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++%3fupAlias+up%3aecName+%3fecName+.%7d%0d%0a++++++++%0d%0a++++++++OPTIONAL%7b+%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++%7b%3fupAlias+up%3afullName+%3falias+.%7d+UNION%0d%0a++++++++%7b%3fupAlias+up%3ashortName+%3falias+.%7d%7d%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3fupAlias+%3funiprot+%3fencodedBy+%3fplabel+%3fecName+%3fupversion&format=srj")

                    r = requests.get(
                        "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+DISTINCT+%3funiprot+%3fplabel+%3fecName+%3fupversion+%0d%0a+++++++(group_concat(distinct+%3fencodedBy%3b+separator%3d%22%3b+%22)+as+%3fencoded_by)%0d%0a+++++++(group_concat(distinct+%3fncbiGene%3b+separator%3d%22%3b+%22)+as+%3fgene_id)%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09VALUES+%3funiprot+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f" +
                        str(up["id"]) +
                        "%3e%7d%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.+%0d%0a++++++++%3funiprot+up%3aencodedBy+%3fgene+.%0d%0a%09%09%3fgene+skos%3aprefLabel+%3fencodedBy+.%0d%0a++++++++optional%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++%3fupAlias+up%3aecName+%3fecName+.%7d%0d%0a++++++++optional%7b%3funiprot+rdfs%3aseeAlso+%3fncbiGene+.%0d%0a+++++++++++++++++%3fncbiGene+up%3adatabase+database%3aGeneID+.%7d%0d%0a++++++++%0d%0a++++++++OPTIONAL%7b+%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++%7b%3fupAlias+up%3afullName+%3falias+.%7d+UNION%0d%0a++++++++%7b%3fupAlias+up%3ashortName+%3falias+.%7d%7d%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3fupAlias+%3funiprot+%3fencodedBy+%3fncbiGene+%3fplabel+%3fecName+%3fupversion&format=srj")

                    protein = r.json()
                    if len(protein["results"]["bindings"])==0:
                        raise Exception("Communication error on " + up["id"])
                    #if "results" not in protein.keys():

                    """
                    '''
                    Get go annotations from Uniprot
                    '''
                    r2 = requests.get(
                        "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e+%0d%0aPREFIX+skos%3a%3chttp%3a%2f%2fwww.w3.org%2f2004%2f02%2fskos%2fcore%23%3e+%0d%0aSELECT+DISTINCT+%3fprotein+%3fgo+%3fgoLabel+%3fparentLabel%0d%0aWHERE%0d%0a%7b%0d%0a++%09%09VALUES+%3fprotein+%7b%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f" +
                        str(up["id"]) +
                        "%3e%7d%0d%0a%09%09%3fprotein+a+up%3aProtein+.%0d%0a++%09%09%3fprotein+up%3aclassifiedWith+%3fgo+.+++%0d%0a++++++++%3fgo+rdfs%3alabel+%3fgoLabel+.%0d%0a++++++++%3fgo+rdfs%3asubClassOf*+%3fparent+.%0d%0a++++++++%3fparent+rdfs%3alabel+%3fparentLabel+.%0d%0a++++++++optional+%7b%3fparent+rdfs%3asubClassOf+%3fgrandParent+.%7d%0d%0a++++++++FILTER+(!bound(%3fgrandParent))%0d%0a%7d&format=srj")
                    go_terms = r2.json()

                    protein["goTerms"] = go_terms
                    """
                    protein["logincreds"] = self.logincreds
                    # protein["label"] = up["label"]
                    protein["id"] = up["id"]
                    protein["start"] = self.start
                    protein["geneSymbols"] = genesymbolwdmapping
                    protein["entrezWikidataIds"] = entrezWikidataIds
                    protein_class = MouseProtein(protein)
                #else:
                    #print(up["id"]+" already covered in wikidata")

            except Exception as e:
                print(traceback.format_exc())
                PBB_Core.WDItemEngine.log('ERROR',
                                          '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                                              main_data_id=up["id"],
                                              exception_type=type(e),
                                              message=e.__str__(),
                                              wd_id='-',
                                              duration=time.time() - self.start
                                          ))


class MouseProtein(object):
    def __init__(self, object):
        # Populate variables with different values
        self.geneSymbols = object["geneSymbols"]
        self.logincreds = object["logincreds"]
        # self.goTerms = object["goTerms"]
        self.version = object["results"]["bindings"][0]["upversion"]["value"]
        self.uniprot = object["results"]["bindings"][0]["uniprot"]["value"]
        self.uniprotId = object["id"]
        self.name = object["results"]["bindings"][0]["plabel"]["value"]
        self.start = object["start"]
        self.entrezWikidataIds = object["entrezWikidataIds"]


        up_in_wd = search_wd(self.name)
        self.wdid = None
        hits = []
        for result in up_in_wd["search"]:
            if result["match"]["text"] == up_in_wd["searchinfo"]["search"]:
                hits.append(result)
                print(result["match"]["text"])
        if len(hits) > 0:
            valid = []
            for hit in hits:
                hitPage = PBB_Core.WDItemEngine(item_name=hit["label"],
                                                wd_item_id=hit["id"], data=[],
                                                server="www.wikidata.org", domain="proteins")
                json_rep = hitPage.get_wd_json_representation()
                proteinClaim = False
                geneClaim = False
                speciesClaim = False
                if "P279" in json_rep["claims"].keys():
                    for it in json_rep["claims"]["P279"]:
                        if it["mainsnak"]["datavalue"]["value"]["numeric-id"] == 8054:
                            proteinClaim = True
                            break
                        if it["mainsnak"]["datavalue"]["value"]["numeric-id"] == 7187:
                            geneClaim = True
                            break
                        if it["mainsnak"]["datavalue"]["value"]["numeric-id"] == 407355:
                            proteinClaim = True
                            break
                if "P31" in json_rep["claims"].keys():
                    for it in json_rep["claims"]["P31"]:
                        if it["mainsnak"]["datavalue"]["value"]["numeric-id"] == 8047:
                            proteinClaim = True
                            break
                        if it["mainsnak"]["datavalue"]["value"]["numeric-id"] == 8054:
                            proteinClaim = True
                            break
                if "P703" in json_rep["claims"].keys():
                    for it in json_rep["claims"]["P703"]:
                        if it["mainsnak"]["datavalue"]["value"]["numeric-id"] == 83310:
                            speciesClaim = True
                            break

                if len(json_rep["claims"]) == 0:
                    raise Exception(hit["id"] + " has an indentical label as " + self.uniprotId + ", but with no claims")
                elif not speciesClaim:
                    self.wdid = None
                elif "P352" in json_rep["claims"].keys() or "P705" in json_rep["claims"].keys() or proteinClaim:
                    valid.append(hit["id"])
                elif geneClaim:
                    self.wdid = None
                else:
                    raise Exception(hit["id"] + " has an identical label as " + self.uniprotId + " but with no valid protein claims")
            if len(valid) == 1:
                self.wdid = valid[0]
            elif len(valid)>1:
                raise Exception(
                    self.uniprotId + " There are multiple valid Wikidata items that might be applicable. " + str(valid))

        if "gene_id" in object["results"]["bindings"][0].keys():
            self.gene_id = []
            for geneId in object["results"]["bindings"][0]["gene_id"]["value"].split(";"):
                if geneId != "":
                    self.gene_id.append(geneId)

        if "ecName" in object["results"]["bindings"][0].keys():
            self.ecname = []
            self.ecname.append(object["results"]["bindings"][0]["ecName"]["value"])
        self.alias = []
        for syn in object["results"]["bindings"][0]["upalias"]["value"].split(";"):
            if syn != "":
                self.alias.append(syn)
        if "pdbid" in object["results"]["bindings"][0].keys() and object["results"]["bindings"][0]["pdbid"][
            "value"] != "":
            self.pdb = []
            for pdbId in object["results"]["bindings"][0]["pdbid"]["value"].split(";"):
                self.pdb.append(pdbId.replace("http://rdf.wwpdb.org/pdb/", "").replace(" ", ""))
        if "refseq" in object["results"]["bindings"][0].keys():
            self.refseq = []
            for refseqId in object["results"]["bindings"][0]["refseqid"]["value"].split(";"):
                self.refseq.append(refseqId.replace("http://purl.uniprot.org/refseq/", "").replace(" ", ""))
        if "ensemblp" in object["results"]["bindings"][0].keys() and object["results"]["bindings"][0]["ensemblp"][
            "value"] != "":
            self.ensemblp = []
            for ensP in object["results"]["bindings"][0]["ensemblp"]["value"].split(";"):
                self.ensemblp.append(ensP.replace("http://purl.uniprot.org/ensembl/", "").replace(" ", ""))

        # Prepare references
        refStatedIn = PBB_Core.WDItemID(value=2629752, prop_nr='P248', is_reference=True)
        refStatedIn.overwrite_references = True
        refURL = "http://www.uniprot.org/uniprot/" + self.uniprotId + ".txt?version=" + str(self.version)
        refReferenceURL = PBB_Core.WDUrl(value=refURL, prop_nr='P854', is_reference=True)
        refReferenceURL.overwrite_references = True
        refImported = PBB_Core.WDItemID(value=905695, prop_nr='P143', is_reference=True)
        refImported.overwrite_references = True
        timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
        refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
        refRetrieved.overwrite_references = True
        protein_reference = [[refStatedIn, refImported, refRetrieved, refReferenceURL]]

        references = dict()
        proteinPrep = dict()
        genePrep = dict()

        # P279 = subclass of
        proteinPrep['P279'] = [PBB_Core.WDItemID(value="Q8054", prop_nr='P279', references=protein_reference)]

        # P703 = found in taxon
        proteinPrep['P703'] = [PBB_Core.WDItemID(value="Q83310", prop_nr='P703', references=protein_reference)]

        # P352 = UniprotID
        proteinPrep['P352'] = [PBB_Core.WDString(value=self.uniprotId, prop_nr='P352', references=protein_reference)]

        # P591 = EC number
        if "ecname" in vars(self):
            proteinPrep['P591'] = []
            for i in range(len(self.ecname)):
                proteinPrep['P591'].append(
                    PBB_Core.WDString(value=self.ecname[i], prop_nr='P591', references=protein_reference))

        # P638 = PDBID
        if "pdb" in vars(self) and len(self.pdb) > 0:
            proteinPrep['P638'] = []
            for i in range(len(self.pdb)):
                proteinPrep['P638'].append(
                    PBB_Core.WDString(value=self.pdb[i], prop_nr='P638', references=protein_reference))

        # P637 = Refseq Protein ID
        if "refseq" in vars(self) and len(self.refseq) > 0:
            proteinPrep['P637'] = []
            for i in range(len(self.refseq)):
                proteinPrep['P637'].append(
                    PBB_Core.WDString(value=self.refseq[i], prop_nr='P637', references=protein_reference))

        # P705 = Ensembl Protein ID
        if "ensemblp" in vars(self) and len(self.ensemblp) > 0:
            proteinPrep['P705'] = []
            for i in range(len(self.ensemblp)):
                proteinPrep['P705'].append(
                    PBB_Core.WDString(value=self.ensemblp[i], prop_nr='P705', references=protein_reference))
        """
        # P686 = Gene Ontology ID
        proteinPrep["P680"] = []
        proteinPrep["P681"] = []
        proteinPrep["P682"] = []

        for result in self.goTerms["results"]["bindings"]:
            # proteinPrep['P686'].append(PBB_Core.WDString(value=result["go"]["value"].replace("'http://purl.obolibrary.org/obo/'", "").replace("_", ":"), prop_nr='P686', references=protein_reference))
            url = 'https://{}/w/api.php'.format("www.wikidata.org")
            params = {
                'action': 'wbsearchentities',
                'language': 'en',
                'search': result["goLabel"]["value"],
                'format': 'json'
            }

            reply = requests.get(url, params=params)
            search_results = reply.json()
            go_id = result["go"]["value"].replace("http://purl.obolibrary.org/obo/GO_", "GO:")

            goTermExists = False
            termIndex = -1
            for searchresult in search_results["search"]:
                if searchresult["label"] == search_results["searchinfo"]["search"] and go_id in self.goWikidataIds.keys():
                    goTermExists = True
                    termIndex = termIndex + 1
                    break

            if (len(search_results["search"]) == 0) or not goTermExists:
                statement = [
                    PBB_Core.WDString(value=result["go"]["value"].replace("http://purl.obolibrary.org/obo/GO_", "GO:"),
                                      prop_nr='P686', references=protein_reference)]
                goWdPage = PBB_Core.WDItemEngine(item_name=result["goLabel"]["value"], data=statement,
                                                 server="www.wikidata.org",
                                                 domain="proteins")
                goWdPage.set_description("Gene Ontology term")
                js = goWdPage.get_wd_json_representation()
                goWdId = goWdPage.write(self.logincreds)
            else:
                goWdId = search_results["search"][termIndex]["id"]

            if result["parentLabel"]["value"] == "molecular_function":
                exists = False
                for i in range(len(proteinPrep["P680"])):
                    if proteinPrep["P680"][i].value == goWdId:
                        exists = True
                if not exists:
                    proteinPrep["P680"].append(
                        PBB_Core.WDItemID(value=goWdId, prop_nr='P680', references=protein_reference))
            if result["parentLabel"]["value"] == "cellular_component":
                exists = False
                for i in range(len(proteinPrep["P681"])):
                    if proteinPrep["P681"][i].value == goWdId:
                        exists = True
                if not exists:
                    proteinPrep["P681"].append(
                        PBB_Core.WDItemID(value=goWdId, prop_nr='P681', references=protein_reference))
            if result["parentLabel"]["value"] == "biological_process":
                exists = False
                for i in range(len(proteinPrep["P682"])):
                    if proteinPrep["P682"][i].value == goWdId:
                        exists = True
                if not exists:
                    proteinPrep["P682"].append(
                        PBB_Core.WDItemID(value=goWdId, prop_nr='P682', references=protein_reference))

        """

        # P702 = Encoded by
        if "gene_id" in vars(self) and len(self.gene_id) > 0:
            proteinPrep['P702'] = []
            if len(self.gene_id) > 1:
                raise Exception(self.uniprot + "reports more then one gene encoding for this protein")
            else:
                proteinPrep['P702'].append(
                    PBB_Core.WDItemID(value=self.entrezWikidataIds[self.gene_id[0].replace("http://purl.uniprot.org/geneid/", "").replace(" ", "")], prop_nr='P702', references=protein_reference))

        proteinData2Add = []
        for key in proteinPrep.keys():
            for statement in proteinPrep[key]:
                proteinData2Add.append(statement)
                print(statement.prop_nr, statement.value)
        if self.wdid is None:
            wdProteinpage = PBB_Core.WDItemEngine(item_name=self.name, data=proteinData2Add, server="www.wikidata.org",
                                                domain="proteins", append_value=['P279'], use_sparql=True)
        else:
            wdProteinpage = PBB_Core.WDItemEngine(wd_item_id=self.wdid, item_name=self.name, data=proteinData2Add,
                                                  server="www.wikidata.org",
                                                  domain="proteins", append_value=['P279'], use_sparql=True)

        if len(self.alias) > 0:
            wdProteinpage.set_aliases(aliases=self.alias, lang='en', append=True)
        wdProteinpage.set_description(description='mouse protein', lang='en')
        self.wd_json_representation = wdProteinpage.get_wd_json_representation()
        PBB_Debug.prettyPrint(self.wd_json_representation)
        wdProteinpage.write(self.logincreds)
        print(wdProteinpage.wd_item_id)
        if not os.path.exists('./json_dumps'):
            os.makedirs('./json_dumps')
        f = open('./json_dumps/' + self.uniprotId + '.json', 'w+')
        pprint.pprint(self.wd_json_representation, stream=f)
        f.close()
        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=self.uniprotId,
            exception_type='',
            message=f.name,
            wd_id=self.wdid,
            duration=time.time() - self.start
        ))
        print("===============")




