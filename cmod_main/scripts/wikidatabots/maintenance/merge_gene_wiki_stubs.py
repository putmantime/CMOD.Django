import PBB_Core
import PBB_login
import sys
import time
import urllib

__author__ = 'Sebastian Burgstaller'
__license__ = 'AGPLv3'

"""
This script merges Gene Wiki protein/gene stubs early on imported into Wikidata from Gene Wiki infoboxes.
The merges are done based on the GeneAtlas image names, extensive error handling has been implemented.
"""


class GeneWikiStubMerger(object):
    def __init__(self, login):

        self.login_obj = login

        candidate_qids = PBB_Core.WDItemEngine.execute_sparql_query(query='''
            SELECT  ?protein WHERE {
                ?protein wdt:P692 ?gene_atlas .
                FILTER NOT EXISTS {?protein wdt:P351 ?m} .
                FILTER NOT EXISTS {?protein wdt:P352 ?n} .
            }
            GROUP BY ?protein
        ''')

        for count, x in enumerate(candidate_qids['results']['bindings'][0:300]):
            qid = x['protein']['value'].split('/')[-1]
            print(qid)

            start = time.time()

            merge_from = PBB_Core.WDItemEngine(wd_item_id=qid)
            gene_atlas_images = []
            for statement in merge_from.statements:
                if statement.get_prop_nr() == 'P692':
                    gene_atlas_images.append(statement.get_value())

            print(count, gene_atlas_images)
            # break

            prop_list = set(merge_from.get_property_list())

            req_props = {'P279', 'P692', 'P703', 'P646', 'P31', 'P349'}
            if prop_list.issubset(req_props):
                data = [PBB_Core.WDBaseDataType.delete_statement(prop_nr='P279'),
                        PBB_Core.WDBaseDataType.delete_statement(prop_nr='P31')]

                try:
                    merge_from = PBB_Core.WDItemEngine(wd_item_id=qid, data=data)
                    merge_from.set_description(description='', lang='en')
                    merge_from.set_description(description='', lang='de')
                    merge_from.set_description(description='', lang='fr')
                    merge_from.set_description(description='', lang='nl')

                    merge_from.write(self.login_obj)

                except Exception as e:
                    print('Error writing to item which should be merged')
                    PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id=qid,
                        duration=time.time() - start
                    ))
                    continue

            else:
                PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='Property error',
                        message='Too many unclear properties on the item',
                        wd_id=qid,
                        duration=time.time() - start
                ))
                print('UNCLEAR props alarm', prop_list)

                continue

            merge_to_item_list = set()
            for i in gene_atlas_images:

                xx = PBB_Core.WDItemEngine.execute_sparql_query(query='''
                SELECT ?ga_carriers WHERE {{
                    BIND(IRI(CONCAT("http://commons.wikimedia.org/wiki/Special:FilePath/", "{0}")) as ?gene_atlas)
                    ?ga_carriers wdt:P692 ?gene_atlas .

                }}
                GROUP BY ?ga_carriers'''.format(urllib.parse.quote(i)))

                ga_carriers = []
                for z in xx['results']['bindings']:
                    ga_qid = z['ga_carriers']['value'].split('/')[-1]
                    ga_carriers.append(ga_qid)

                merge_to_item_list.update(ga_carriers)
                print('GA carriers: ', ga_carriers)

            merge_to_item_list.remove(qid)

            if len(merge_to_item_list) == 0:
                PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='Merge target error',
                        message='Merge target not found!',
                        wd_id=qid,
                        duration=time.time() - start
                ))
                print('Merge target error, merge target not found')
                continue

            elif len(merge_to_item_list) > 1:
                PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='Merge target error',
                        message='More than one merge target recovered, skipping this item! ' + str(merge_to_item_list),
                        wd_id=qid,
                        duration=time.time() - start
                ))
                print('Merge target error, more than one target')
                continue

            else:
                merge_to_qid = merge_to_item_list.pop()
                merge_to = PBB_Core.WDItemEngine(wd_item_id=merge_to_qid)

                merge_to_props = merge_to.get_property_list()
                if 'P352' in merge_to_props:
                    PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='Merge target error',
                        message='Merge to protein item attempted',
                        wd_id=qid,
                        duration=time.time() - start
                    ))
                    print('Merge target error, protein item as target')
                    continue

                try:
                    PBB_Core.WDItemEngine.merge_items(from_id=qid, to_id=merge_to_qid, login_obj=self.login_obj)

                    PBB_Core.WDItemEngine.log('INFO', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='',
                        message='success',
                        wd_id=qid,
                        duration=time.time() - start
                    ))
                    print('Success: ', qid, )

                except PBB_Core.MergeError as e:
                    PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id=qid,
                        duration=time.time() - start
                    ))

                    print(e)


def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    GeneWikiStubMerger(login)


if __name__ == '__main__':
    sys.exit(main())
