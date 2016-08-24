from SPARQLWrapper import SPARQLWrapper, JSON
import pprint
import pandas as pd


def sparql_for_qids():
    """
    sparql query to return number of genes and proteins by species with unique taxid in WD
    :return: .csv
    """
    endpoint = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
    props = {'gene': 'P351',
             'protein': 'P352'
             }

    def execute_query(itype):
        query = '''SELECT ?species ?label ?taxid  (count (distinct ?item) as ?{}_counts)
                WHERE {{
                ?item wdt:{} ?ID ;
                wdt:P703 ?species .
                ?species wdt:P171* wd:Q10876;
                wdt:P685 ?taxid;
                rdfs:label ?label filter (lang(?label) = "en") .
                }}
                 GROUP BY ?species ?label ?taxid
                '''.format(itype, props[itype])

        endpoint.setQuery(query)
        endpoint.setReturnFormat(JSON)
        wd_query = endpoint.query().convert()
        return wd_query['results']['bindings']

    def sparql2pandas(sparql, type):
        items_list = []
        for i in sparql:
            idict = {'wd_species': i['species']['value'],
                     'taxid': i['taxid']['value'],
                     'label': i['label']['value'],
                     '{}_count'.format(type): i['{}_counts'.format(type)]['value']
                     }
            items_list.append(idict)

        return pd.DataFrame(items_list)

    genes = execute_query('gene')
    pdgenes = sparql2pandas(genes, 'gene')
    proteins = execute_query('protein')
    pdproteins = sparql2pandas(proteins, 'protein')
    joined = pd.merge(pdgenes, pdproteins, how='left',  left_on=pdgenes['taxid'], right_on=pdproteins['taxid'], sort=True)

    df1 = joined[['wd_species_x', 'label_x', 'taxid_x', 'gene_count', 'protein_count']]
    return df1.to_csv("wd_microbes_report.csv", sep="\t")



sparql_for_qids()