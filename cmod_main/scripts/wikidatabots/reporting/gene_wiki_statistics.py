import PBB_Core
import requests
import urllib
import PBB_login
import sys
import pprint
import re
import datetime
import pandas as pd

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__license__ = 'AGPLv3'

'''
This script retrieves all human genes from the Wikidata SPARQL endpoint which have links to the English Wikipedia.
Then, the Wikipedia metrics page is being queried for user access statistics. The top 10 most accessed and the pages
with the most content are then written to the Wikidata Gene Wiki portal page.
'''


def main():
    prefix = '''
    PREFIX schema: <http://schema.org/>
    PREFIX wd: <http://www.wikidata.org/entity/>
    PREFIX wdt: <http://www.wikidata.org/prop/direct/>
    '''

    query = '''
    SELECT ?entrez_id ?cid ?article ?label WHERE {
        ?cid wdt:P351 ?entrez_id .
        ?cid wdt:P703 wd:Q5 .
        OPTIONAL {
            ?cid rdfs:label ?label filter (lang(?label) = "en") .
        }
        ?article schema:about ?cid .
        ?article schema:inLanguage "en" .
        FILTER (SUBSTR(str(?article), 1, 25) = "https://en.wikipedia.org/") .
        FILTER (SUBSTR(str(?article), 1, 38) != "https://en.wikipedia.org/wiki/Template")
    }
    '''

    print(sys.argv[1])

    sparql_results = PBB_Core.WDItemEngine.execute_sparql_query(query=query, prefix=prefix)

    curr_date = datetime.datetime.now()
    end_date = datetime.date(year=curr_date.year, month=curr_date.month, day=1) - datetime.timedelta(days=1)
    start_date = datetime.date(year=end_date.year, month=end_date.month, day=1)

    total_views = 0
    from_timestamp = '{}00'.format(start_date.strftime('%Y%m%d'))
    to_timestamp = '{}00'.format(end_date.strftime('%Y%m%d'))

    all_items = list()
    gene_df = pd.DataFrame(columns=list(['Gene_name', 'page_views', 'page_size']))
    url = 'https://en.wikipedia.org/w/api.php'

    for count, i in enumerate(sparql_results['results']['bindings']):
        article = i['article']['value'].split('/')[-1]
        print(article)

        r = requests.get(url='https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/'
                             'en.wikipedia/all-access/user/{}/daily/{}/{}'.format(article, from_timestamp,
                                                                                  to_timestamp))
        article_views = 0
        gene = None

        if 'items' in r.json():

            for day in r.json()['items']:
                article_views += day['views']

            total_views += article_views

            params = {
                'action': 'query',
                'prop': 'pageprops|info',
                'titles': urllib.parse.unquote(article),
                'format': 'json'
            }

            page_size = 0
            size_results = requests.get(url=url, params=params).json()['query']['pages']
            for x in size_results.values():
                page_size = x['length']

            gene = (urllib.parse.unquote(article), article_views, page_size)
            all_items.append(gene)

            # do some printing for the user
            print(count, 'article views: ', article_views, 'total views: ', total_views,
                  'mean views: ', total_views/(count + 1), 'page size:', page_size)

            if count % 100 == 0:
                # print top accessed pages
                all_items.sort(key=lambda z: z[1], reverse=True)
                pprint.pprint(all_items[0:10])

                # print largest pages
                all_items.sort(key=lambda z: z[2], reverse=True)
                pprint.pprint(all_items[0:10])

        else:
            pprint.pprint(r.text)
            gene = (urllib.parse.unquote(article), 0, 0)
            all_items.append(gene)

        df = pd.DataFrame(data=[list(gene)], columns=['Gene_name', 'page_views', 'page_size'])
        gene_df = gene_df.append(df, ignore_index=True)

        if count % 100 == 0:
            gene_df.to_csv('gene_view_counts.csv')


    # final sort and print top accessed pages
    all_items.sort(key=lambda z: z[1], reverse=True)
    pprint.pprint(all_items[0:10])
    table_data = [all_items[0:10]]

    # print largest pages
    all_items.sort(key=lambda z: z[2], reverse=True)
    pprint.pprint(all_items[0:10])
    table_data.append(all_items[0:10])

    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1], server='en.wikipedia.org')

    # get page text
    params = {
        'action': 'query',
        'titles': 'Portal:Gene_Wiki/Quick_Links',
        'prop': 'revisions',
        'rvprop': 'content',
        'format': 'json'
    }

    page_text = [x['revisions'][0]['*']
                 for x in requests.get(url=url, params=params).json()['query']['pages'].values()][0]

    re_pattern = re.match(re.compile('^{.*?}', re.DOTALL), page_text)

    wp_string = \
        '''{{| align="right" border="1" style="text-align:center" cellpadding="0" cellspacing="0" class="wikitable"
        |+ Top Gene Wiki articles (as of {}. 1, {})
        ! Rank !! by size (word count) !! by page views in {}., {}{}
        |}}'''

    wp_table_row = '''
    |-
    |{0}
    | [[{1}]]
    | [[{2}]]'''

    tmp_string = ''
    for i in range(1, 11):
        tmp_string += wp_table_row.format(i, table_data[1][i - 1][0], table_data[0][i - 1][0])

    table_string = wp_string.format(curr_date.strftime("%B")[0:3], curr_date.year, end_date.strftime("%B")[0:3],
                                    end_date.year, tmp_string)
    print(table_string + page_text[re_pattern.end():])

    params = {
        'action': 'edit',
        'title': 'Portal:Gene_Wiki/Quick_Links',
        'section': '0',
        'text': table_string + page_text[re_pattern.end():],
        'token': login.get_edit_token(),
        'format': 'json'
    }

    r = requests.post(url=url, data=params, cookies=login.get_edit_cookie())
    pprint.pprint(r.json())

if __name__ == '__main__':
    sys.exit(main())
