# -*- coding: utf-8 -*-
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
from raven import Client
import urllib2
import xml.etree.ElementTree as ET
import pprint
import pywikibot
from pywikibot.data import api
import ProteinBoxBotFunctions
import json

def getPubmedObject(pmid):
    try:
      pubmedUrl = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=Pubmed&Retmode=xml&id='+str(pmid)
      request = urllib2.Request(pubmedUrl)
      u = urllib2.urlopen(request)
      pubmedObject = u.read()
      return ET.fromstring(pubmedObject)       
    except Exception, err:
           client = Client('http://fe8543035e154f6591e0b578faeddb07:dba0f35cfa0a4e24880557c4ba99c7c0@sentry.sulab.org/9')
           client.captureException()

def getItems(site, itemtitle):
  params = { 'action' :'wbsearchentities' , 'format' : 'json' , 'language' : 'en', 'type' : 'item', 'search': itemtitle}
  request = api.Request(site=site,**params)
  return request.submit()

def addNewLabel(localdata, label):
    englishLabel = dict()
    englishLabel['language']='en'
    englishLabel['value']=label
    englishLabels=dict()
    englishLabels['en']=englishLabel
    localdata['entities']['labels']=englishLabels
    return localdata

def addNewAlias(localdata, label):
    aliases={'en':[]}
    tempAlias = dict()
    tempAlias["language"] = "en"
    tempAlias["value"] = label
    aliases['en'].append(tempAlias)
    localdata['entities']['aliases']=aliases
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
        statement["references"]=addReference(statement["references"], 'P248', 180686, stated)
        localdata["entities"]["claims"][property].append(statement)
    return localdata

def addReference(references, property, itemId, stated=True):
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
        references.append(reference)
        return references

def setStatedIn(reference):
    return None

print "Start..."
# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

pubmedClass = getPubmedObject(25522365)
pubmedClass = getPubmedObject(19034548)
# pubmedClass = getPubmedObject(19715393)
pubmedClass = getPubmedObject(25058083)
pmidRet = pubmedClass.findall('.//MedlineCitation/PMID')
doiRet = pubmedClass.findall(".//ArticleIdList/ArticleId[@IdType='doi']")
print len(doiRet)
print doiRet[0].text
pmcRet = pubmedClass.findall(".//ArticleIdList/ArticleId/[@IdType='pmc']")
articleTitle = pubmedClass.findall('.//MedlineCitation/Article/ArticleTitle')
results =  ProteinBoxBotFunctions.getItems(site, articleTitle[0].text.encode("utf-8"))
PubmedObject = None
if len(results["search"]) == 0:
    pubmedObject ={   u'entities': {   }}
    pubmedObject["entities"]["claims"]=dict()
    token = repo.token(pywikibot.Page(repo, articleTitle[0].text.encode("utf-8")), 'edit')
    pubmedObject = ProteinBoxBotFunctions.addNewLabel(pubmedObject, articleTitle[0].text.encode("utf-8"))
    pubmedObject = ProteinBoxBotFunctions.addNewClaims(pubmedObject, 'P856', ["http://www.ncbi.nlm.nih.gov/pubmed/"+pmidRet[0].text], 'string', False) # official website P856
    pubmedObject = ProteinBoxBotFunctions.addNewClaims(pubmedObject, 'P698', [pmidRet[0].text], 'string', False) # PubMed ID P698
    if len(pmcRet)>0:
        pubmedObject = ProteinBoxBotFunctions.addNewClaims(pubmedObject, 'P932', [pmcRet[0].text], 'string', False) # PMCID P932
    if len(doiRet)>0:
        pubmedObject = ProteinBoxBotFunctions.addNewClaims(pubmedObject, 'P356', [doiRet[0].text], 'string', False) # DOI P356
print len(results["search"])
print pmidRet[0].text
print articleTitle[0].text.encode("utf-8")

# Journal info
journalTitle = pubmedClass.findall('.//MedlineCitation/Article/Journal/Title')
journalIsoAbrev = pubmedClass.findall('.//MedlineCitation/Article/Journal/ISOAbbreviation')
journalIssn = pubmedClass.findall('.//MedlineCitation/MedlineJournalInfo/ISSNLinking')
print journalTitle[0].text.encode("utf-8") 
print journalIsoAbrev[0].text.encode("utf-8")

journalResults = getItems(site, journalTitle[0].text.encode("utf-8"))
existsAsScienceJournal = False
ID = None
token = repo.token(pywikibot.Page(repo, articleTitle[0].text.encode("utf-8")), 'edit')
if len(journalResults["search"]) > 0:
    pprint.pprint(journalResults)
    for journalResult in journalResults["search"]:
        print journalResult["id"]  

        params = {
                      'action' :'wbgetclaims' ,
                      'entity' : journalResult["id"],
                      'property': 'P31',
                 }
        request = api.Request(site=site,**params)
        data =  request.submit()
        if len(data["claims"]) > 0:
            for claim in data["claims"]['P31']:
               if claim['mainsnak']['datavalue']['value']['numeric-id']==5633421:
                     existsAsScienceJournal = True
                     ID = journalResult["id"]
                     break
    	if existsAsScienceJournal:
           break       
                  
if not existsAsScienceJournal:
   journalObject ={   u'entities': {   }}
   journalObject["entities"]["claims"]=dict()
   journalObject = ProteinBoxBotFunctions.addNewLabel(journalObject, journalTitle[0].text.encode("utf-8"))
   # journalObject = ProteinBoxBotFunctions.addNewAliases(journalObject, journalIsoAbrev[0].text)
   journalObject = ProteinBoxBotFunctions.addNewClaims(journalObject, 'P31', [5633421], 'wikibase-entityid', False)
   if len(journalIssn)>0:
      journalObject = ProteinBoxBotFunctions.addNewClaims(journalObject, 'P236', [journalIssn[0].text], 'string', False)
   ProteinBoxBotFunctions.prettyPrint(journalObject)
   request = api.Request(site=site,
                                  action='wbeditentity',
                                  format='json',
                                  new='item',
                                  bot=True,
                                  token=token,
                                  data=json.dumps(journalObject['entities']))
   data = request.submit()
   ID = data['entity']['id']
   print ID 


# Author info
authorList = pubmedClass.findall('.//MedlineCitation/Article/AuthorList/Author')
collectiveName = pubmedClass.findall('.//MedlineCitation/Article/AuthorList/CollectiveName')
pubmedAuthors = []
for author in authorList:
  if len(collectiveName) == 0:
   lastName = author.find('LastName')
   # Add Last name to WD
   lastNameExists = False
   if lastName != None:
       lastNameResults = getItems(site, lastName.text.encode("utf-8"))
   lastNameID = None
   if len(lastNameResults["search"]) > 0:
      for lastNameResult in lastNameResults["search"]:
        params = {
                      'action' :'wbgetclaims' ,
                      'entity' : lastNameResult["id"],
                      'property': 'P31',
                 }
        request = api.Request(site=site,**params)
        data =  request.submit()
        if len(data["claims"]) > 0:
           for claim in data["claims"]['P31']:
               if claim['mainsnak']['datavalue']['value']['numeric-id']==101352:
                    lastNameExists = True
                    lastNameID = lastNameResult["id"]
                    print lastNameResult["id"]
                    break
        if lastNameExists:
             break
   if not lastNameExists:
       lastNameObject ={   u'entities': {   }}
       lastNameObject["entities"]["claims"]=dict()
       lastNameObject = addNewLabel(lastNameObject, lastName.text.encode("utf-8"))
       lastNameObject = addNewClaims(lastNameObject, 'P31', [101352], 'wikibase-entityid', False)    
       request = api.Request(site=site,
                                  action='wbeditentity',
                                  format='json',
                                  new='item',
                                  bot=True,
                                  token=token,
                                  data=json.dumps(lastNameObject['entities']))
       data = request.submit()
       lastNameID = data['entity']['id']
       print lastNameID 

   foreName = author.find('ForeName')
   givenNameExists = False
   if foreName != None:
       givenNameResults = getItems(site, foreName.text.encode("utf-8"))
   givenNameID = None
   if len(givenNameResults["search"]) > 0:
      for givenNameResult in givenNameResults["search"]:
        params = {
                      'action' :'wbgetclaims' ,
                      'entity' : givenNameResult["id"],
                      'property': 'P31',
                 }
        request = api.Request(site=site,**params)
        data =  request.submit()
        if len(data["claims"]) > 0:
           for claim in data["claims"]['P31']:
               if claim['mainsnak']['datavalue']['value']['numeric-id']==202444:
                    givenNameExists = True
                    givenNameID = givenNameResult["id"]
                    print givenNameResult["id"]
                    break
        if givenNameExists:
             break
   if not givenNameExists:
       givenNameObject ={   u'entities': {   }}
       givenNameObject["entities"]["claims"]=dict()
       givenNameObject = addNewLabel(givenNameObject, foreName.text.encode("utf-8"))
       givenNameObject = addNewClaims(givenNameObject, 'P31', [202444], 'wikibase-entityid', False)
       request = api.Request(site=site,
                                  action='wbeditentity',
                                  format='json',
                                  new='item',
                                  bot=True,
                                  token=token,
                                  data=json.dumps(givenNameObject['entities']))
       data = request.submit()
       givenNameID = data['entity']['id']
       print givenNameID
   initials = author.find('Initials')

   if foreName != None and lastName != None:
       print foreName.text.encode("utf-8") + " " + lastName.text.encode("utf-8") + " aka " + initials.text.encode("utf-8") + " " + lastName.text.encode("utf-8")
 
   #@ Add affiliation to WD
   affiliation = author.find('AffiliationInfo/Affiliation')
   affiliationID = None
   affiliationExists = False 
   if affiliation != None:
      print affiliation.text.encode("utf-8")
      affiliationResults = getItems(site, affiliation.text.encode("utf-8"))
      affiliationID = None
      if len(affiliationResults["search"])>0:
           for affiliationResult in affiliationResults["search"]:
                params = {
				'action' : 'wbgetclaims' ,
				'entity' : affiliationResult["id"] ,
				'property' : 'P31' ,
			 }
		request = api.Request(site=site,**params)
        	data =  request.submit()
                if len(data["claims"]) > 0:
           		for claim in data["claims"]['P31']:
               			if claim['mainsnak']['datavalue']['value']['numeric-id']==43229:
					affiliationExists = True
					affiliationID = affiliationResult["id"]
					break
		if affiliationExists:
		   break
      if not affiliationExists:
         affiliationObject = {   u'entities': {   }}
         affiliationObject["entities"]["claims"]=dict()
         affiliationObject = addNewLabel(affiliationObject, affiliation.text.encode("utf-8"))
         affiliationObject = addNewClaims(affiliationObject, 'P31', [43229], 'wikibase-entityid', False)
         request = api.Request(site=site,
			       action='wbeditentity',
                               format='json',
                               new='item',
                               bot=True,
                               token=token,
                               data=json.dumps(affiliationObject['entities']))
         data = request.submit()
         affiliationID = data['entity']['id']	              
    
   ## Add an author to WD
   initials = author.find('Initials')
   print foreName.text.encode("utf-8") + " " + lastName.text.encode("utf-8") + " aka " + initials.text.encode("utf-8") + " " + lastName.text.encode("utf-8")
  
   authorName = foreName.text.encode("utf-8") + " " + lastName.text.encode("utf-8")
   authorAlias = initials.text.encode("utf-8") + " " + lastName.text.encode("utf-8")
   authorExists = False
   authorResults = getItems(site, authorName)
   authorID = None
   if len(authorResults["search"]) > 0:
     for authorResult in authorResults["search"]:
        params = {
                     'action' :'wbgetclaims' ,
                     'entity' : authorResult["id"],
                     'property': 'P31',
                 }
        request = api.Request(site=site,**params)
        data =  request.submit()
        if len(data["claims"]) > 0:
           for claim in data["claims"]['P31']:
               if claim['mainsnak']['datavalue']['value']['numeric-id']==482980:
                   authorExists = True
                   authorID = authorResult["id"]
                   break
        if authorExists:
           break
   if not authorExists:
      authorObject = {   u'entities': {   }}
      authorObject["entities"]["claims"]=dict()
      authorObject = addNewLabel(authorObject, authorName)
      authorObject = addNewAlias(authorObject, authorAlias)
      authorObject = addNewClaims(authorObject, 'P31', [482980], 'wikibase-entityid', False)
      authorObject = addNewClaims(authorObject, 'P735', [givenNameID[1:]], 'wikibase-entityid', False)
      authorObject = addNewClaims(authorObject, 'P734', [lastNameID[1:]], 'wikibase-entityid', False)
      if affiliation != None:
           authorObject = addNewClaims(authorObject, 'P1416', [affiliationID[1:]], 'wikibase-entityid', False)
      ProteinBoxBotFunctions.prettyPrint(authorObject['entities'])
      request = api.Request(site=site,
                               action='wbeditentity',
                               format='json',
                               new='item',
                               bot=True,
                               token=token,
                               data=json.dumps(authorObject['entities']))
      data = request.submit()  
      authorID = data['entity']['id'] 
   print authorID
   pubmedAuthors.append(authorID[1:])

# Finally add the pubmed entry
pubmedEntryExists = False
results =  ProteinBoxBotFunctions.getItems(site, articleTitle[0].text.encode("utf-8"))
pubmedWDID = None
if len(results["search"]) > 0:
      for result in results["search"]:
         params = {
			'action' : 'wbgetclaims' ,
                        'entity' : result["id"] ,
  			'property': 'P31' ,
		  }
         request = api.Request(site=site,**params)
         data =  request.submit()
         if len(data["claims"]) > 0:
            for claim in data["claims"]['P31']:
               if claim['mainsnak']['datavalue']['value']['numeric-id']==732577:
 		  pubmedEntryExists=True
		  pubmedWDID = result["id"]
       		  break
    	 if pubmedEntryExists:
		break
if not pubmedEntryExists:
       pubmedObject ={   u'entities': {   }}
       pubmedObject["entities"]["claims"]=dict()
       token = repo.token(pywikibot.Page(repo, articleTitle[0].text.encode("utf-8")), 'edit')
       pubmedObject = addNewLabel(pubmedObject, articleTitle[0].text.encode("utf-8"))
       pubmedObject = addNewClaims(pubmedObject, 'P856', ["http://www.ncbi.nlm.nih.gov/pubmed/"+pmidRet[0].text], 'string', False) # official website P856
       pubmedObject = addNewClaims(pubmedObject, 'P698', [pmidRet[0].text], 'string', False) # PubMed ID P698
       if len(pmcRet)>0:
          pubmedObject = addNewClaims(pubmedObject, 'P932', [pmcRet[0].text], 'string', False) # PMCID P932
       if len(doiRet)>0:
          pubmedObject = addNewClaims(pubmedObject, 'P356', [doiRet[0].text], 'string', False) # DOI P356
       pubmedObject = addNewClaims(pubmedObject, 'P1433', [ID[1:]], 'wikibase-entityid', False) # Published In P1433
       pubmedObject = addNewClaims(pubmedObject, 'P31', [732577], 'wikibase-entityid', False) # Published In P1433
       pubmedObject = addNewClaims(pubmedObject, 'P50', pubmedAuthors, 'wikibase-entityid', False) # Author P50
       ProteinBoxBotFunctions.prettyPrint(pubmedObject['entities'])       
       request = api.Request(site=site,
                               action='wbeditentity',
                               format='json',
                               new='item',
                               bot=True,
                               token=token,
                               data=json.dumps(pubmedObject['entities']))
       data = request.submit()
       pubmedID = data['entity']['id']
       print pubmedID
