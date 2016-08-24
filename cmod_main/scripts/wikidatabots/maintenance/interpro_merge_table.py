"""
Create a table of interpro items and wikipedia pages that are probably (possibly?) about those items,
for the purpose of helping people review and merge those items
https://www.wikidata.org/wiki/User:ProteinBoxBot/Interpro_merge

Greg Stupp Jul 18, 2016
"""

import itertools
from collections import defaultdict

import pandas as pd
import requests
from SPARQLWrapper import SPARQLWrapper, JSON

from interproscan.WDHelper import WDHelper


def pd_to_table(df):
    # quick n dirty pandas DataFrame to mediawikitable converter
    """{| border="1" class="dataframe"
        |- style="text-align: right;"
        !
        ! Article Name!! wikidata ID!! InterPro Items!! InterPro WDIDs!! About Gene!! Done
        |-
        ! 0
        |[[:en:Tetratricopeptide|Tetratricopeptide]]||[[Q7706768]]||[www.ebi.ac.uk/interpro/entry/IPR001440 IPR001440]||[[Q24779822]]||False||False
        |-
        ! 1
        |[[:en:UDP-N-acetylglucosamine 2-epimerase|UDP-N-acetylglucosamine 2-epimerase]]||[[Q13411653]]||[www.ebi.ac.uk/interpro/entry/IPR003331 IPR003331]||[[Q24721922]]||False||False
        |-
        ! 2
        |[[:en:Motilin|Motilin]]||[[Q126440]]||[www.ebi.ac.uk/interpro/entry/IPR006738 IPR006738]||[[Q24772416]]||False||False
        |-
        ! 3
        |[[:en:Contryphan|Contryphan]]||[[Q3689200]]||[www.ebi.ac.uk/interpro/entry/IPR011062 IPR011062]||[[Q24738476]]||False||False
        |}
    """
    out = "{| border='1' class='wikitable sortable table-yes table-no' style='text-align: left;'\n!\n"
    out += '!'.join(['! {}'.format(x) for x in list(df.columns)])
    for record in df.to_records():
        record = tuple(record)
        out += "\n|-\n"
        out += "! " + str(record[0]) + '\n'
        out += '|'.join(['|{}'.format(x) for x in record[1:]])
    out += "\n|}"
    return out


def grouper(n, iterable):
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return
        yield chunk


def get_wiki_id_from_title(titles):
    result = dict()
    titlegrouper = grouper(50, titles)
    for titlegroup in titlegrouper:
        titlegroup = [x for x in titlegroup if x]
        url = "https://en.wikipedia.org/w/api.php?action=query&prop=pageprops&ppprop=wikibase_item&format=json&titles={}".format(
            "|".join(titlegroup))
        response = requests.get(url).json()['query']['pages']
        for x in response.values():
            if 'pageprops' not in x:
                print("page not found: {}".format(x['title']))
        result.update({x['title']: x['pageprops']['wikibase_item'] for x in response.values() if 'pageprops' in x})
    return result


def make_table():
    # Make a wikipedia table containing all of these links and ask the community to help

    # Use dbpedia to look up every article with an interpro property.
    url = "http://dbpedia.org/sparql/?default-graph-uri=http%3A%2F%2Fdbpedia.org&query=++++select+%3Farticle+%3Fipr+%3Fen+%3Ftitle+where+%7B%0D%0A++++%3Farticle+dbp%3Ainterpro+%3Fipr+.%0D%0A++++%3Farticle+foaf%3AisPrimaryTopicOf+%3Fen+.%0D%0A++++%3Farticle+rdfs%3Alabel+%3Ftitle%0D%0Afilter+langMatches%28+lang%28%3Ftitle%29%2C+%22EN%22+%29++++%7D&format=json&CXML_redir_for_subjs=121&CXML_redir_for_hrefs=&timeout=30000&debug=on"
    response = requests.get(url).json()
    results = response['results']['bindings']
    article2ipr = defaultdict(set)
    for result in results:
        article2ipr[result['title']['value']].add(result['ipr']['value'])

    # If an article has more than 4 interpro links in it, skip it
    article2ipr = {k: v for k, v in article2ipr.items() if len(v) <= 4}

    # get wikidata id of items for each article
    wiki2wdid = get_wiki_id_from_title(article2ipr.keys())

    # Filter out any items with a entrez id (P351), or HGNC (P354), or transcript id (P704), or uniprotid (P352)
    wdgrouper = grouper(200, ["wd:" + x for x in wiki2wdid.values()])
    response = []
    for wdgroup in wdgrouper:
        endpoint = SPARQLWrapper("https://query.wikidata.org/bigdata/namespace/wdq/sparql")
        query = """
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wd: <http://www.wikidata.org/entity/>
        select * where { """ + \
                "values ?wd {" + " ".join(wdgroup) + "}" + \
                """\nFILTER NOT EXISTS { ?wd wdt:P351 ?x }
                FILTER NOT EXISTS { ?wd wdt:P352 ?x }
                FILTER NOT EXISTS { ?wd wdt:P354 ?x }
                FILTER NOT EXISTS { ?wd wdt:P704 ?x }}"""
        endpoint.setQuery(query)
        endpoint.setReturnFormat(JSON)
        response.extend(endpoint.query().convert()['results']['bindings'])
    wditems = {x['wd']['value'].replace('http://www.wikidata.org/entity/', '') for x in response}

    # These (150) items are about the gene
    gene_items = set(wiki2wdid.values()) - wditems

    # Need the wikidata IDs for the interpro items
    ipr_wd = WDHelper().id_mapper("P2926")

    # Get the names of each interpro item
    query = """SELECT ?a ?itemLabel WHERE
    {	?item <http://www.wikidata.org/prop/direct/P2926> ?a
    SERVICE wikibase:label { bd:serviceParam wikibase:language "en" } }"""
    endpoint.setQuery(query)
    endpoint.setReturnFormat(JSON)
    response = endpoint.query().convert()['results']['bindings']
    ipr_names = {x['a']['value'].replace('http://www.wikidata.org/entity/', ''): x['itemLabel']['value'] for x in response}

    # Build a dataframe
    # [[:en:Death_domain|Death_domain]]
    an = pd.Series(['[[:en:{x}|{x}]]'.format(x=x) for x in article2ipr.keys()], name="Article Name")
    df = pd.DataFrame(an)
    wdid = pd.Series([wiki2wdid.get(x, '') for x in article2ipr.keys()])
    df['wikidata ID'] = ['[[{}]]'.format(x) for x in wdid]
    # [www.ebi.ac.uk/interpro/entry/IPR000455 IPR000455]
    df['InterPro Items'] = [
        ', '.join(['[http://www.ebi.ac.uk/interpro/entry/{iprid} {iprid}]'.format(iprid=iprid) for iprid in x]) for x in
        article2ipr.values()]
    df['InterPro WDIDs'] = [', '.join(['[[{wdid}]]'.format(wdid=ipr_wd.get(iprid, '')) for iprid in x]) for x in
                            article2ipr.values()]
    df['AboutGene'] = wdid.isin(gene_items)

    df['Same Name'] = [article_name.lower() == ipr_names.get(list(ipr)[0], '').lower() if len(ipr) == 1 else False for article_name, ipr in article2ipr.items() ]

    # For each article's wdid, we want to see if its already been merged. As in, does it have an IPR ID property already
    df['merged'] = wdid.map(lambda x:x in ipr_wd.values())

    # This will be for people to fill in
    df['status'] = df.merged.map(lambda x:"done" if x else "")

    # Remove the "about gene" items from table
    df = df.query("AboutGene == False")
    del df['AboutGene']
    df.index = range(len(df))

    with open("table.md", 'w') as f:
        f.write(pd_to_table(df))
    with open("table.html", 'w') as f:
        f.write(df.to_html())


if __name__ == "__main__":
    make_table()