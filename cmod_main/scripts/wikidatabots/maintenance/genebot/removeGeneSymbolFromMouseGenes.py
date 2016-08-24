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
import time
try:
    import simplejson as json
except ImportError as e:
    import json

start = time.time()
entrezWikidataIds = dict()
wdqQuery = "CLAIM[703:83310] AND CLAIM[353]"
InWikiData = PBB_Core.WDItemList(wdqQuery, wdprop="353")
for geneItem in InWikiData.wditems["props"]["353"]:
        entrezWikidataIds[str(geneItem[2])] = geneItem[0]
pprint.pprint(entrezWikidataIds)
print(len(entrezWikidataIds))

for symbol in entrezWikidataIds.keys():
  try:
    data2add = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P353')]
    wdPage = PBB_Core.WDItemEngine('Q'+str(entrezWikidataIds[symbol]), data=data2add, server="www.wikidata.org",
                                           domain="genes")
    login = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())
    print('Q'+str(entrezWikidataIds[symbol]))
    wdPage.write(login)
    print('Q'+str(entrezWikidataIds[symbol]))
    PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id='Q'+str(entrezWikidataIds[symbol]),
                        exception_type='',
                        message='',
                        wd_id='Q'+str(entrezWikidataIds[symbol]),
                        duration=time.time()-start
                    ))
  except Exception as e:
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id='Q'+str(entrezWikidataIds[symbol]),
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='-',
                        duration=time.time() - start
                    ))
