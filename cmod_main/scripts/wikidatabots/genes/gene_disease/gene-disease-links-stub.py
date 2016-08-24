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

# This is a stub bot that was run and successfully extended just the gene SLC1A1 in Wikidata with a
# gene-disease link from the OMIM data source in Phenocarta. This suitably provides disease information
# to be pulled into the gene infobox for SLC1A1 on Wikipedia.

# login to Wikidata
login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
value = PBB_Core.WDItemID(value="Q41112", prop_nr="P2293")
	    # https://www.wikidata.org/wiki/Wikidata:Property_proposal/Natural_science#genetic_Association
	    # note: property now approved: P2293. id for schiz: Q41112

# Get a pointer to the Wikidata page on the gene under scrutiny
wd_gene_page = PBB_Core.WDItemEngine(wd_item_id="Q18031520", data=[value], server="www.wikidata.org", domain="genes")
#Q18037645 <- id for apol2
#Q18031520 <- id for slc1a1
wd_json_representation = wd_gene_page.get_wd_json_representation()
pprint.pprint(wd_json_representation)

# Write to Wikidata
# UNCOMMENT ONLY IF CONFIDENT ENOUGH ON CONTENT BEING ADDED (i.e. wd_json_representation
#wd_gene_page.write(login)







