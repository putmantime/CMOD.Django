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
# Load the path to the PBB_Core library
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__))+"/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_Debug
import PBB_Functions
import PBB_login
import PBB_settings

# Resource specific 
import gene

import traceback
from datetime import date, datetime, timedelta


try:

    speciesInfo = dict()
    speciesInfo["human"] = dict()
    speciesInfo["9606"] = dict()
    speciesInfo["mouse"] = dict()
    speciesInfo["10090"] = dict()
    speciesInfo["rat"] = dict()
    speciesInfo["10116"] = dict()
    
    speciesInfo["human"]["taxid"] = "9606"
    speciesInfo["human"]["wdid"] = "Q5"
    speciesInfo["human"]["name"] = "human"
    speciesInfo["human"]["de-name"] = "Humanes"
    speciesInfo["human"]["fr-name"] = "Humaine"
    speciesInfo["human"]["nl-name"] = "Menselijk"
    speciesInfo["human"]["release"] = "Q20950174"
    speciesInfo["human"]["genome_assembly"] = "Q20966585"
    speciesInfo["human"]["genome_assembly_previous"] = "Q21067546"

    speciesInfo["9606"]["taxid"] = "9606"
    speciesInfo["9606"]["wdid"] = "Q5"
    speciesInfo["9606"]["name"] = "human"
    speciesInfo["9606"]["de-name"] = "Humanes"
    speciesInfo["9606"]["fr-name"] = "Humaine"
    speciesInfo["9606"]["nl-name"] = "Menselijk"
    speciesInfo["9606"]["release"] = "Q20950174"
    speciesInfo["9606"]["genome_assembly"] = "Q20966585"
    speciesInfo["9606"]["genome_assembly_previous"] = "Q21067546"

    speciesInfo["mouse"]["taxid"] = "10090"
    speciesInfo["mouse"]["wdid"] = "Q83310"
    speciesInfo["mouse"]["name"] = "mouse"
    speciesInfo["mouse"]["fr-name"] = "de souris"
    speciesInfo["mouse"]["nl-name"] = "muizen"
    speciesInfo["mouse"]["release"] = "Q20973051"
    speciesInfo["mouse"]["genome_assembly"] = "Q20973075"
    speciesInfo["mouse"]["genome_assembly_previous"] = "Q20973075"

    speciesInfo["10090"]["taxid"] = "10090"
    speciesInfo["10090"]["wdid"] = "Q83310"
    speciesInfo["10090"]["name"] = "mouse"
    speciesInfo["10090"]["fr-name"] = "souris"
    speciesInfo["10090"]["nl-name"] = "muizen"
    speciesInfo["10090"]["release"] = "Q20973051"
    speciesInfo["10090"]["genome_assembly"] = "Q20973075"
    speciesInfo["10090"]["genome_assembly_previous"] = "Q20973075"

    speciesInfo["rat"]["taxid"] = "10116"
    speciesInfo["rat"]["wdid"] = "Q184224"
    speciesInfo["rat"]["name"] = "rat"
    speciesInfo["rat"]["release"] = "Q19296606"
    speciesInfo["rat"]["genome_assembly"] = "Q21578759"
    speciesInfo["rat"]["genome_assembly_previous"] = "None"

    speciesInfo["10116"]["taxid"] = "10116"
    speciesInfo["10116"]["wdid"] = "Q184224"
    speciesInfo["10116"]["name"] = "rat"
    speciesInfo["10116"]["release"] = "Q19296606"
    speciesInfo["10116"]["genome_assembly"] = "Q21578759"
    speciesInfo["10116"]["genome_assembly_previous"] = "None"

    if len(sys.argv) == 1:
        print("Please provide one of the following species as argument: "+ str(speciesInfo.keys()))
        print("Example: python ProteinBoxBot_EntrezGene.py human")
        sys.exit()
    else:
        if not sys.argv[1] in speciesInfo.keys():
            print(sys.argv[1] + " is not (yet) supported.")
            sys.exit()

    tempvar = dict()
    tempvar["speciesInfo"] = speciesInfo
    tempvar["species"] = sys.argv[1]
    genome = gene.genome(tempvar)
    
      
except (Exception):
    print(traceback.format_exc())
    # client.captureException()  