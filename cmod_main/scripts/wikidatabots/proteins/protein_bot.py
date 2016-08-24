import xml.etree.ElementTree as Et
import requests
import requests_ftp
import sys
import os
import gzip
import PBB_Core
import PBB_login
import pprint
import time
import json
import copy
import traceback
import argparse


class ProteinBot(object):
    taxon_map = {
        '9606': 'Q5',
        '10090': 'Q83310'
    }

    descr_map = {
        '9606': {
            'en': 'human protein',
        },
        '10090': {
            'en': 'mouse protein'
        }
    }

    # instance of Gene Ontology Evidence code (Q23173209)
    go_evidence_codes = {
        'EXP': 'Q23173789',
        'IDA': 'Q23174122',
        'IPI': 'Q23174389',
        'IMP': 'Q23174671',
        'IGI': 'Q23174952',
        'IEP': 'Q23175251',
        'ISS': 'Q23175558',
        'ISO': 'Q23190637',
        'ISA': 'Q23190738',
        'ISM': 'Q23190825',
        'IGC': 'Q23190826',
        'IBA': 'Q23190827',
        'IBD': 'Q23190833',
        'IKR': 'Q23190842',
        'IRD': 'Q23190850',
        'RCA': 'Q23190852',
        'TAS': 'Q23190853',
        'NAS': 'Q23190854',
        'IC': 'Q23190856',
        'ND': 'Q23190857',
        'IEA': 'Q23190881',
        'IMR': 'Q23190842'
    }

    def __init__(self, uniprot, base_map, pdb_to_go, go_prop_map, login, progress):
        self.uniprot = uniprot
        self.uniprot_qid = base_map[uniprot]['qid']
        self.ensp = set()
        self.ncbip = set()
        self.go_terms = set()
        self.login = login
        self.go_prop_map = go_prop_map
        self.entrez = base_map[uniprot]['entrez']['id']
        self.entrez_quid = base_map[uniprot]['entrez']['qid']
        self.res_id = base_map[uniprot]['entrez']['res_id']

        self.label = ''
        self.description = ''
        self.aliases = set()
        self.tax_id = ''
        self.annotation_type = ''

        self.statements = []

        self.res_prefixes = {x.split(':')[0] for x in res_id_to_entrez_qid}

        start = time.time()

        if not os.path.exists('./data/uniprot_raw'):
            os.makedirs('./data/uniprot_raw')

        # check if Uniprot xml exists and its age?
        r = requests.get('http://www.uniprot.org/uniprot/{}.xml'.format(self.uniprot))

        f = open('./data/uniprot_raw/{}.xml'.format(self.uniprot), 'w')
        f.write(r.text)
        f = open('./data/uniprot_raw/{}.xml'.format(self.uniprot), 'r')

        # check if XML can be properly parsed, log obsolete items for permanent removal.
        try:
            for event, e in Et.iterparse(f, events=('start', 'end')):

                if event == 'end' and e.tag == '{http://uniprot.org/uniprot}entry':
                    if 'dataset' in e.attrib:
                        self.annotation_type = e.attrib['dataset']

                if event == 'end' and e.tag == '{http://uniprot.org/uniprot}protein':
                    tmp = e.find('./{http://uniprot.org/uniprot}recommendedName/'
                                 '{http://uniprot.org/uniprot}fullName')
                    if tmp is not None:
                        self.label = tmp.text
                    elif e.find('./{http://uniprot.org/uniprot}submittedName/'
                                '{http://uniprot.org/uniprot}fullName') is not None:
                        self.label = e.find('./{http://uniprot.org/uniprot}submittedName/'
                                            '{http://uniprot.org/uniprot}fullName').text

                    for prop in e.findall('./{http://uniprot.org/uniprot}alternativeName/'):
                        self.aliases.add(prop.text)

                if event == 'end' and e.tag == '{http://uniprot.org/uniprot}organism':
                    for prop in e.findall('./{http://uniprot.org/uniprot}dbReference'):
                        if prop.attrib['type'] == 'NCBI Taxonomy':
                            self.tax_id = prop.attrib['id']

                # print(e)
                if event == 'end' and e.tag == '{http://uniprot.org/uniprot}dbReference' \
                        and 'type' in e.attrib and e.attrib['type'] == 'Ensembl':

                    for prop in e.findall('./{http://uniprot.org/uniprot}property'):
                        if prop.attrib['type'] == 'protein sequence ID':
                            self.ncbip.add(prop.attrib['value'])
                            self.statements.append(PBB_Core.WDString(value=prop.attrib['value'], prop_nr='P705',
                                                                     references=[self.create_reference()]))

                if event == 'end' and e.tag == '{http://uniprot.org/uniprot}dbReference' \
                        and 'type' in e.attrib and e.attrib['type'] == 'RefSeq':
                    self.ncbip.add(e.attrib['id'])
                    self.statements.append(PBB_Core.WDString(value=e.attrib['id'], prop_nr='P637',
                                                             references=[self.create_reference()]))

                # get alternative identifiers for gene to protein mapping
                if event == 'end' and e.tag == '{http://uniprot.org/uniprot}dbReference' \
                        and 'type' in e.attrib and e.attrib['type'] in self.res_prefixes:
                    res_id = e.attrib['id']
                    if res_id in res_id_to_entrez_qid:
                        self.entrez_quid = res_id_to_entrez_qid[res_id][0]

        except Et.ParseError as e:
            print('Error when parsing Uniprot {} XML file, item {} most likely obsolete'.format(self.uniprot,
                                                                                                self.uniprot_qid))
            PBB_Core.WDItemEngine.log(
                'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                    .format(
                        main_data_id='{}'.format(self.uniprot),
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id=self.uniprot_qid,
                        duration=time.time() - start
                    ))
            return

        # get GO annotations from QuickGO
        params = {
            'format': 'tsv',
            'limit': '1000',
            'protein': self.uniprot
        }

        url = 'http://www.ebi.ac.uk/QuickGO/GAnnotation'

        try:
            itrt = iter(requests.get(url, params=params).text.strip('\n ').split('\n'))
            next(itrt)  # skip header line

            for line in itrt:
                cols = line.split('\t')
                go_id = cols[6]
                evidence_code = cols[9]
                go_aspect = cols[11][0]

                if self.uniprot not in pdb_to_go:
                    pdb_to_go[self.uniprot] = {
                        'go_terms': list(),
                        'evidence': list(),
                        'pdb': set()
                    }

                pdb_to_go[self.uniprot]['go_terms'].append(go_id)
                pdb_to_go[self.uniprot]['evidence'].append(evidence_code)

                if go_id in go_prop_map:
                    go_prop_map[go_id]['go_class_prop'] = ProteinBot.get_go_class(go_id, go_aspect)
        except requests.HTTPError:
            pass
        except IndexError:
            pass

        # set description according to the annotation the Uniprot entry is coming from
        self.description = self.descr_map[self.tax_id]['en']

        if self.annotation_type == 'TrEMBL':
            self.description += ' (annotated by UniProtKB/TrEMBL {})'.format(self.uniprot)
        elif self.annotation_type == 'Swiss-Prot':
            self.description += ' (annotated by UniProtKB/Swiss-Prot {})'.format(self.uniprot)

        # assign a GO term a GO subontology/OBO namespace
        if self.uniprot in pdb_to_go:
            for go in set(pdb_to_go[self.uniprot]['go_terms']):
                # check if a GO term is not yet in Wikidata
                # TODO: If a GO term is not in Wikidata, trigger OBO bot to add it
                if go not in go_prop_map:
                    PBB_Core.WDItemEngine.log(
                        'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                            .format(
                                main_data_id='{}'.format(self.uniprot),
                                exception_type='GO term not in Wikidata exception',
                                message='GO term {} not found in Wikidata, skipping this one'.format(go),
                                wd_id=self.uniprot_qid,
                                duration=time.time() - start
                            ))
                    print('GO term {} not found in Wikidata, skipping this one'.format(go))
                    continue

                # search in the EBI OBO Lookup Service, for the rare case a GO term has not been assigned its class
                if not go_prop_map[go]['go_class_prop']:
                    go_class_prop = ProteinBot.get_go_class(go)
                    if not go_class_prop:
                        continue

                    go_prop_map[go]['go_class_prop'] = go_class_prop
                    print('added class code {} to {}'.format(go_prop_map[go]['go_class_prop'], go))

                # create a set of WD QIDs representing GO evidence code items in WD
                evidence = {self.go_evidence_codes[ev] for count, ev in enumerate(pdb_to_go[self.uniprot]['evidence'])
                            if pdb_to_go[self.uniprot]['go_terms'][count] == go}

                # iterate though the evidence code set and create a new qualifier for each one
                qualifiers = [PBB_Core.WDItemID(value=ev, prop_nr='P459', is_qualifier=True) for ev in evidence if ev]

                # Create Wikidata GO term value
                prop_nr = self.go_prop_map[go]['go_class_prop']
                qid = self.go_prop_map[go]['qid']
                self.statements.append(PBB_Core.WDItemID(value=qid, prop_nr=prop_nr, qualifiers=qualifiers,
                                                         references=[self.create_reference()]))

            for pdb in pdb_to_go[self.uniprot]['pdb']:
                self.statements.append(PBB_Core.WDString(value=pdb.upper(), prop_nr='P638',
                                                         references=[self.create_reference()]))

        self.statements.append(PBB_Core.WDItemID(value='Q8054', prop_nr='P279', references=[self.create_reference()]))

        if self.entrez_quid != '':
            self.statements.append(PBB_Core.WDItemID(value=self.entrez_quid, prop_nr='P702',
                                                     references=[self.create_reference()]))

        current_taxonomy_id = self.taxon_map[self.tax_id]
        self.statements.append(PBB_Core.WDItemID(value=current_taxonomy_id, prop_nr='P703',
                                                 references=[self.create_reference()]))
        self.statements.append(PBB_Core.WDString(value=self.uniprot, prop_nr='P352',
                                                 references=[self.create_reference()]))

        # remove all Wikidata properties where no data has been provided, but are handled by the bot
        all_stmnt_props = list(map(lambda x: x.get_prop_nr(), self.statements))
        for pr in ['P680', 'P681', 'P682', 'P705', 'P637', 'P702']:
            if pr not in all_stmnt_props:
                self.statements.append(PBB_Core.WDBaseDataType.delete_statement(prop_nr=pr))

        try:
            new_msg = ''
            if self.uniprot_qid != '':
                wd_item = PBB_Core.WDItemEngine(wd_item_id=self.uniprot_qid, domain='proteins', data=self.statements)
            else:
                wd_item = PBB_Core.WDItemEngine(item_name=self.label, domain='proteins', data=self.statements)
                new_msg = 'new protein created'

            wd_item.set_label(self.label)
            wd_item.set_description(self.description)
            wd_item.set_aliases(aliases=self.aliases, append=False)

            self.uniprot_qid = wd_item.write(self.login)

            if self.entrez_quid != '':
                encodes = PBB_Core.WDItemID(value=self.uniprot_qid, prop_nr='P688',
                                            references=[self.create_reference()])
                gene_item = PBB_Core.WDItemEngine(wd_item_id=self.entrez_quid, data=[encodes], append_value=['P688'])
                gene_item.write(login)

            progress[self.uniprot] = self.uniprot_qid

            PBB_Core.WDItemEngine.log(
                'INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                    .format(
                        main_data_id='{}'.format(self.uniprot),
                        exception_type='',
                        message='success{}'.format(new_msg),
                        wd_id=self.uniprot_qid,
                        duration=time.time() - start
                    ))

            # pprint.pprint(wd_item.get_wd_json_representation())
        except Exception as e:
            print(e)

            PBB_Core.WDItemEngine.log(
                'ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'
                    .format(
                        main_data_id='{}'.format(self.uniprot),
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id=self.uniprot_qid,
                        duration=time.time() - start
                    ))
            traceback.print_exc()

        print(self.label)
        print(self.aliases)
        print(self.tax_id)

    def create_reference(self):
        first_ref = PBB_Core.WDItemID(value='Q905695', prop_nr='P248', is_reference=True)
        first_ref.overwrite_references = True
        return [
            first_ref,
            PBB_Core.WDString(value=self.uniprot, prop_nr='P352', is_reference=True),
            PBB_Core.WDTime(time=time.strftime('+%Y-%m-%dT00:00:00Z', time.gmtime()), prop_nr='P813',
                            is_reference=True),
            PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
        ]

    @staticmethod
    def get_go_class(go_term, class_letter=None):
        go_classes = {'P': 'P682', 'F': 'P680', 'C': 'P681'}

        if class_letter:
            return go_classes[class_letter]

        base_url = 'http://www.ebi.ac.uk/ols/beta/api/ontologies/go/terms/'
        base_url += 'http%253A%252F%252Fpurl.obolibrary.org%252Fobo%252F{}'.format(go_term.replace(':', '_'))

        headers = {
            'Accept': 'application/json'
        }

        r = requests.get(base_url, headers=headers)

        go_json = r.json()

        valid_namespaces = {
            'biological_process': 'P682',
            'molecular_function': 'P680',
            'cellular_component': 'P681'
        }

        for x in valid_namespaces:
            try:
                if x in go_json['annotation']['has_obo_namespace']:
                    return valid_namespaces[x]
            except KeyError:
                print('No GO subclass defined for this GO term in OLS, returning None')

        return None


def main():

    def read_file(url):
        if not os.path.exists('./data'):
            os.makedirs('./data')

        file_name = url.split('/')[-1]
        file_path = './data/{}'.format(file_name)

        if not read_local or not os.path.isfile(file_path):
            requests_ftp.monkeypatch_session()
            s = requests.Session()

            if url.startswith('ftp://'):
                reply = s.retr(url, stream=True)
            else:
                reply = s.get(url, stream=True)

            with open(file_path, 'wb') as f:
                for chunk in reply.iter_content(chunk_size=2048):
                    if chunk:
                        f.write(chunk)
                        f.flush()

        if file_name.endswith('.gz'):
            f = gzip.open(file_path, 'rt')
        else:
            f = open(file_path, 'rt')

        cnt = 0
        while f:

            line = f.readline()
            if line is None or line == '':
                break

            cnt += 1
            if cnt % 100000 == 0:
                print('count: ', cnt)

            yield line

    def get_uniprot_for_entrez():
        # query WD for all entrez IDs (eukaryotic)
        # query Uniprot for all high quality annotated Uniprots based on the entrez id.

        query = '''
        SELECT * WHERE {
            ?gene wdt:P351 ?entrez .
            {?gene wdt:P703 wd:Q5}
            UNION {?gene wdt:P703 wd:Q83310} .
            {?gene wdt:P354 ?res_id}
            UNION {?gene wdt:P671 ?res_id} .
        }
        '''

        results = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

        entrez_to_qid = dict()
        global res_id_to_entrez_qid
        res_id_to_entrez_qid = dict()

        for z in results:
            # ensure that the correct prefix exists so the identifier can be found in the Uniprot XML file
            res_id = z['res_id']['value']
            entrez_qid = z['gene']['value'].split('/')[-1]
            entrez_id = z['entrez']['value']
            if len(res_id.split(':')) <= 1:
                res_id = 'HGNC:' + z['res_id']['value']

            entrez_to_qid[entrez_id] = (entrez_qid, res_id)
            res_id_to_entrez_qid.update({res_id: (entrez_qid, entrez_id)})

        print('Wikidata Entrez query complete')

        uniprot_to_qid = get_all_wd_uniprots()
        print('Wikidata Uniprot query complete')

        up_prefix = '''
        PREFIX taxon:<http://purl.uniprot.org/taxonomy/>
        PREFIX up:<http://purl.uniprot.org/core/>
        PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        '''

        headers = {
            'content-type': 'application/sparql-results+json',
            'charset': 'utf-8'
        }

        up_query = '''
        SELECT DISTINCT * WHERE {
            ?uniprot rdfs:seeAlso ?gene .
            ?uniprot up:reviewed ?reviewed .
            {?uniprot up:organism taxon:9606}
            UNION {?uniprot up:organism taxon:10090} .

            FILTER regex(?gene, "^http://purl.uniprot.org/geneid/")
        }
        GROUP BY ?uniprot ?gene ?reviewed
        '''

        query_string = up_prefix + up_query

        data = {
            'format': 'srj',
            'query': query_string
        }

        if read_local and os.path.isfile('uniprot_entrez_map.json'):
            with open('uniprot_entrez_map.json', 'r') as f:
                results = json.load(f)
        else:
            reply = requests.post(url='http://sparql.uniprot.org/sparql/', params=data, headers=headers)
            results = reply.json()

            with open('uniprot_entrez_map.json', 'w') as of:
                json.dump(results, of)

        print('Uniprot query complete')
        uniprot_map = dict()

        for ids in results['results']['bindings']:
            entrez_id = ids['gene']['value'].split('/')[-1]
            uniprot_id = ids['uniprot']['value'].split('/')[-1]

            reviewed = False
            if ids['reviewed']['value'] == 'true':
                reviewed = True

            if reviewed or (not reviewed and uniprot_id in uniprot_to_qid):
                if entrez_id not in entrez_to_qid:
                    print('Entrez ID {} not in Wikidata'.format(entrez_id))
                    continue

                if uniprot_id not in uniprot_to_qid:
                    protein_qid = ''
                else:
                    protein_qid = uniprot_to_qid[uniprot_id]

                uniprot_map[uniprot_id] = {
                    'entrez': {
                        'id': entrez_id,
                        'qid': entrez_to_qid[entrez_id][0],
                        'res_id': entrez_to_qid[entrez_id][1]
                    },
                    'qid': protein_qid
                }

        # Uniprot items in WD without a link to a gene should also be updated, therefore add them to uniprot_map,
        # keep entrez empty.
        for wd_protein_item in uniprot_to_qid:
            if wd_protein_item not in uniprot_map:
                uniprot_map[wd_protein_item] = {
                    'entrez': {
                        'id': '',
                        'qid': '',
                        'res_id': ''
                    },
                    'qid': uniprot_to_qid[wd_protein_item]
                }

        return uniprot_map

    def get_all_wd_uniprots():
        query = '''
        SELECT * WHERE {
            ?protein wdt:P352 ?uniprot .
            {?protein wdt:P703 wd:Q5}
            UNION {?protein wdt:P703 wd:Q83310} .
        }
        '''

        results = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

        return {z['uniprot']['value']: z['protein']['value'].split('/')[-1] for z in results}

    def get_go_map():
        query = '''
        SELECT * WHERE {
            ?qid wdt:P686 ?go .
        }
        '''

        results = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

        go_to_qid = dict()
        for z in results:
            go_to_qid[z['go']['value']] = {
                'qid': z['qid']['value'].split('/')[-1],
                'go_class_prop': ''

            }

        return go_to_qid

    def get_pdb_to_uniprot():
        file = 'ftp://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/csv/uniprot_pdb.csv.gz'

        pdb_uniprot_map = dict()

        for c, line in enumerate(read_file(file)):
            if c < 2:
                print(line)
                continue

            dt = line.strip('\n').split(',')

            if dt[0] not in pdb_uniprot_map:
                pdb_uniprot_map[dt[0]] = dt[1].split(';')

        return pdb_uniprot_map

    def const_go_map():
        base_dict = {
            'go_terms': list(),
            'evidence': list(),
            'pdb': set()
        }

        file = 'ftp://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/csv/pdb_chain_go.csv.gz'

        pdb_go_map = dict()

        for c, line in enumerate(read_file(file)):
            if c < 2:
                print(line)
                c += 1
                continue

            dt = line.strip('\n').split(',')
            uniprot = copy.copy(dt[2])

            if uniprot not in base_map:
                continue

            if uniprot not in pdb_go_map:
                pdb_go_map[uniprot] = copy.deepcopy(base_dict)

            pdb_go_map[uniprot]['go_terms'].append(dt[-1])
            pdb_go_map[uniprot]['evidence'].append(dt[-2])

            pdb_go_map[uniprot]['pdb'].add(dt[0])

        print('total number of PDBs', len(pdb_go_map))

        pdb_to_uniprot = get_pdb_to_uniprot()
        for uniprot in pdb_to_uniprot:
            if uniprot in pdb_go_map:
                pdb_go_map[uniprot]['pdb'].update(pdb_to_uniprot[uniprot])
            else:
                pdb_go_map[uniprot] = copy.deepcopy(base_dict)
                pdb_go_map[uniprot]['pdb'] = set(pdb_to_uniprot[uniprot])

        entrez_to_uniprot = {base_map[z]['entrez']['id']: z for z in base_map if base_map[z]['entrez']['id']}

        # Download and process latest human and mouse GO term annotation files
        files = [
            'http://geneontology.org/gene-associations/gene_association.goa_human.gz',
            'http://geneontology.org/gene-associations/gene_association.mgi.gz'
        ]

        for file in files:
            for line in read_file(file):
                if line.startswith('!'):
                    continue

                cols = line.split('\t')
                uniprot = cols[1]
                go_id = cols[4]
                evidence = cols[6]
                go_class = cols[8]

                if cols[0] == 'MGI':
                    try:
                        mgi = cols[1]
                        entrez = res_id_to_entrez_qid[mgi][1]
                        uniprot = entrez_to_uniprot[entrez]
                    except KeyError:
                        continue

                if uniprot not in pdb_go_map:
                    pdb_go_map[uniprot] = copy.deepcopy(base_dict)

                pdb_go_map[uniprot]['go_terms'].append(go_id)
                pdb_go_map[uniprot]['evidence'].append(evidence)

                try:
                    go_prop_map[go_id]['go_class_prop'] = ProteinBot.get_go_class(go_id, go_class)
                except KeyError:
                    print('GO term {} not yet in Wikidata'.format(go_id))
                    continue

        return pdb_go_map

    parser = argparse.ArgumentParser(description='ProteinBot parameters')
    parser.add_argument('--run-locally', action='store_true', help='Locally stored data files and run progress '
                                                                   'will be used. Acts also as if continuing a run.')
    parser.add_argument('--user', action='store', help='Username on Wikidata', required=True)
    parser.add_argument('--pwd', action='store', help='Password on Wikidata', required=True)
    args = parser.parse_args()

    read_local = args.run_locally

    login = PBB_login.WDLogin(user=args.user, pwd=args.user)

    # generate a basic mapping of Uniprot to Entrez and Wikidata genes and proteins
    base_map = get_uniprot_for_entrez()

    # generate mappings of GO terms to their Wikidata QIDs
    go_prop_map = get_go_map()

    # generate a map of Uniprot IDs with the matches PDB IDs, GO term and GO evidence codes
    pdb_to_go = const_go_map()

    if read_local and os.path.isfile('uniprot_progress.json'):
        with open('uniprot_progress.json', 'r') as infile:
            progress = json.load(infile)
    else:
        progress = dict()

    for count, x in enumerate(base_map):
        if x in progress:
            continue

        pprint.pprint(x)
        pprint.pprint(base_map[x])
        ProteinBot(uniprot=x, base_map=base_map, pdb_to_go=pdb_to_go, go_prop_map=go_prop_map, login=login,
                   progress=progress)

        with open('uniprot_progress.json', 'w') as outfile:
                json.dump(progress, outfile)

if __name__ == '__main__':
    sys.exit(main())
