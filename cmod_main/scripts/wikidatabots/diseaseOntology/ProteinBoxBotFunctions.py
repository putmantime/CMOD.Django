#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Author:Andra Waagmeester (andra@waagmeester.net)

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

# Import the required libraries
import urllib2
import simplejson
import json
# -*- coding: utf-8  -*-
import pywikibot
import pprint
from pywikibot.data import api
import sys
import traceback
import time
import datetime
import xml.etree.ElementTree as ET
import ProteinBoxBotKnowledge
from raven import Client

namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}

# Define the funcitons.
globalDiseaseOntology = None
globalWikidataID = ""
globalSite = None

def prettyPrint(variable):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(variable)

def getClaims(site, wdItem, claimProperty):
    params = {
    			'action' :'wbgetclaims' ,
                'entity' : wdItem.getID(),
    			'property': claimProperty,
             }
    request = api.Request(site=site,**params)
    return request.submit()
   
def countClaims(site, wdItem, claimProperty):
    data = getClaims(site, wdItem, claimProperty)
    return len(data["claims"][claimProperty])

def claimExists(site, wdItem, claimProperty, claimValue):
    data = getClaims(site, wdItem, claimProperty)
    if len(data["claims"]) > 0:
      for claim in data["claims"][claimProperty]:
        if isinstance(claimValue, basestring):
          if str(claim['mainsnak']['datavalue']['value']) == str(claimValue):
            return True
        if isinstance(claimValue, pywikibot.page.ItemPage):
          if str(claim['mainsnak']['datavalue']['value']['numeric-id']) == str(claimValue.getID())[1:]:
            return True
      return False # end for loop
    else: return False # len(data["claims"]) == 0

def getItems(site, itemtitle):
  params = { 'action' :'wbsearchentities' , 'format' : 'json' , 'language' : 'en', 'type' : 'item', 'search': itemtitle}
  request = api.Request(site=site,**params)
  return request.submit()
	
def countItems(site, itemtitle):
   data = getItems(site, itemtitle)
   finalResult = 0
   for item in data['search']:
       if (itemtitle == item['label']):
           finalResult = finalResult + 1
   return finalResult
   
def itemExists(site, itemtitle):
    itemFound = False
    if countItems(site, itemtitle) > 0:
        itemFound = True
    return itemFound 
      
def getWDProperties(site, wdItem):
    params = {'action':'wbgetclaims', 'entity':wdItem}
    request = api.Request(site=site,**params)
    data = request.submit()
    return data['claims']
    
def getWDProperty(site, wdItem, wdProperty):
    params = {'action':'wbgetclaims', 'entity':wdItem, 'property':wdProperty}
    request = api.Request(site=site,**params)
    data = request.submit()
    return data['claims']
    
def countWDProperties(site, wdItem):
    return len(getWDProperties(site, wdItem))  
    
def hasProperty(site, wdItem, wdProperty):
    if getWDProperty(site, wdItem, wdProperty) == []:
        return False
    elif len(getWDProperty(site, wdItem, wdProperty)[wdProperty]) == 1:
        return True
    else: 
        return False     
        
def setAlias(site, repo, item, itemLabel, alias):
    token = repo.token(pywikibot.Page(repo, itemLabel), 'edit')
    params = {'action':'wbsetaliases', 'language':'en', 'id':item, 'set':alias, 'bot':True, 'token':token}
    request = api.Request(site=site,**params)
    data = request.submit()
    print data 
 

def createNewPage(site, token):
    params = {'action':'wbeditentity','format' : 'json', 'new':'item', 'data':'{}', 'bot':True, 'token':token}
    request = api.Request(site=site,**params)
    return request.submit()
    
def addLabel(localdata, label, wdid):
    englishLabel = dict()
    englishLabel['language']='en'
    englishLabel['value']=label
    englishLabels=dict()
    englishLabels['en']=englishLabel
    localdata['entities'][wdid]['labels']=englishLabels
    return localdata

def addNewLabel(localdata, label):
    englishLabel = dict()
    englishLabel['language']='en'
    englishLabel['value']=label
    englishLabels=dict()
    englishLabels['en']=englishLabel
    localdata['entities']['labels']=englishLabels
    return localdata

def addAliases(localdata, alias, otheraliases, wdid):
    aliases={'en':[]}
    if (otheraliases != "-"):
       otherAliases=otheraliases
       aliasesList = otherAliases
       for tempAlias in aliasesList:
         alias=dict()
         alias['language']='en'
         alias['value']=tempAlias
         aliases['en'].append(alias)
    localdata['entities'][wdid]['aliases']=aliases
    return localdata

def addClaims(localdata, property, values, datatype, wdid, obsolete): 
    localdata["entities"][wdid]["claims"][property] = []
    localvalues = []
    if isinstance(values, list): 
        localvalues = values
    else:
        localvalues.append(values)     
    for value in localvalues:
        statement = dict()
        if obsolete:
            statement["rank"]="deprecated"
        else:
            statement["rank"]="normal"
        statement["type"]="statement"
        mainsnak =dict()
        statement["mainsnak"]=mainsnak      
        # mainsnak["datatype"]=datatype 
        mainsnak['property']=property    
        mainsnak['datavalue']=dict()
        if datatype=='string':
            mainsnak['datavalue']['type']='string'
            mainsnak['datavalue']['value']=value
            mainsnak['snaktype']='value'
        elif datatype=='wikibase-entityid':
            mainsnak['datavalue']['type']='wikibase-entityid'
            mainsnak['datavalue']['value']=dict()
            mainsnak['datavalue']['value']['entity-type']='item'
            mainsnak['datavalue']['value']['numeric-id']=value
            mainsnak['snaktype']='value'
        mainsnak["type"]="statement"
        mainsnak["rank"]="normal"
        statement["references"]=[]
        statement["references"]=addReference(statement["references"], 'P143', 5282129)
        localdata["entities"][wdid]["claims"][property].append(statement)
    return localdata
    
    
    
def addNewClaims(localdata, property, values, datatype, stated=True):
    localdata["entities"]["claims"][property] = []
    localvalues = []
    if isinstance(values, list):
        localvalues = values
    else:
        localvalues.append(values)

    for value in localvalues:
        statement = dict()
        statement["rank"]="normal"
        statement["type"]="statement"
        mainsnak =dict()
        statement["mainsnak"]=mainsnak
        # mainsnak["datatype"]=datatype 
        mainsnak['property']=property
        mainsnak['datavalue']=dict()
        if datatype=='string':
            mainsnak['datavalue']['type']='string'
            mainsnak['datavalue']['value']=value
            mainsnak['snaktype']='value'
        elif datatype=='wikibase-entityid':
            mainsnak['datavalue']['type']='wikibase-entityid'
            mainsnak['datavalue']['value']=dict()
            mainsnak['datavalue']['value']['entity-type']='item'
            mainsnak['datavalue']['value']['numeric-id']=value
            mainsnak['snaktype']='value'
        mainsnak["type"]="statement"
        mainsnak["rank"]="normal"
        statement["references"]=[]
        statement["references"]=addReference(statement["references"], 'P143', 1345229, stated)
        localdata["entities"]["claims"][property].append(statement)
    return localdata

def updateClaim(claim, value, obsolete):
    if obsolete:
        claim["rank"]="deprecated"
    else:
        claim["rank"]="normal"
    claim["mainsnak"]["datavalue"]["value"]=value
    return claim
    

def addReference(references, property, itemId, stated=True):
    found = False
    for ref in references:
      if property in ref["snaks"]:
        for snak in ref["snaks"][property]:
          if snak["datavalue"]["value"]["numeric-id"]==itemId:
            ref = setDateRetrievedTimestamp(ref)
            found = True
            break
    if not found:    
        reference = dict()
        snaks = dict()
        reference["snaks"] = snaks
        snaks[property]=[]
        reference['snaks-order']=['P143']
        snak=dict()
        snaks[property].append(snak)
        snak['property']=property
        snak["snaktype"]='value'
        snak["datatype"]='wikibase-item'
        snak["datavalue"]=dict()
        snak["datavalue"]["type"]='wikibase-entityid'
        snak["datavalue"]["value"]=dict()
        snak["datavalue"]["value"]["entity-type"]='item'
        snak["datavalue"]["value"]["numeric-id"]=itemId
        reference = setDateRetrievedTimestamp(reference)
        if stated:
            reference = setStatedIn(reference)
        references.append(reference)
    return references    

def setDateRetrievedTimestamp(reference):
    ts = time.time()
    timestamp = datetime.datetime.fromtimestamp(ts).strftime('+0000000%Y-%m-%dT00:00:00Z')
    wdTimestamp = dict()
    reference["snaks-order"]=['P143', 'P813']                 
    wdTimestamp["datatype"]='time'
    wdTimestamp["property"]='P813'
    wdTimestamp["snaktype"]='value'
    wdTimestamp["datavalue"]=dict()
    wdTimestamp["datavalue"]["type"]='time'
    wdTimestamp["datavalue"]["value"]=dict()
    wdTimestamp["datavalue"]["value"]["after"]=0
    wdTimestamp["datavalue"]["value"]["before"]=0
    wdTimestamp["datavalue"]["value"]["calendarmodel"]='http://www.wikidata.org/entity/Q1985727'
    wdTimestamp["datavalue"]["value"]["precision"]=11
    wdTimestamp["datavalue"]["value"]["time"]=timestamp
    wdTimestamp["datavalue"]["value"]["timezone"]=0
    reference["snaks"]['P813']=[wdTimestamp]
    return reference
    
def setStatedIn(reference):
    doDate =  globalDiseaseOntology.findall('.//oboInOwl:date', namespaces)
    dateList = doDate[0].text.split(' ')[0].split(":")
    searchTerm = "Disease ontology release "+dateList[2]+"-"+dateList[1]+"-"+dateList[0]
    snak = dict()      
    snak["datatype"]='wikibase-item'
    snak["property"]='P248'
    snak["snaktype"]='value'
    snak["datavalue"]=dict()
    snak["datavalue"]["type"]='wikibase-entityid'
    snak["datavalue"]["value"]=dict()
    snak["datavalue"]["value"]["entity-type"]='item'
    searchResult = getItems(globalSite, searchTerm)['search'][0]["id"]
    snak["datavalue"]["value"]["numeric-id"]=int(searchResult[1:])
    print "gglobalWikidataID: "+globalWikidataID
    print "searchResult: "+searchResult
    if globalWikidataID != searchResult:
        reference["snaks-order"]=['P143', 'P248', 'P813']
        reference["snaks"]['P248']=[snak]
    return reference

def getItem(site, wdItem, token):
    request = api.Request(site=site,
                          action='wbgetentities',
                          format='json',
                          ids=wdItem)    
    return request.submit()

def getItemsByProperty(wdproperty):
    req = urllib2.Request("http://wdq.wmflabs.org/api?q=claim%5B"+wdproperty+"%5D&props="+wdproperty, None, {'user-agent':'proteinBoxBot'})
    opener = urllib2.build_opener()
    f = opener.open(req)
    return simplejson.load(f)
    
def updateDiseaseOntologyVersion(site, repo, diseaseOntology): 
    global globalDiseaseOntology
    globalDiseaseOntology = diseaseOntology  

    global globalSite
    globalSite = site
     
    doDate =  diseaseOntology.findall('.//oboInOwl:date', namespaces)
    doversion = diseaseOntology.findall('.//owl:versionIRI', namespaces)
    for name, value in doversion[0].items():
                doUrlversion = value
    dateList = doDate[0].text.split(' ')[0].split(":")
    searchTerm = "Disease ontology release "+dateList[2]+"-"+dateList[1]+"-"+dateList[0]

    if len(getItems(site, searchTerm)['search']) == 0:
            metadata={   u'entities': {   }}
            metadata["entities"]["claims"]=dict()
            token = repo.token(pywikibot.Page(repo, searchTerm), 'edit')
            metadata = addNewLabel(metadata, searchTerm)
            metadata = addNewClaims(metadata, 'P856', ["http://disease-ontology.org"], 'string', False) # official website P856
            metadata = addNewClaims(metadata, 'P1065', ["http://purl.obolibrary.org/obo/doid/releases/"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"/doid.owl"], 'string', False) # archive URL P1065
            request = api.Request(site=site,
                                  action='wbeditentity',
                                  format='json',
                                  new='item',
                                  bot=True,
                                  token=token,
                                  data=json.dumps(metadata['entities']))
            # pp.pprint(localdata)
            data = request.submit()
            # pp.pprint(data)
            ID = data['entity']['id']
            print "WikiData entry made for this version of Disease Ontology: "+ID
    
def createNewDOItemPage(site, repo, doValues, diseaseOntologyTimeStamp, obsolete):
    token = repo.token(pywikibot.Page(repo, doValues["labels"][0].strip()), 'edit')
    localdata=createNewPage(site, token)
    
    global globalWikidataID
    global globalSite
    globalSite = site
    globalWikidataID = localdata['entity']['id']
    prettyPrint(localdata)
    localdata['entities']=dict()
    localdata['entities'][globalWikidataID]=localdata.pop('entity')
    xrefs=doValues["xrefs"]
    prettyPrint(localdata) 
    localdata = addLabel(localdata, doValues["labels"][0].strip(), globalWikidataID)
    localdata = addAliases(localdata, "", doValues["synonyms"], globalWikidataID)
    localdata["entities"][globalWikidataID]["claims"] = dict()
    # add Disease ontology claim
    localdata = addClaims(localdata, 'P699', doValues["doid"][0].split(":")[1], 'string', globalWikidataID, obsolete) # Disease ontology ID (P699)
    if obsolete:
        localdata['entities'][globalWikidataID]['claims']['P699'][0]['rank']='deprecated'
    else:
        localdata['entities'][globalWikidataID]['claims']['P699'][0]['rank']='normal'
    if "Orphanet" in xrefs.keys():
        localdata = addClaims(localdata, 'P1550', xrefs["Orphanet"], 'string', globalWikidataID, obsolete) # Orphanet ID (P1550)
    if "ICD10CM" in xrefs.keys():
        localdata = addClaims(localdata, 'P494', xrefs["ICD10CM"], 'string', globalWikidataID, obsolete) # ICD-10 ID (P494)
    if "ICD9CM" in xrefs.keys():
        localdata = addClaims(localdata, 'P493', xrefs["ICD9CM"], 'string', globalWikidataID, obsolete) # ICD-9 ID (P493)
    if "MSH" in xrefs.keys():
        localdata = addClaims(localdata, 'P486', xrefs["MSH"], 'string', globalWikidataID, obsolete) # MeSH ID (P486)
    if "NCI" in xrefs.keys():
        localdata = addClaims(localdata, 'P1395', xrefs["NCI"], 'string', globalWikidataID, obsolete) # National Cancer Institute ID (P1395) 
    if "OMIM" in xrefs.keys():
        localdata = addClaims(localdata, 'P492', xrefs["OMIM"], 'string', globalWikidataID, obsolete) # National Cancer Institute ID (P1395)       
        
    localdata.pop("success", None)
        
    token = repo.token(pywikibot.Page(repo, doValues["labels"][0].strip()), 'edit')
    request = api.Request(site=site,
                          action='wbeditentity',
                          format='json',
                          id=globalWikidataID,
                          bot=True,
                          token=token,
                          data=json.dumps(localdata['entities'][globalWikidataID]))
    data = request.submit()

def updateDOWDItem(site, repo, wikidataID, doValues, diseaseOntologyTimeStamp, obsolete, diseaseOntology):
     # TODO: Timestamp DO, Label for token, Add stated in reference claim
     #get the xrefs to be added/updated
     
     ## TOT HIER WERKT HET!!!!
     global globalDiseaseOntology
     globalDiseaseOntology = diseaseOntology
     
     global globalWikidataID
     globalWikidataID = wikidataID
     
     global globalSite
     globalSite = site
      
     xrefs=doValues["xrefs"] # xrefs are the external identifiers from Disease ontology
     #get the data from WikiData
     wikidataEntry = getItem(site, wikidataID, "\\__")
     # prettyPrint(wikidataEntry['entities'][wikidataID])
     # pp.pprint(wikidataEntry)
     #wikidataEntry['entities'][wikidataID]['synonyms']=doValues["synonyms"]
     claims = wikidataEntry['entities'][wikidataID]['claims']  
     print xrefs.keys()
     
     for xrefKey in xrefs.keys(): # iterate over all xrefs contained in Disease Ontology
        print xrefKey
        xrefToAdd = []
        for item in xrefs[xrefKey]:
            xrefToAdd.append(item)
        # print xrefToAdd
        if xrefKey not in ProteinBoxBotKnowledge.diseaseWDProperties.keys():
            # Do nothing if the xref doesn't have a WikiData property
            print xrefKey + ": not recognized as a disease property in WikiData."
            continue
        print ProteinBoxBotKnowledge.diseaseWDProperties[xrefKey]
        print claims.keys()
        print ProteinBoxBotKnowledge.diseaseWDProperties[xrefKey] in claims.keys()
        if ProteinBoxBotKnowledge.diseaseWDProperties[xrefKey] in claims.keys(): #                
           for doXref in xrefs[xrefKey]:             
               # print xrefs[xrefKey][0]
               doReference = False
               print claims[ProteinBoxBotKnowledge.diseaseWDProperties[xrefKey]]
               for claim in claims[ProteinBoxBotKnowledge.diseaseWDProperties[xrefKey]]:                  
                   print "wikiData: "+claim["mainsnak"]["datavalue"]["value"]
                   print "Disease ontology: "+doXref
                   if str(claim["mainsnak"]["datavalue"]["value"]) == str(doXref):
                       ## On WikiData a claim exist with the value in DO
                       xrefToAdd.remove(str(doXref))
                       if "references" in claim.keys():                      
                           # print "There are references"
                           for reference in claim["references"]:
                               if 'P143' in reference["snaks"].keys():
                                   # print "There is an imported from:"
                                   for P143reference in reference["snaks"]["P143"]:
                                       # Check if the reference points to Disease ontology Q5282129
                                       print "Imported from: "+str(P143reference["datavalue"]["value"]["numeric-id"])
                                       if P143reference["datavalue"]["value"]["numeric-id"] == 5282129:
                                           doReference = True                                 
                                           break  # stop continueing reading all references
                                   # print doReference
                                   if doReference:
                                       print "updateClaim"
                                       claim = updateClaim(claim, doXref, obsolete)
                                       reference = setDateRetrievedTimestamp(reference)
                                       reference = setStatedIn(reference)
                                   else: # the reference to disease ontology doesn't exist
                                       claim["references"] = addReference(claim["references"], 'P143', 5282129)   
                       else:
                           claim["references"] = addReference([], 'P143', 5282129)

                       # break  # stop iterating over WD xrefs                                                      
        print "xrefsToAdd:" + ",".join(xrefToAdd)
        if len(xrefToAdd)>0:
             wikidataEntry = addClaims(wikidataEntry, ProteinBoxBotKnowledge.diseaseWDProperties[xrefKey], xrefToAdd, 'string', wikidataID, obsolete)                                             
     if 'P699' not in wikidataEntry['entities'][wikidataID]['claims'].keys():               
         wikidataEntry = addClaims(wikidataEntry, "P699", doValues["doid"][0].split(":")[1], 'string', wikidataID, obsolete)
     else:
         if "references" not in wikidataEntry['entities'][wikidataID]['claims']['P699'][0].keys():
             wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["references"] = addReference([], 'P143', 5282129)
             
         wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["mainsnak"]["datavalue"]["value"]=doValues["doid"][0].split(":")[1]        
         wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["references"][0] = setDateRetrievedTimestamp(wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["references"][0])
         wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["references"][0] = setStatedIn(wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["references"][0])                                         
     # print wikidataEntry['entities'][wikidataID]['claims']['P699'][0]["mainsnak"]["datavalue"]["value"]
          # print wikidataEntry
     
     wikidataEntry.pop("success", None)
     wikidataEntry['entities'][wikidataID].pop("modified", None)
     wikidataEntry['entities'][wikidataID].pop("lastrevid", None)
     wikidataEntry['entities'][wikidataID].pop("ns", None)
     wikidataEntry['entities'][wikidataID].pop("pageid", None)
     wikidataEntry['entities'][wikidataID].pop("title", None)
     wikidataEntry['entities'][wikidataID].pop("type", None)
     
     prettyPrint(wikidataEntry)
     if obsolete:
        wikidataEntry['entities'][wikidataID]['claims']['P699'][0]['rank']='deprecated'
     else:
        wikidataEntry['entities'][wikidataID]['claims']['P699'][0]['rank']='normal'
         
     token = repo.token(pywikibot.Page(repo, "Mecom adjacent non-protein coding RNA"), 'edit')
     # prettyPrint(wikidataEntry['entities'][wikidataID])
     with open("/tmp/wikidataOutput.json", "a") as myfile:
         myfile.write("=========================================\n")
         myfile.write(json.dumps(wikidataEntry['entities'], indent=4)+"\n")
     try:         
             request = api.Request(site=site,
                        action='wbeditentity',
                        format='json',
                        id=wikidataID,
                        bot=True,
                        token=token,
                        data=json.dumps(wikidataEntry['entities'][wikidataID]))
             
             data = request.submit()  
            
                                   
     except Exception, err:
         client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
         client.captureException()
         with open("/tmp/debugErrors.txt", "a") as myfile2:
             myfile2.write(traceback.format_exc())
 
        
def hasDiseaseProperties(site, repo, WdId):
    # P563 = ICD-O # P493 = ICD-9 # P494 = ICD-10 # P1550 = Orphanet # P492 = OMIM ID # P1395 = NCI # P486 = MeSH 
    return (hasProperty(site, WdId, 'P699') or \
       hasProperty(site, WdId, 'P563') or \
       hasProperty(site, WdId, 'P493') or \
       hasProperty(site, WdId, 'P494') or \
       hasProperty(site, WdId, 'P1550') or \
       hasProperty(site, WdId, 'P492') or \
       hasProperty(site, WdId, 'P1395') or \
       hasProperty(site, WdId, 'P486') or \
       hasProperty(site, WdId, 'P1461'))

def getLatestDiseaseOntology():
  try:
    namespaces = {'owl': 'http://www.w3.org/2002/07/owl#', 'rdfs': 'http://www.w3.org/2000/01/rdf-schema#', 'oboInOwl': 'http://www.geneontology.org/formats/oboInOwl#', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'}
    dourl = 'http://purl.obolibrary.org/obo/doid.owl'
    request = urllib2.Request(dourl)
    u = urllib2.urlopen(request)
    do = u.read()
    return ET.fromstring(do)       
  except Exception, err:
         client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
         client.captureException()
        

def reportItemsForCurations(doid, diseaseItems, diseaseLabelsText):
    with open("/tmp/curationReport", "a") as myfile:
        myfile.write(",".join(doid)+'\t'+"wdid: "+diseaseItems+'\t'+diseaseLabelsText+"\n")
        
def getDiseaseOntologyTimeStamp(diseaseOntology):
    doDate =  diseaseOntology.findall('.//oboInOwl:date', namespaces)
    dateList = doDate[0].text.split(' ')[0].split(":")
    timeList = doDate[0].text.split(' ')[1].split(":")
    # return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+timeList[0]+":"+timeList[1]+":00Z"
    return "+0000000"+dateList[2]+"-"+dateList[1]+"-"+dateList[0]+"T"+"00:00:00Z"


def addOrUpdateDOWDItem(site, repo, diseaseClass, diseaseOntologyTimeStamp, obsolete, diseaseOntology):
    global globalDiseaseOntology
    globalDiseaseOntology = diseaseOntology
    
    doValues = getDiseaseOntologyValues(diseaseClass)   
    print doValues

    # Search for WikiData entries of both the labels and the synonyms.     
    diseaseWdIDs = []    
    for diseaseLabel in doValues["labels"]:
        wikidata = getItems(site, diseaseLabel)
        for result in wikidata["search"]:
                  if "label" in result.keys():
                    if wikidata["searchinfo"]["search"].capitalize() == result["label"] :
                      diseaseWdIDs.append(result["id"])
                    if wikidata["searchinfo"]["search"] == result["label"] :
                      diseaseWdIDs.append(result["id"])
    
    for diseaseSynonym in doValues["synonyms"]:
        wikidata = getItems(site, diseaseSynonym)
        for result in wikidata["search"]:
            if isinstance(result, dict):
                  if "label" in result.keys():
                    if wikidata["searchinfo"]["search"].capitalize() == result["label"] :
                      diseaseWdIDs.append(result["id"])
                    if wikidata["searchinfo"]["search"] == result["label"] :
                      diseaseWdIDs.append(result["id"])  
    
    # If WikiData has a term for either a label or a synonym for a given Disease ontology class 
    ## If it is only one and that WikiData item has Disease Properties then update that item
    diseaseItems = []
    for WdId in diseaseWdIDs:
        print hasDiseaseProperties(site, repo, WdId)
        if hasDiseaseProperties(site, repo, WdId):
            diseaseItems.append(WdId)
    print diseaseWdIDs
     
    if len(diseaseItems) == 0:
        print "it is creating a new wd entry"
        if not "<new term>" in doValues["labels"]:
          with open("/tmp/listDOIDtoCreate.txt", "a") as myfile:
            myfile.write(",".join(doValues["doid"])+'\t'+"#".join(doValues["labels"])+"\n")
            createNewDOItemPage(site, repo, doValues, diseaseOntologyTimeStamp, obsolete)
    elif len(set(diseaseItems)) == 1:
        print "it is Updating an existing wd entry"
        print doValues
        print diseaseItems[0]    
        updateDOWDItem(site, repo, diseaseItems[0], doValues, diseaseOntologyTimeStamp, obsolete, globalDiseaseOntology)
    else: 
        print "it is reporting a curation concern"
        reportItemsForCurations(doValues["doid"], ",".join(set(diseaseItems)), "#".join(doValues["labels"]))   

def getDiseaseOntologyValues(diseaseClass):
    doValues = dict()
    doValues["doid"] = []
    doValues["labels"] = []
    doValues["synonyms"] = []
    doValues["xrefs"] = dict()
    
    #doid
    diseaseOntologyIds = diseaseClass.findall('.//oboInOwl:id', namespaces)
    for diseaseOntologyId in diseaseOntologyIds:
        doValues["doid"].append(diseaseOntologyId.text.encode('ascii', 'replace'))
    
    # Labels
    diseaseLabels = diseaseClass.findall('.//rdfs:label', namespaces)
    for diseaseLabel in diseaseLabels:
         doValues["labels"].append(diseaseLabel.text.encode('ascii', 'replace'))
    # Synonyms
    diseaseSynonyms = diseaseClass.findall('.//oboInOwl:hasExactSynonym', namespaces)
    for diseaseSynonym in diseaseSynonyms:
        doValues["synonyms"].append(diseaseSynonym.text.encode('ascii', 'replace'))
    externalReferences = diseaseClass.findall('.//oboInOwl:hasDbXref', namespaces)
    
    # External references
    for externalReference in externalReferences:
        if not externalReference.text.split(":")[0] in doValues["xrefs"].keys():
            doValues["xrefs"][externalReference.text.split(":")[0]] = []
        doValues["xrefs"][externalReference.text.split(":")[0]].append(externalReference.text.split(":")[1])
    return doValues
    
