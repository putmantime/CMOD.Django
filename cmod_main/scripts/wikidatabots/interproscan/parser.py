"""
Parse InterPro flat files

Flat files:
ftp://ftp.ebi.ac.uk/pub/databases/interpro/interpro.xml.gz
ftp://ftp.ebi.ac.uk/pub/databases/interpro/protein2ipr.dat.gz

interpro.xml.gz information about each interpro item
protein2ipr.dat.gz contains annotations for each protein in uniprot

@author: gstupp
"""
import gzip
import json
import os
import subprocess
import sys
from itertools import groupby

import lxml.etree as et
import requests
from dateutil import parser as dup
from tqdm import tqdm

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


class IPRTerm:
    """
    Represents one interproscan term/item

    """
    type2desc = {"Active_site": "InterPro Active Site",
                 "Binding_site": "InterPro Binding Site",
                 "Conserved_site": "InterPro Conserved Site",
                 "Domain": "InterPro Domain",
                 "Family": "InterPro Family",
                 "PTM": "InterPro PTM",
                 "Repeat": "InterPro Repeat"}

    def __init__(self, name=None, short_name=None, id=None, parent=None, children=None, contains=None,
                 found_in=None, level=None, type=None, description=None, **kwargs):
        self.name = name
        self.short_name = short_name
        self.id = id
        self.parent = parent
        self.children = children
        self.contains = contains
        self.found_in = found_in
        self.level = level
        self.type = type
        self.description = description
        if self.description is None and self.type:
            self.description = IPRTerm.type2desc[self.type]

    def __repr__(self):
        return '{}: {}'.format(self.id, self.name)

    def __str__(self):
        return '{}: {}'.format(self.id, self.name)


def get_unprot_ids_from_species(species_wdid):
    """
    # get all uniprot ids from species
    :param species_wdid: wikidata id of the species
    :type species_wdid: str
    :return: set of uniprot ids (string)
    """
    query = """PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        SELECT ?item ?id
        WHERE
        {{
            ?item wdt:P279 wd:Q8054 .
            ?item wdt:P703 wd:{0} .
            ?item wdt:P352 ?id
        }}""".format(species_wdid)
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()

    human_uniprot = {x['id']['value']: x['item']['value'] for x in data['results']['bindings']}
    uniprot_ids = set(human_uniprot.keys())
    return uniprot_ids


def get_all_unprot_ids():
    """
    returns set of all uniprot id for all items in wikidata
    :return:
    """
    query = """
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT DISTINCT ?protein ?uniprotID WHERE {
       ?protein wdt:P352 ?uniprotID . # P352 UniProt ID
       #?protein wdt:P703 ?species . # P703 Found in taxon
    }"""
    url = 'https://query.wikidata.org/bigdata/namespace/wdq/sparql'
    data = requests.get(url, params={'query': query, 'format': 'json'}).json()

    # x['protein']['value'].replace('http://www.wikidata.org/entity/', '')
    return {x['uniprotID']['value'] for x in data['results']['bindings']}


def parse_protein2ipr(p2ipr_filename, keep_ids=None):
    """
    A0A060XN28	IPR029064	50S ribosomal protein L30e-like	SSF55315	17	101
    A0A060XN29	IPR003653	Ulp1 protease family, C-terminal catalytic domain	PF02902	412	581
    A0A060XN29	IPR003653	Ulp1 protease family, C-terminal catalytic domain	PS50600	397	562
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PF00001	1	234
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	28	49
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	72	95
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	174	198
    A0A060XN30	IPR000276	G protein-coupled receptor, rhodopsin-like	PR00237	216	242
    A0A060XN30	IPR000455	5-Hydroxytryptamine 2A receptor	PTHR24247:SF30	1	282
    A0A060XN30	IPR017452	GPCR, rhodopsin-like, 7TM	PS50262	1	234
    A0A060XN31	IPR004092	Mbt repeat	PF02820	50	117
    A0A060XN31	IPR004092	Mbt repeat	PS51079	1	114
    A0A060XN31	IPR004092	Mbt repeat	PS51079	122	196
    A0A060XN31	IPR004092	Mbt repeat	SM00561	23	114
    """

    p = subprocess.Popen(["zcat", p2ipr_filename], stdout=subprocess.PIPE).stdout
    uni_dict = {}
    p2ipr = map(lambda x: x.decode('utf-8').rstrip().split('\t'), p)
    for key, lines in tqdm(groupby(p2ipr, key=lambda x: x[0]), total=51536456):
        # the total is just for a time estimate. Nothing bad happens if the total is wrong
        if keep_ids and key not in keep_ids:
            continue
        protein = []
        for line in lines:
            uniprot_id, interpro_id, name, ext_id, start, stop = line
            protein.append({'uniprot_id': uniprot_id, 'interpro_id': interpro_id, 'name': name,
                            'ext_id': ext_id, 'start': start, 'stop': stop})
        uni_dict[key] = protein
    return uni_dict


def parse_protein_ipr(species_wdid=None):
    p2ipr_filename = os.path.join(DATA_DIR, "protein2ipr.dat.gz")
    keep_ids = get_unprot_ids_from_species(species_wdid) if species_wdid else get_all_unprot_ids()
    print("Found {} proteins".format(len(keep_ids)))
    uni_dict = parse_protein2ipr(p2ipr_filename, keep_ids=keep_ids)

    filename = "interproscan_uniprot_{}.json".format(species_wdid) if species_wdid else "interproscan_uniprot_all.json"
    with open(os.path.join(DATA_DIR, filename), 'w') as f:
        json.dump(uni_dict, f, indent=2)


def parse_interpro_xml():
    d = {}

    f = gzip.GzipFile(os.path.join(DATA_DIR, "interpro.xml.gz"))
    parser = et.parse(f)
    root = parser.getroot()

    release_info = dict(root.find("release").find("dbinfo[@dbname='INTERPRO']").attrib)
    release_info['date'] = dup.parse(release_info['file_date'])

    for itemxml in root.findall("interpro"):
        item = IPRTerm(name=itemxml.find('name').text, **itemxml.attrib)
        parents = [x.attrib['ipr_ref'] for x in itemxml.find("parent_list").getchildren()] if itemxml.find(
            "parent_list") is not None else None
        children = [x.attrib['ipr_ref'] for x in itemxml.find("child_list").getchildren()] if itemxml.find(
            "child_list") is not None else None
        contains = [x.attrib['ipr_ref'] for x in itemxml.find("contains").getchildren()] if itemxml.find(
            "contains") is not None else None
        found_in = [x.attrib['ipr_ref'] for x in itemxml.find("found_in").getchildren()] if itemxml.find(
            "found_in") is not None else None
        if parents:
            assert len(parents) == 1
            item.parent = parents[0]
        item.children = children
        item.contains = contains
        item.found_in = found_in
        d[item.id] = item
    return d, release_info


if __name__ == "__main__":
    # check for or download flat files
    quit = False
    file1 = os.path.join(DATA_DIR, "protein2ipr.dat.gz")
    if not os.path.exists(file1):
        print("{} not found. Download:\n{}".format(file1, "ftp://ftp.ebi.ac.uk/pub/databases/interpro/protein2ipr.dat.gz"))
        quit = True
    file2 = os.path.join(DATA_DIR, "interpro.xml.gz")
    if not os.path.exists(file2):
        print("{} not found. Download:\n{}".format(file2, "ftp://ftp.ebi.ac.uk/pub/databases/interpro/interpro.xml.gz"))
        quit = True
    if quit:
        sys.exit(1)
    if len(sys.argv) == 2:
        parse_protein_ipr(sys.argv[1])
    else:
        print("you can pass wiki data ID of species you'd like to parse from interpro flat file")
        parse_protein_ipr()
