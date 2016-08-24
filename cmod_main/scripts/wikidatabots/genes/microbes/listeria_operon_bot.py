import requests
import pprint
from SPARQLWrapper import SPARQLWrapper, JSON
import time
from time import strftime,gmtime
import sys
import os
import listeria_operons_store as los
import MicrobeBotWDFunctions as wdo

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login

__author__ = 'timputman'


class WDSparqlQueries(object):
    """
    params: optional depending on type of query (for qid provide prop and string, for label provide qid)
    extendable wrapper for sparql queries in WD
    """

    def __init__(self, qid=None, prop=None, string=None, taxid=None):
        self.qid = qid
        self.prop = prop
        self.string = string
        self.taxid = taxid
        self.endpoint = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
        self.wd = 'PREFIX wd: <http://www.wikidata.org/entity/>'
        self.wdt = 'PREFIX wdt: <http://www.wikidata.org/prop/direct/>'

    def execute_query(self, query):
        self.endpoint.setQuery(query)
        self.endpoint.setReturnFormat(JSON)
        return self.endpoint.query().convert()

    def wd_prop2qid(self):
        """
        :param prop: 'P351' Entrez gene id (ex. print( SPARQL_for_qidbyprop('P351','899959')))
        :param string: '899959' String value
        :return: QID Q21514037
        """
        arguments = '?gene wdt:{} "{}"'.format(self.prop, self.string)
        select_where = 'SELECT * WHERE {{{}}}'.format(arguments)
        query = self.wdt + " " + select_where
        results = self.execute_query(query)
        final_qid = []
        try:
            rawqid = results['results']['bindings'][0]['gene']['value']
            qid_list = rawqid.split('/')
            final_qid.append(qid_list[-1])
        except Exception:
            final_qid.append('None')
        return final_qid[0]

    def wd_qid2label(self):
        """
        :param string: 'Q2458943' String value
        :return: QID 'Label'
        """
        arguments = ' wd:{} rdfs:label ?label. Filter (LANG(?label) = "en") .'.format(self.qid)
        select_where = 'SELECT ?label WHERE {{{}}}'.format(arguments)
        query = self.wd + " " + select_where
        results = self.execute_query(query)
        final_qid = []
        try:
            rawqid = results['results']['bindings'][0]['label']['value']
            final_qid.append(rawqid)
        except Exception:
            final_qid.append('None')
        return final_qid[0]

    def genes4tid(self):
        query = '''SELECT ?gene ?locus_tag ?entrezid WHERE{{
                   ?gene wdt:P703 ?taxa;
                         wdt:P279 wd:Q7187;
                         wdt:P2393 ?locus_tag;
                         wdt:P351 ?entrezid.
                   ?taxa wdt:P685 '{}'.
        }}'''.format(self.taxid)

        results = self.execute_query(query)
        gene_loc_list = {}
        for result in results['results']['bindings']:
            gene_loc_list[result['entrezid']['value']] = result['gene']['value'].split('/')[-1]

        return gene_loc_list


def mygeneinfo_rest_query(taxid):
    """
    Downloads the latest list of microbial genes by taxid to a pandas dataframe
    :return: pandas data frame
    """
    url = 'http://mygene.info/v2/query/'
    params = dict(q="__all__", species=taxid, entrezonly="true", size="10000", fields="all")
    data = requests.get(url=url, params=params).json()
    # Reads mgi json hits into dataframe
    return data['hits']


def combine_resources():
    list_genes = mygeneinfo_rest_query('169963')
    wd_genes = WDSparqlQueries(taxid='169963')
    wd_qids = wd_genes.genes4tid()
    for i in list_genes:
        if i['_id'] in wd_qids.keys():
            i['wikidata'] = wd_qids[i['_id']]

    with open('/Users/timputman/wikdata_repo/notebooks/L_mono_operons.csv', 'r') as f:
        for line in f:
            line = line.strip().split(",")
            operon = line[0].rstrip()
            strand = line[1]
            if strand == '+':
                strand = 'Q22809680'
            else:
                strand = 'Q22809711'
            genes = line[2:]
            for gene in genes:
                for lgene in list_genes:
                    if gene == lgene['symbol']:
                        lgene['operon'] = {'operon': operon, 'strand': strand}
        f.close()
        return list_genes


ops = combine_resources()
#pprint.pprint(ops)
genestot = len(ops)
count = 0
reference = [PBB_Core.WDString(value='19448609', prop_nr='P698', is_reference=True),
             PBB_Core.WDTime(str(strftime("+%Y-%m-%dT00:00:00Z", gmtime())), prop_nr='P813', is_reference=True)
             ]
for ref in reference:
    ref.overwrite_references = True

login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])
for gene in ops:
    statements = []
    if 'locus_tag' in gene.keys():
        item_name = '{}    {}'.format(gene['name'], gene['locus_tag'])

        if 'operon' in gene.keys():
            count += 1
            if count > 640:
                wd_operon = los.listeria_operons[gene['operon']['operon']].rstrip()
                print(wd_operon)

                statements.append(PBB_Core.WDString(prop_nr='P351', value=gene['_id'], references=[reference]))
                statements.append(PBB_Core.WDItemID(prop_nr='P361', value=wd_operon, references=[reference]))

                start = time.time()
                try:
                    wd_item_gene = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=statements,
                                                         use_sparql=True)
                    #pprint.pprint(wd_item_gene.get_wd_json_representation())
                    wd_item_gene.write(login=login)
                    new_mgs = ''
                    # log actions to log file
                    if wd_item_gene.create_new_item:
                        new_mgs = ': New item'
                    PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=gene['_id'],
                        exception_type='',
                        message='success{}'.format(new_mgs),
                        wd_id=wd_item_gene.wd_item_id,
                        duration=time.time() - start
                    ))
                    print('success', str(count)+'/'+ str(genestot))

                except Exception as e:
                    print(e)
                    PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=gene['_id'],
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='',
                        duration=time.time() - start
                    ))

                end = time.time()
                print('Time elapsed:', end - start)
