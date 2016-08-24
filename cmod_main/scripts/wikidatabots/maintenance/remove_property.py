__author__ = 'andra'

# This is a maintenance bot which removes all occurences where a protein is incorrectly being encoded by another protein

import time
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../ProteinBoxBot_Core")
import PBB_login
import PBB_settings
import PBB_Core


logincreds = PBB_login.WDLogin(PBB_settings.getWikiDataUser(), PBB_settings.getWikiDataPassword())

data2add = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P682')]
wdPage = PBB_Core.WDItemEngine("Q169960", data=data2add, server="www.wikidata.org",
                                           domain="proteins")
wdPage.write(logincreds)