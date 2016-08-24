import json
import os
from datetime import datetime

from SPARQLWrapper import SPARQLWrapper, JSON
from tqdm import tqdm

from ProteinBoxBot_Core import PBB_Core, PBB_login
from ProteinBoxBot_Core.PBB_Core import WDApiError
from interproscan.WDHelper import WDHelper
from interproscan.local import WDUSER, WDPASS
from interproscan.parser import parse_interpro_xml

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INTERPRO = "P2926"
SERVER = "www.wikidata.org"


class IPRItem:
    """
    create wikidata item from an IPRTerm
    """
    login = None
    reference = None
    fr = {"InterPro Active Site": "Site Actif InterPro",
          "InterPro Binding Site": "Site de Liaison InterPro",
          "InterPro Conserved Site": "Site Conservé InterPro",
          "InterPro Domain": "Domaine InterPro",
          "InterPro Family": "Famille InterPro",
          "InterPro PTM": "MPT InterPro",
          "InterPro Repeat": "Répétition InterPro"}

    type2subclass = {"Active_site": "Q423026",  # Active site
                     "Binding_site": "Q616005",  # Binding site
                     "Conserved_site": "Q7644128",  # Supersecondary_structure
                     "Domain": "Q898273",  # Protein domain
                     "Family": "Q417841",  # Protein family
                     "PTM": "Q898362",  # Post-translational modification
                     "Repeat": "Q3273544"}  # Structural motif

    def __init__(self, ipr, date, version):
        self.name = ipr.name
        self.id = ipr.id
        self.type = ipr.type
        self.description = dict()
        self.description['en'] = ipr.description
        self.description['fr'] = IPRItem.fr[ipr.description]
        self.url = "http://www.ebi.ac.uk/interpro/entry/{}".format(self.id)
        self.parent = ipr.parent  # subclass of (P279)
        self.children = ipr.children  # Will not add this property to wd
        self.contains = ipr.contains  # has part (P527)
        self.found_in = ipr.found_in  # part of (P361)
        self.short_name = ipr.short_name
        self.date = date
        self.version = version
        self.reference = None

        # to be created
        self.wd_item_id = None

        self.create_reference()

    def create_reference(self):
        """
        Create wikidata references for interpro

        Items:
        Q3047275: InterPro

        Properties:
        stated in (P248)
        imported from (P143)
        software version (P348)
        publication date (P577)

        """
        # This same reference will be used for everything. Except for a ref to the interpro item itself
        ref_stated_in = PBB_Core.WDItemID("Q3047275", 'P248', is_reference=True)
        ref_imported = PBB_Core.WDItemID("Q3047275", 'P143', is_reference=True)
        ref_version = PBB_Core.WDString(self.version, 'P348', is_reference=True)
        ref_date = PBB_Core.WDTime(self.date.strftime("+%Y-%m-%dT00:00:00Z"), 'P577', is_reference=True)
        ref_ipr = PBB_Core.WDString(self.id, "P2926", is_reference=True)
        self.reference = [ref_stated_in, ref_imported, ref_version, ref_date, ref_ipr]
        for ref in self.reference:
            ref.overwrite_references = True

    def create_item(self):
        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=INTERPRO, references=[self.reference]),
                      PBB_Core.WDItemID(value=IPRItem.type2subclass[self.type], prop_nr="P279",
                                        references=[self.reference])]

        item = PBB_Core.WDItemEngine(item_name=self.name, domain='interpro', data=statements, server=SERVER)

        item.set_label(self.name)
        for lang, description in self.description.items():
            item.set_description(description, lang=lang)
        item.set_aliases([self.short_name, self.id])

        try:
            item.write(login=self.login)
        except WDApiError as e:
            print(e)
            PBB_Core.WDItemEngine.log('ERROR',
                                      '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                                          main_data_id=self.id,
                                          exception_type=type(e),
                                          message=e.__str__(),
                                          wd_id=self.wd_item_id,
                                          duration=datetime.now()
                                      ))
            return

        self.wd_item_id = item.wd_item_id
        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=self.id,
            exception_type='',
            message='created/updated interpro item',
            wd_id=item.wd_item_id,
            duration=datetime.now()
        ))

    def create_relationships(self, ipr_wd):
        # ipr_wd is a dict ipr ID to wikidata ID mapping
        statements = [PBB_Core.WDExternalID(value=self.id, prop_nr=INTERPRO, references=[self.reference])]
        if self.parent:
            statements.append(
                PBB_Core.WDItemID(value=ipr_wd[self.parent], prop_nr='P279',
                                  references=[self.reference]))  # subclass of
        if self.contains:
            for c in self.contains:
                statements.append(
                    PBB_Core.WDItemID(value=ipr_wd[c], prop_nr='P527', references=[self.reference]))  # has part
        if self.found_in:
            for f in self.found_in:
                statements.append(
                    PBB_Core.WDItemID(value=ipr_wd[f], prop_nr='P361', references=[self.reference]))  # part of
        if len(statements) == 1:
            return
        # write data
        item = PBB_Core.WDItemEngine(item_name=self.name, domain='interpro', data=statements, server=SERVER,
                                     append_value=["P279", "P527", "P361"])
        try:
            item.write(self.login)
        except WDApiError as e:
            print(e)
            PBB_Core.WDItemEngine.log('ERROR',
                                      '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                                          main_data_id=self.id,
                                          exception_type=type(e),
                                          message=e.__str__(),
                                          wd_id=self.wd_item_id,
                                          duration=datetime.now()
                                      ))
            return

        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=self.id,
            exception_type='',
            message='created interpro relationships: {}'.format([(x.prop_nr, x.value) for x in statements]),
            wd_id=item.wd_item_id,
            duration=datetime.now()
        ))


def import_interpro_items(only_new=False):
    """
    Main function for doing interpro item import and building interpro relationships (to each other)
    if only_new: only insert new items
    :return:
    """
    ipr_wd = {}
    if only_new:
        ipr_wd = WDHelper().id_mapper(INTERPRO)

    d, release_info = parse_interpro_xml()
    date = release_info['date']
    version = release_info['version']

    IPRItem.login = PBB_login.WDLogin(WDUSER, WDPASS, server=SERVER)

    # Start with adding all interpro items
    ipritems = {ipr_id: IPRItem(iprdict, date, version) for ipr_id, iprdict in d.items()}

    # x = iter(ipritems.values())
    # ipritem = next(x)
    for ipritem in ipritems.values():
        if only_new and ipritem.id not in ipr_wd:
            ipritem.create_item()
        elif not only_new:
            ipritem.create_item()

    # store IPRID -> wikidata ID mapping
    ipr_wd = {iprid: ipritem.wd_item_id for iprid, ipritem in ipritems.items()}


# resume = "/logs/WD_bot_run-2016-06-24_18:55.log"
def add_parents(resume=None):
    log = set()
    if resume:
        log = set([x.split(",")[2].strip() for x in open(resume).readlines()])

    ipr_wd = WDHelper().id_mapper(INTERPRO)
    d, release_info = parse_interpro_xml()
    date = release_info['date']
    version = release_info['version']
    IPRItem.login = PBB_login.WDLogin(WDUSER, WDPASS, server=SERVER)
    ipritems = {ipr_id: IPRItem(iprdict, date, version) for ipr_id, iprdict in d.items()}
    # Add parents
    for ipritem in tqdm(ipritems.values()):
        if ipritem not in log:
            ipritem.create_relationships(ipr_wd)
    return ipr_wd


def create_protein_ipr(uniprot_id, uniprot_wdid, families, has_part, release_info, login):
    """
    Create interpro relationships to one protein
    :param uniprot_id: uniprot ID of the protein to modify
    :type uniprot_id: str
    :param uniprot_wdid: wikidata ID of the protein
    :param families: list of ipr wd ids the protein is a (P279) subclass of
    :param has_part: list of ipr wd ids the protein has (P527) has part
    :return:
    """
    date = release_info['date']
    version = release_info['version']

    # create ref
    ref_stated_in = PBB_Core.WDItemID("Q3047275", 'P248', is_reference=True)
    ref_imported = PBB_Core.WDItemID("Q3047275", 'P143', is_reference=True)
    ref_version = PBB_Core.WDString(version, 'P348', is_reference=True)
    ref_date = PBB_Core.WDTime(date.strftime("+%Y-%m-%dT00:00:00Z"), 'P577', is_reference=True)
    ref_ipr = PBB_Core.WDString("http://www.ebi.ac.uk/interpro/protein/{}".format(uniprot_id), "P854",
                                is_reference=True)
    reference = [ref_stated_in, ref_imported, ref_version, ref_date, ref_ipr]
    for ref in reference:
        ref.overwrite_references = True

    statements = []
    if families:
        for f in families:
            statements.append(PBB_Core.WDItemID(value=f, prop_nr='P279', references=[reference]))
    if has_part:
        for hp in has_part:
            statements.append(PBB_Core.WDItemID(value=hp, prop_nr='P527', references=[reference]))

    item = PBB_Core.WDItemEngine(wd_item_id=uniprot_wdid, data=statements, server=SERVER,
                                 append_value=["P279", "P527", "P361"])
    # print(item.get_wd_json_representation())
    try:
        item.write(login)
    except WDApiError as e:
        print(e)
        PBB_Core.WDItemEngine.log('ERROR',
                                  '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                                      main_data_id=uniprot_id,
                                      exception_type=type(e),
                                      message=e.__str__(),
                                      wd_id=uniprot_wdid,
                                      duration=datetime.now()
                                  ))
        return

    PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
        main_data_id=uniprot_id,
        exception_type='',
        message='created protein interpro relationships: {}'.format([(x.prop_nr, x.value) for x in statements]),
        wd_id=uniprot_wdid,
        duration=datetime.now()
    ))


def create_all_protein_interpro_human(resume=None):
    return create_all_protein_interpro("Q5", resume=resume)


def create_all_protein_interpro(taxon_wdid=None, resume=False):
    """
    Main function for creating all protein <-> interpro relationships for a particular taxon

    :param taxon_wdid: wikidata id of the taxon whoes protein to process
    :type taxon_wdid: str
    :param resume: If resume, only attempt to process proteins with no interpro annotations
    :type resume: bool
    :return:
    """
    done = set()
    if resume:
        done = get_done_prot()

    # parse the protein <-> interpro relationships
    uni_dict_f = os.path.join(DATA_DIR, "interproscan_uniprot_{}.json".format(taxon_wdid) if taxon_wdid else "interproscan_uniprot_all.json")
    if not os.path.exists(uni_dict_f):
        raise ValueError(
            "file not found: {}\nMust create interpro uniprot mapping file first. see parser.py".format(uni_dict_f))
    with open(uni_dict_f, 'r') as f:
        uni_dict = json.load(f)

    # dict of interpro ID -> wikidata ID
    ipr_wd = WDHelper().id_mapper(INTERPRO)
    # dict of uniprot ID -> wikidata ID (human)
    uniprot_wd = WDHelper().id_mapper("P352", (("P703", taxon_wdid),)) if taxon_wdid else WDHelper().id_mapper("P352")

    d, release_info = parse_interpro_xml()
    login = PBB_login.WDLogin(WDUSER, WDPASS)

    for uniprot_id in tqdm(uni_dict):
        if uniprot_id in done:
            print("skipping: {}".format(uniprot_id))
            continue
        if uniprot_id not in uniprot_wd:
            print("Warning uniprot item {} not found".format(uniprot_id))
            PBB_Core.WDItemEngine.log('WARNING', '{main_data_id}, "{ex_type}", "{message}", {wd_id}, {duration}'.format(
                main_data_id=uniprot_id,
                ex_type='',
                message="uniprot item not found in wikidata",
                wd_id="",
                duration=datetime.now()
            ))
            continue

        items = [d[x] for x in set(x['interpro_id'] for x in uni_dict[uniprot_id])]
        # Of all families, which one is the most precise? (remove families that are parents of any other family in this list)
        families = [x for x in items if x.type == "Family"]
        families_id = set(x.id for x in families)
        parents = set(family.parent for family in families)
        # A protein be in multiple families. ex: http://www.ebi.ac.uk/interpro/protein/A0A0B5J454
        specific_families = families_id - parents

        specific_families_wd = [ipr_wd[x] for x in specific_families]

        # all other items (not family) are has part (P527)
        has_part = [x.id for x in items if x.type != "Family"]
        has_part_wd = [ipr_wd[x] for x in has_part]
        for ipr_id in has_part:
            has_part_items = [x for x in uni_dict[uniprot_id] if x['interpro_id'] == ipr_id]
            # TODO add specfiic start and stop positions for each member domain
            # for example: https://www.wikidata.org/wiki/Q21097531
            # complicated example: http://www.ebi.ac.uk/interpro/protein/Q149N8

        create_protein_ipr(uniprot_id, uniprot_wd[uniprot_id], specific_families_wd, has_part_wd, release_info, login)


def test_number_of_interpro_items():
    """
    As of release 58. There should be 29,415 interpro items

    :return:
    """
    d, release_info = parse_interpro_xml()
    from SPARQLWrapper import SPARQLWrapper, JSON
    endpoint = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
    query = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/>\nSELECT * WHERE {?gene wdt:P2926 ?id}'
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    results = endpoint.query().convert()
    if not results['results']['bindings']:
        raise ValueError("No interpro items found")
    bindings = results['results']['bindings']
    if len(bindings) != len(d):
        raise ValueError("{} InterPro items expected. {} found".format(len(d), len(bindings)))


def get_done_prot():
    """Get the wd items that have a uniprot ID and are instance of a protein family or have 'has part' any type of domiain.
    Return the uniprot IDs """
    endpoint = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
    if False:
        # ?item wdt:P703 wd:Q5 .
        query = """
            PREFIX wdt: <http://www.wikidata.org/prop/direct/>
            PREFIX wd: <http://www.wikidata.org/entity/>
            select distinct ?item where { \n""" + \
                "?item wdt:P352 ?uniprot .}"
        endpoint.setQuery(query)
        endpoint.setReturnFormat(JSON)
        response = endpoint.query().convert()['results']['bindings']
        all_prots = {x['item']['value'].replace('http://www.wikidata.org/entity/', '') for x in response}

    query = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        select distinct ?uniprot where { \n""" + \
            """?item wdt:P352 ?uniprot .
             ?item wdt:P279 ?subclass .
             ?subclass wdt:P279 wd:Q417841 . }"""
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    response = endpoint.query().convert()['results']['bindings']
    family_prots = {x['uniprot']['value'] for x in response}

    query = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        select distinct ?uniprot where { \n""" + \
            """VALUES ?domain {wd:Q423026 wd:Q616005 wd:Q7644128 wd:Q898273 wd:Q898362 wd:Q3273544}
            ?item wdt:P352 ?uniprot .
             ?item wdt:P527 ?haspart .
             ?haspart wdt:P279 ?domain .}"""
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    response = endpoint.query().convert()['results']['bindings']
    domain_prots = {x['uniprot']['value'] for x in response}

    done = family_prots | domain_prots

    return done