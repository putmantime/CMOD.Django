__author__ = 'andra'
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core
import PBB_Debug
from time import gmtime, strftime
import rdflib
from rdflib import URIRef
from rdflib.namespace import RDF, RDFS
import traceback
import requests
import copy

class Uberon():
    def __init__(self):
        self.start = time.time()
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        # Get all WikiData entries that contain a WikiData ID
        print("Getting all terms with a Uberon ID in WikiData")
        ubWikiData_id = dict()
        ubInWikiData = PBB_Core.WDItemList("CLAIM[1554]", "1554")
        for uberonItem in ubInWikiData.wditems["props"]["1554"]:
           ubWikiData_id[str(uberonItem[2])]=uberonItem[0] # diseaseItem[2] = Uberon identifier, diseaseItem[0] = Uberon identifier
        graph = rdflib.Graph()

        ubUrl = requests.get("http://purl.obolibrary.org/obo/uberon.owl")

        print("ja")
        graph.parse(data=ubUrl.text, format="application/rdf+xml")

        cls = URIRef("http://www.w3.org/2002/07/owl#Class")
        subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
        for uberonuri in graph.subjects(RDF.type, cls):
            try:
                uberonVars = dict()
                uberonVars["uberon"] = uberonuri
                uberonVars["uberonLabel"] = graph.label(URIRef(uberonuri))
                uberonVars["wikidata_id"] = ubWikiData_id
                uberonVars["logincreds"] = self.logincreds
                uberonVars["start"] = self.start
                uberonVars["graph"] = graph
                if "UBERON" in uberonuri:
                    uberonClass = uberonTerm(uberonVars)

            except Exception as e:
                print(traceback.format_exc())
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=uberonuri,
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='-',
                        duration=time.time() - self.start
                    ))


class uberonTerm(object):
    def __init__(self, object):
            self.logincreds = object["logincreds"]
            self.name = object["uberonLabel"]
            self.uberon = object["uberon"]
            self.uberon_id = self.uberon.replace("http://purl.obolibrary.org/obo/UBERON_", "")
            self.wikidata_id = object["wikidata_id"]
            self.start = object["start"]
            self.graph = object["graph"]

            subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
            id = URIRef("http://www.geneontology.org/formats/oboInOwl#id")
            hasExactSyn = URIRef("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym")
            print(self.uberon_id)
            print(self.name)

            refStatedIn = PBB_Core.WDItemID(21552738, prop_nr='P248', is_reference=True)
            refStatedIn.overwrite_references = True
            refImported = PBB_Core.WDItemID(value=7876491, prop_nr='P143', is_reference=True)
            refImported.overwrite_references = True
            timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
            refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
            refRetrieved.overwrite_references = True
            ub_reference = [refStatedIn, refImported, refRetrieved]


            if self.uberon_id in self.wikidata_id.keys():
                self.wdid = self.wikidata_id[self.uberon_id.replace("UBERON:", "")]
            else:
                self.wdid = None

            self.synonyms = []
            for synonym in self.graph.objects(URIRef(self.uberon), hasExactSyn):
                self.synonyms.append(str(synonym))

            prep = dict()
            prep["P279"] = [PBB_Core.WDItemID(value='Q4936952', prop_nr='P279', references=[copy.deepcopy(ub_reference)])]
            prep["P1554"] = [PBB_Core.WDString(value=self.uberon_id, prop_nr='P1554', references=[copy.deepcopy(ub_reference)])]
            print(self.uberon)
            prep["P1709"] = [PBB_Core.WDUrl(value=self.uberon, prop_nr='P1709', references=[copy.deepcopy(ub_reference)])]

            data2add = []
            for key in prep.keys():
                for statement in prep[key]:
                    data2add.append(statement)
                    print(statement.prop_nr, statement.value)

            if self.wdid is not None:
                wdPage = PBB_Core.WDItemEngine(self.wdid, item_name=self.name, data=data2add, server="www.wikidata.org", domain="anatomical_structure",append_value=['P279'])
            else:
                wdPage = PBB_Core.WDItemEngine(item_name=self.name, data=data2add, server="www.wikidata.org", domain="anatomical_structure", append_value=['P279'])
            if len(self.synonyms) >0:
                wdPage.set_aliases(aliases=self.synonyms, lang='en', append=True)
            print(self.synonyms)
            for syn in self.synonyms:
                print(syn)
            wdPage.write(self.logincreds)
            print("======")
            sys.exit()