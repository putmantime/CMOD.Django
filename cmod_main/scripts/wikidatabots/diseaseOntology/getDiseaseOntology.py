
import urllib2
import simplejson
import json


import xml.etree.ElementTree as ET
from datetime import date, timedelta
import pprint
import sys
import pywikibot
from pywikibot.data import api
import ProteinBoxBotFunctions
import ProteinBoxBotKnowledge

def getItems(site, itemtitle):
  params = { 'action' :'wbsearchentities' , 'format' : 'json' , 'language' : 'en', 'type' : 'item', 'search': itemtitle}
  request = api.Request(site=site,**params)
  return request.submit()
 
successLog = open('Diseases_succesfullyAdded.log', 'w')
    
# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()

pp = pprint.PrettyPrinter(indent=4)
namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

dourl = 'http://purl.obolibrary.org/obo/doid.owl'
request = urllib2.Request(dourl)
u = urllib2.urlopen(request)
do = u.read()

# pp.pprint(do)
print "start"
root = ET.fromstring(do)

doDate =  root.findall('.//oboInOwl:date', namespaces)
doversion = root.findall('.//owl:versionIRI', namespaces)
for name, value in doversion[0].items():
            doUrlversion = value

print "doUrl: "+doUrlversion
dateList = doDate[0].text.split(' ')[0].split(":")
print dateList[2]+"-"+dateList[1]+"-"+dateList[0]

searchTerm = "Disease ontology release "+dateList[2]+"-"+dateList[1]+"-"+dateList[0]

if len(getItems(site, searchTerm)['search']) == 0:
        metadata={   u'entity': {   }}
        metadata["entity"]["claims"]=dict()
        token = repo.token(pywikibot.Page(repo, searchTerm), 'edit')
        metadata = ProteinBoxBotFunctions.addLabel(metadata, searchTerm)
        metadata = ProteinBoxBotFunctions.addClaims(metadata, 'P856', ["http://disease-ontology.org"], 'string') # official website P856
        metadata = ProteinBoxBotFunctions.addClaims(metadata, 'P1065', ["http://purl.obolibrary.org/obo/doid/releases/"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"/doid.owl"], 'string') # archive URL P1065
        request = api.Request(site=site,
                              action='wbeditentity',
                              format='json',
                              new='item',
                              bot=True,
                              token=token,
                              data=json.dumps(metadata['entity']))
        data = request.submit()
        ID = data['entity']['id']
        print ID

for diseaseClass in root.findall('.//owl:Class', namespaces):
    if len(diseaseClass.findall('.//owl:deprecated', namespaces))>0:
            continue
    doid = diseaseClass.findall('.//oboInOwl:id', namespaces)[0].text
    diseaseLabels = diseaseClass.findall('.//rdfs:label', namespaces)
    diseaseWdIDs = []
    diseaseLabelsText = []
    diseaseSynonymsText = []
    for diseaseLabel in diseaseLabels:
        token = repo.token(pywikibot.Page(repo, diseaseLabel.text), 'edit')
        localdata={   u'entity': {   },
            u'success': 1}
        diseaseLabelsText.append(diseaseLabel.text.encode('ascii', 'replace'))
        wikidata = getItems(site, diseaseLabel.text.rstrip())
        # pp.pprint(wikidata)
        for result in wikidata["search"]:
                  if "label" in result.keys():
                    if wikidata["searchinfo"]["search"].capitalize() == result["label"] :
                      diseaseWdIDs.append(result["id"])
                    if wikidata["searchinfo"]["search"] == result["label"] :
                      diseaseWdIDs.append(result["id"])
    diseaseSynonyms = diseaseClass.findall('.//oboInOwl:hasExactSynonym', namespaces)
    for diseaseSynonym in diseaseSynonyms:
        diseaseSynonymsText.append(diseaseSynonym.text.encode('ascii', 'replace'))
        wikidata = getItems(site, diseaseSynonym.text.rstrip())
        for result in wikidata["search"]:
            if isinstance(result, dict):
                  if "label" in result.keys():
                    if wikidata["searchinfo"]["search"].capitalize() == result["label"] :
                      diseaseWdIDs.append(result["id"])
                    if wikidata["searchinfo"]["search"] == result["label"] :
                      diseaseWdIDs.append(result["id"])  
    
    externalReferences = diseaseClass.findall('.//oboInOwl:hasDbXref', namespaces)
    xrefs = dict()
    for externalReference in externalReferences:
        if not externalReference.text.split(":")[0] in xrefs:
            xrefs[externalReference.text.split(":")[0]] = []
        xrefs[externalReference.text.split(":")[0]].append(externalReference.text.split(":")[1])
        
    sys.stdout.write(doid+"\t") 
    if len(diseaseWdIDs)>0:
        sys.stdout.write(", ".join(set(diseaseWdIDs))+"\t")
        # print " # ".join(diseaseLabelsText)
    else:
        sys.stdout.write("new Item\t")
        # print " # ".join(diseaseLabelsText)
        localdata = ProteinBoxBotFunctions.addLabel(localdata, diseaseLabelsText[0])
        localdata = ProteinBoxBotFunctions.addAliases(localdata, "", diseaseSynonymsText)
        localdata["entity"]["claims"] = dict()
        localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P279', [12136], 'wikibase-entityid') # subclass of (P279) disease
        localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P699', [doid], 'string') # Disease ontology ID (P699)
        if "Orphanet" in xrefs.keys():
            localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P1550', xrefs["Orphanet"], 'string') # Orphanet ID (P1550)
        if "ICD10CM" in xrefs.keys():
            localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P494', xrefs["ICD10CM"], 'string') # ICD-10 ID (P494)
        if "ICD9CM" in xrefs.keys():
            localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P493', xrefs["ICD9CM"], 'string') # ICD-9 ID (P493)
        if "MSH" in xrefs.keys():
            localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P486', xrefs["MSH"], 'string') # MeSH ID (P486)
        if "NCI" in xrefs.keys():
            localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P1395', xrefs["NCI"], 'string') # National Cancer Institute ID (P1395) 
        if "OMIM" in xrefs.keys():
            localdata = ProteinBoxBotFunctions.addClaims(localdata, 'P492', xrefs["OMIM"], 'string') # National Cancer Institute ID (P1395)       
            
        localdata.pop("success", None)
        
        request = api.Request(site=site,
                              action='wbeditentity',
                              format='json',
                              new='item',
                              bot=True,
                              token=token,
                              data=json.dumps(localdata['entity']))
        data = request.submit()
        ID = data['entity']['id']
        print ID
        successLog.write(doid+'\t'+ID+'\n')
