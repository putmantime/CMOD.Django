import PBB_Core
import PBB_login
import pprint
import requests
import sys
import time

__author__ = 'Sebastian Burgstaller'
__license__ = 'AGPLv3'

"""
This script executes a SPARQL query and based on that looks for human genes which could match, it displays the whole
item and prompts whether the users wants to merge or do a different action. This allows to quickly find, clean and merge
many items
"""

prop_store = dict()


def lookup_symbol(symbol):
    query = '''
        SELECT ?gene WHERE {{
          ?gene wdt:P353 '{}' .

        }}
    '''.format(symbol)

    r = PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']

    for z in r:
        return z['gene']['value'].split('/')[-1]

    return None


def extract_sitelinks(sitelink_dict):
    base_url = 'https://{}.wikipedia.org/wiki/{}\n\t'
    sitelink_string = ''
    for wiki in sitelink_dict:
        lang = wiki[0:-4]
        title = sitelink_dict[wiki]['title']
        sitelink_string += base_url.format(lang, title)

    return sitelink_string


def print_item(qid):
    wd_item = PBB_Core.WDItemEngine(wd_item_id=qid, use_sparql=True)
    label = wd_item.get_label()
    description = wd_item.get_description()
    aliases = wd_item.get_aliases()
    sitelinks_string = extract_sitelinks(wd_item.get_wd_json_representation()['sitelinks'])

    statement_print = ''

    for stmt in wd_item.statements:
        # retrieve English prop label and store in prop_label dict to minimize traffic
        prop_nr = stmt.get_prop_nr()
        prop_label = ''
        if prop_nr not in prop_store:
            prop_item = PBB_Core.WDItemEngine(wd_item_id=prop_nr)
            prop_label = prop_item.get_label()
            prop_store[prop_nr] = prop_label
        else:
            prop_label = prop_store[prop_nr]

        item_label = stmt.get_value()
        item_id = ''
        if isinstance(stmt, PBB_Core.WDItemID):
            item_id = item_label
            # print(item_id)
            item = PBB_Core.WDItemEngine(wd_item_id='Q{}'.format(item_label))
            item_label = '{} (QID: Q{})'.format(item.get_label(), item_id)

        statement_print += 'Prop: {0:.<40} value: {1} \n    '.format('{} ({})'.format(prop_label, prop_nr), item_label)

    output = '''


    Item QID: {4}
    Item: {0} / {1} / {2}
    {3}
    {5}
    '''.format(label, description, aliases, statement_print, qid, sitelinks_string)

    print(output)


def get_wd_search_results(search_string=''):
        """
        Performs a search in WD for a certain WD search string
        :param search_string: a string which should be searched for in WD
        :return: returns a list of QIDs found in the search and a list of labels complementary to the QIDs
        """
        try:
            url = 'https://www.wikidata.org/w/api.php'
            params = {
                'action': 'wbsearchentities',
                'language': 'en',
                'search': search_string,
                'format': 'json',
                'limit': '15'
            }

            reply = requests.get(url, params=params)
            search_results = reply.json()

            if search_results['success'] != 1:
                raise PBB_Core.WDSearchError('WD search failed')
            elif len(search_results['search']) == 0:
                return []
            else:
                id_list = []
                id_labels = []
                id_descr = []
                id_aliases = []
                for i in search_results['search']:
                    id_list.append(i['id'])
                    id_labels.append(i['label'])
                    if 'description' in i:
                        id_descr.append(i['description'])
                    else:
                        id_descr.append('')
                    if 'aliases' in i:
                        id_aliases.append(i['aliases'])
                    else:
                        id_aliases.append('')

                return id_list, id_labels, id_descr, id_aliases

        except requests.HTTPError as e:
            print(e)


def merge(merge_to, merge_from, login_obj):
    data = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P279')]
    try:
        wd_item = PBB_Core.WDItemEngine(wd_item_id=merge_from, data=data)
        wd_item.set_description(description='', lang='en')
        wd_item.set_description(description='', lang='de')
        wd_item.set_description(description='', lang='fr')
        wd_item.set_description(description='', lang='nl')
        wd_item.write(login=login_obj)

        print('merge accepted')
        merge_reply = PBB_Core.WDItemEngine.merge_items(from_id=merge_from, to_id=merge_to, login_obj=login_obj)
        pprint.pprint(merge_reply)
        print('merge completed')
    except PBB_Core.MergeError as e:
        pprint.pprint(e)

    except Exception as e:
        pprint.pprint(e)


def main():

    print(sys.argv[1], sys.argv[2])
    # pwd = input('Password:')
    login_obj = PBB_login.WDLogin(user=sys.argv[2], pwd=sys.argv[1])

    prefix = '''
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX schema: <http://schema.org/>
    '''

    missing_go_query = '''
        SELECT distinct ?protein ?label WHERE {
          ?protein wdt:P279 wd:Q8054 .
          ?protein wdt:P703 wd:Q5 .
          OPTIONAL {
              ?protein rdfs:label ?label filter (lang(?label) = "en") .
              #?article schema:about ?protein .
          }
          FILTER NOT EXISTS {?protein wdt:P351 ?m} .
          FILTER NOT EXISTS {?protein wdt:P352 ?n} .
          FILTER NOT EXISTS {?protein wdt:P31 wd:Q21996465} .
          FILTER NOT EXISTS {?protein wdt:P31 wd:Q14633939} .
        }
        #GROUP BY ?protein
    '''

    results = PBB_Core.WDItemEngine.execute_sparql_query(prefix=prefix, query=missing_go_query)['results']['bindings']
    start_time = time.time()

    for count, x in enumerate(results):
        protein_qid = x['protein']['value'].split('/')[-1]
        # pprint.pprint(x)
        if 'label' in x:
            label = x['label']['value']
        else:
            print('No label found for', protein_qid)


        print_item(protein_qid)

        gene_qid = lookup_symbol(symbol=label)
        print('count:', count, 'Gene QID:', gene_qid)
        if gene_qid is not None:
            decision = input('Merge? (y):')

            if decision == 'y':
                merge(merge_from=protein_qid, merge_to=gene_qid, login_obj=login_obj)

        else:
            # Protein class/family Q417841
            # protein complex Q14633939
            decision = input('Protein class? (p):\nProtein complex? (c)\nSearch (s):')

            if decision == 's':
                s_qids, s_labels, s_descr, s_aliases = get_wd_search_results(search_string=label)

                for s_count, s in enumerate(s_qids):
                    print(s_count, s_qids[s_count], s_labels[s_count], s_descr[s_count], s_aliases[s_count])

                decision = input('Select by number:')
                try:
                    number = int(decision)
                    merge_to_qid = s_qids[number]

                    merge(merge_to=merge_to_qid, merge_from=protein_qid, login_obj=login_obj)
                    continue
                except ValueError:
                    decision = input('\n\nProtein class? (p):\nProtein complex? (c):')

            try:
                if decision == 'p':
                    data = [PBB_Core.WDItemID(value='Q417841', prop_nr='P31')]
                elif decision == 'c':
                    data = [PBB_Core.WDItemID(value='Q14633939', prop_nr='P31')]
                else:
                    continue

                wd_item = PBB_Core.WDItemEngine(wd_item_id=protein_qid, data=data)

                wd_item.write(login=login_obj)

                print('added protein class')
            except Exception as e:
                pprint.pprint(e)
                continue

            pass

        # if count % 8 == 0:
        #     time.sleep(20)


if __name__ == '__main__':
    sys.exit(main())
