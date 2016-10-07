from SPARQLWrapper import SPARQLWrapper, JSON
from time import gmtime, strftime
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core


__author__ = 'timputman'

#can be done with wd_item engine  :to get label enter wd_item_engine(wditemid = Qxxxx).getLabel()
class WDSparqlQueries(object):
    """
    params: optional depending on type of query (for qid provide prop and string, for label provide qid)
    extendable wrapper for sparql queries in WD
    """
    def __init__(self, qid=None, prop=None, string=None):
        self.qid = qid
        self.prop = prop
        self.string = string
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

    def wd_qid2property(self):
        """
        :param string: 'Q2458943' String value
        :return: "property value'
        """
        arguments = ' wd:{} wdt:{} ?prop.'.format(self.qid, self.prop)
        select_where = 'SELECT ?prop WHERE {{{}}}'.format(arguments)
        query = self.wd + " " + select_where
        results = self.execute_query(query)
        final_qid = []
        try:
            rawqid = results['results']['bindings'][0]['prop']['value']
            final_qid.append(rawqid)
        except Exception:
            final_qid.append('None')
        return final_qid[0].split("/")[-1]



def reference_store(source='', identifier=''):
    """
    :param source: database source to be referenced (key name from source_qids)
    :param ref_type: type of WD reference statement (imported from, stated in) (key names from prop_ids)
    :return: PBB_Core reference object for database source
    """
    source_items = {'uniprot': 'Q905695',
                    'ncbi_gene': 'Q20641742',
                    'ncbi_taxonomy': 'Q13711410',
                    'swiss_prot': 'Q2629752',
                    'trembl': 'Q22935315'}

    prop_ids = {'uniprot': 'P352',
                'ncbi_gene': 'P351',
                'ncbi_taxonomy': 'P685',
                'ncbi_locus_tag': 'P2393'
                }
    refs = [PBB_Core.WDItemID(value=source_items[source], prop_nr='P248', is_reference=True),
            PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),
            PBB_Core.WDString(value=identifier, prop_nr=prop_ids[source], is_reference=True),
            PBB_Core.WDTime(str(strftime("+%Y-%m-%dT00:00:00Z", gmtime())), prop_nr='P813', is_reference=True)
            ]
    for ref in refs:
        ref.overwrite_references = True
    return refs




