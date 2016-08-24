__author__ = 'andra'

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

logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

for x in range (7, 21):

    prep = dict()
    prep['P279'] = [PBB_Core.WDItemID(value='Q37748', prop_nr='P279')]
    prep['P703'] = [PBB_Core.WDItemID(value='Q184224', prop_nr='P703')]
    data2add = []
    for key in prep.keys():
            for statement in prep[key]:
                data2add.append(statement)
                print(statement.prop_nr, statement.value)
    wdPage = PBB_Core.WDItemEngine(item_name="rat chromosome "+str(x), data=data2add, server="www.wikidata.org", domain="genes")
    wdPage.set_description(description='Rattus norvegicus chromosome', lang='en')
    wdPage.write(logincreds)

