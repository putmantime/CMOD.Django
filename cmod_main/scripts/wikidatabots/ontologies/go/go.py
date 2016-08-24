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

class go():
    def __init__(self):
        self.start = time.time()
        self.logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
        # Get all WikiData entries that contain a WikiData ID
        print("Getting all terms with a Gene Ontology ID in WikiData")
        goWikiData_id = dict()
        goInWikiData = PBB_Core.WDItemList("CLAIM[686]", "686")
        for goItem in goInWikiData.wditems["props"]["686"]:
           goWikiData_id[str(goItem[2])]=goItem[0] # diseaseItem[2] = go identifier, diseaseItem[0] = go identifier
        print(len(goWikiData_id.keys()))
        sys.exit()
        graph = rdflib.Graph()

        goUrl = requests.get("http://purl.obolibrary.org/obo/go.owl")

        print("ja")
        graph.parse(data=goUrl.text, format="application/rdf+xml")

        cls = URIRef("http://www.w3.org/2002/07/owl#Class")
        subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
        counter = 0
        for gouri in graph.subjects(RDF.type, cls):
            try:
                counter = counter + 1
                print(counter)
                goVars = dict()
                goVars["uri"] = gouri
                goVars["label"] = graph.label(URIRef(gouri))
                goVars["wikidata_id"] = goWikiData_id
                goVars["logincreds"] = self.logincreds
                goVars["start"] = self.start
                goVars["graph"] = graph
                if "GO" in gouri:
                    goClass = goTerm(goVars)

            except Exception as e:
                print(traceback.format_exc())
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=gouri,
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='-',
                        duration=time.time() - self.start
                    ))


class goTerm(object):
    def __init__(self, object):
            self.logincreds = object["logincreds"]
            self.name = object["label"]
            self.go = object["uri"]
            self.go_id = self.go.replace("http://purl.obolibrary.org/obo/GO_", "")
            self.wikidata_id = object["wikidata_id"]
            self.start = object["start"]
            self.graph = object["graph"]

            subcls = URIRef("http://www.w3.org/2000/01/rdf-schema#subClassOf")
            id = URIRef("http://www.geneontology.org/formats/oboInOwl#id")
            hasExactSyn = URIRef("http://www.geneontology.org/formats/oboInOwl#hasExactSynonym")
            print(self.go_id)
            print(self.name)

            refStatedIn = PBB_Core.WDItemID(21552738, prop_nr='P248', is_reference=True) # TODO FIX automatic generation of version item in Wikidata
            refStatedIn.overwrite_references = True
            refImported = PBB_Core.WDItemID(value=135085, prop_nr='P143', is_reference=True)
            refImported.overwrite_references = True
            timeStringNow = strftime("+%Y-%m-%dT00:00:00Z", gmtime())
            refRetrieved = PBB_Core.WDTime(timeStringNow, prop_nr='P813', is_reference=True)
            refRetrieved.overwrite_references = True
            go_reference = [refStatedIn, refImported, refRetrieved]


            if self.go_id in self.wikidata_id.keys():
                self.wdid = self.wikidata_id[self.go_id]
            else:
                self.wdid = None

            self.synonyms = []
            for synonym in self.graph.objects(URIRef(self.go), hasExactSyn):
                self.synonyms.append(str(synonym))

            prep = dict()
            prep["P279"] = [PBB_Core.WDItemID(value='Q4936952', prop_nr='P279', references=[copy.deepcopy(go_reference)])]
            prep["P1554"] = [PBB_Core.WDString(value=self.go_id, prop_nr='P1554', references=[copy.deepcopy(go_reference)])]
            print(self.go)
            prep["P1709"] = [PBB_Core.WDUrl(value=self.go, prop_nr='P1709', references=[copy.deepcopy(go_reference)])]

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
            # wdPage.write(self.logincreds)
            print("======")
