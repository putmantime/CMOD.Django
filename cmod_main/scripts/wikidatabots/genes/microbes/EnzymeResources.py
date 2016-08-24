import Bio.ExPASy.Enzyme as bee
import re
import pprint
import requests
import urllib.request
import sys
import pandas as pd
import tempfile
__author__ = 'timputman'

enzyme_out = open('enz_out.txt', 'w')


def link_compound2chebi(compound):
    """
    used NCBO Annotator from BioPortal to return ChEBI IDS
    for substrates and products of reactions from Expasy enzyme

    """
    url = 'http://data.bioontology.org/annotator'
    params = dict(apikey=sys.argv[1], text=compound, ontologies='CHEBI', longest_only='true',
                  include='properties', exlude_numbers='false', exclude_synonyms='false', mappins='all')
    tm_results = requests.get(url=url, params=params).json()
    for i in tm_results:
        prefLabel = i['annotatedClass']['properties']['http://data.bioontology.org/metadata/def/prefLabel']
        text_input = i['annotations'][0]['text']
        if prefLabel[0].lower() == text_input.lower():
            final_chebi = i['annotatedClass']['@id'].split("/")[-1]
            return final_chebi.split("_")[-1]


def replace_strings(compound):
    """
    takes list of compound names and replaces with names formatted for NCBO annotator
    """
    names = {'H(2)O': 'water',
             'CO(2)': 'carbon dioxide'
            }

    for k, v in names.items():
        if compound == k:
            return compound.replace(k,v)
        else:
            return compound


def get_expasy_enzyme():
    """

    """
    url = "ftp://ftp.expasy.org/databases/enzyme/enzyme.dat"
    enzyme = urllib.request.urlretrieve(url)
    enzyme_p = bee.parse(open(enzyme[0], 'r'))
    enz_records = []
    count = 0
    for record in enzyme_p:

        enz_rec = {}
        enz_rec['Reaction(s)'] = record['CA']
        #create record for each enzyme with EC number as primary key
        enz_rec['PreferedName'] = record['DE']
        enz_rec['ECNumber'] = record['ID']
        enz_rec['Reaction(s)'] = []
        enz_rec['Substrates'] = {}
        enz_rec['Products'] = {}
        enz_rec['UniProt'] = {}
        enz_records.append(enz_rec)

        # split split to seperate multiple reactions
        reaction1 = record['CA'].split('.')
        for rxn in reaction1:
            if len(reaction1) > 2:
                rxn = rxn[3:]
            enz_rec['Reaction(s)'].append(rxn)
            #split reactions into [substrates, products]
            constituents = rxn.split('=')
            # split each side of reaction on '+' not '(+)'
            r = re.compile(r'(?:[^\+(]|\([^)]*\))+')
            substrates = r.findall(constituents[0])
            products = r.findall(constituents[-1])

            if substrates:
                for sub in substrates:
                    sub = replace_strings(sub.lstrip().rstrip())
                    schebi = link_compound2chebi(sub)
                    enz_rec['Substrates'][sub] = schebi
            if products:
                for prod in products:
                    prod = replace_strings(prod.lstrip().rstrip())
                    pchebi = link_compound2chebi(prod)
                    enz_rec['Products'][prod] = pchebi

                # populate enz_rec['UniProt'] with dictionary of uniprotid:name key, value pairs for protein
            for unpid in record['DR']:
                enz_rec['UniProt'][unpid[0]] = unpid[1]

        enz_records.append(enz_rec)

    return enz_records

expasy = get_expasy_enzyme()
OUT = open('enzyme_parsed.txt', 'w')
print(expasy, file=OUT)

