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
import pprint
import sys

gene_ontologydataids = dict()
print('Getting all proteins with a uniprot ID in Wikidata...')
inwikidata = PBB_Core.WDItemList("CLAIM[686] and CLAIM[351]", "686")
for goItem in inwikidata.wditems["props"]["686"]:
    if not "GO:" in str(goItem[2]):
        gene_ontologydataids[str(goItem[2])] = goItem[0]

pprint.pprint(gene_ontologydataids)
print(len(gene_ontologydataids))
logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
prep = dict()
for id in gene_ontologydataids.keys():
    print(id)
    wdid = 'Q'+str(gene_ontologydataids[str(id)])
    prep["P686"] = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P686')]
    data2Add = []
    for key in prep.keys():
      for statement in prep[key]:
          data2Add.append(statement)
          print(statement.prop_nr, statement.value)
    wdPage = PBB_Core.WDItemEngine(wd_item_id=wdid, data=data2Add,
                                                  server="www.wikidata.org",
                                                  domain="proteins")
    print(wdid)
    print(wdPage.get_wd_json_representation())
    wdPage.write(logincreds)


