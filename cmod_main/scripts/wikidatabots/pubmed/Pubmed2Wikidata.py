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

def addPubmed2WD(pmid, site, repo):
  pubmedClass = getPubmedObject(pmid)
  pmidRet = pubmedClass.findall('.//MedlineCitation/PMID')
  articleTitle = pubmedClass.findall('.//MedlineCitation/Article/ArticleTitle')
  PubmedObject = None
  pubmedEntryExists=False
  results =  ProteinBoxBotFunctions.getItems(site, articleTitle[0].text.encode("utf-8"))
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
               if claim['mainsnak']['datavalue']['value']['numeric-id']==18918145:
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
       pubmedObject = addNewClaims(pubmedObject, 'P698', [pmidRet[0].text], 'string', False) # PubMed ID P698
       pubmedObject = addNewClaims(pubmedObject, 'P31', [18918145], 'wikibase-entityid', False) # Published In P1433
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


# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
repo = site.data_repository()

addPubmed2WD(18652912, site, repo)