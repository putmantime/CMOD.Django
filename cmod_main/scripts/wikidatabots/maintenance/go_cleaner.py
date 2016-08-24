import PBB_Core
import PBB_login
import sys
import time
import pprint

__author__ = 'Sebastian Burgstaller'

"""
This script retrieves Wikidata GO terms which do not match the current formatter URL (without GO: prefix) and fix those.
It will only work if the GO term ID is the last digits of a string.
"""

class GOCleaner(object):
    def __init__(self, login):

        self.login_obj = login

        # wdq_results = PBB_Core.WDItemList('CLAIM[686]', '686').wditems
        # wd_go_terms = list(map(lambda z: z[2], wdq_results['props']['686']))
        # go_qid_list = list(map(lambda z: 'Q{}'.format(z[0]), wdq_results['props']['686']))

        query = '''
            SELECT distinct ?gene ?go WHERE {
                ?gene wdt:P686 ?go .
                FILTER(!REGEX(?go, "^GO:[0-9]", "i"))
            }
        '''
        qids_to_clean = set()
        for x in PBB_Core.WDItemEngine.execute_sparql_query(query=query)['results']['bindings']:
            qids_to_clean.add(x['gene']['value'].split('/')[-1])

        # print(len(wd_go_terms))
        # for count, go_term in enumerate(wd_go_terms):
        #     curr_qid = go_qid_list[wd_go_terms.index(go_term)]
        #
        #     # try:
        #     #     int(go_term)
        #     # except ValueError as e:
        #     qids_to_clean.add(curr_qid)

        for count, curr_qid in enumerate(qids_to_clean):
            start = time.time()
            clean_gos = []
            print(curr_qid)

            cleanup_item = PBB_Core.WDItemEngine(wd_item_id=curr_qid)
            for wd_value in cleanup_item.statements:
                if wd_value.get_prop_nr() == 'P686':
                    go_value = wd_value.get_value()

                    # int(go_value)

                    if not go_value.startswith('GO'):
                        clean_gos.append(PBB_Core.WDString(value='GO:' + go_value, prop_nr='P686'))

            try:
                go_item = PBB_Core.WDItemEngine(wd_item_id=curr_qid, data=clean_gos)
                # pprint.pprint(go_item.get_wd_json_representation())

                go_item.write(self.login_obj)

                PBB_Core.WDItemEngine.log('INFO', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        exception_type='',
                        message='success',
                        wd_id=curr_qid,
                        duration=time.time() - start
                ))
                print(count, 'success', curr_qid, go_item.get_label(lang='en'))

            except Exception as e:
                print(count, 'error', curr_qid)
                PBB_Core.WDItemEngine.log('ERROR', '"{exception_type}", "{message}", {wd_id}, {duration}'.format(
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=curr_qid,
                    duration=time.time() - start
                ))


def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    GOCleaner(login)


if __name__ == '__main__':
    sys.exit(main())
