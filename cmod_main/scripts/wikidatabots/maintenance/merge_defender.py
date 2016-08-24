import PBB_Core
import PBB_login
import sys
import requests
import time
import pprint
import traceback

__author__ = 'Sebastian Burgstaller-Muehlbacher'
__licence__ = 'AGPLv3'

'''
Allows to find and undo merges in Wikidata, based on WDQ queries and two lists of incompatible properties.
It will find the responsible user account and the revisions and will undo the merge. Also, a log file is being
generated. For undoing, the MediaWiki API calls 'undo' and 'undoafter' are being used.
'''


class MergeDefender(object):
    def __init__(self, login, merge_target, conflict_set_1, conflict_set_2):
        """
        Constructor
        :param login: the PBB_core login object for Wikidata
        :type login: Instance of PBB_core.login
        :param merge_target: The WD QID the merge has been made to
        :type merge_target: str
        :param conflict_set_1: A set of WD property IDs which should be on one but not the other item. Needs to be
                                mutually exclusive with parameter conflict_set_2
        :param conflict_set_2: A set of WD property IDs which should be on one but not the other item. Needs to be
                                mutually exclusive with parameter conflict_set_1
        """

        assert isinstance(conflict_set_1, set)
        assert isinstance(conflict_set_2, set)

        self.login_obj = login
        self.base_url = 'https://www.wikidata.org/w/api.php'

        self.perpetrator = ''

        self.merged_from = ''

        # The two revision ids after which everything should be undone
        self.merged_to_rev_id = ''
        self.merged_from_rev_id = ''

        # The latest revision ids
        self.merged_to_latest_rev_id = ''
        self.merged_from_latest_rev_id = ''

        self.merged_to = merge_target
        merged_to_revisions = self.get_revision_history(self.merged_to)
        self.merged_to_latest_rev_id = merged_to_revisions[0]['revid']

        # Search for first revision where something was merged into the current item
        for revision in merged_to_revisions:
            # pprint.pprint(revision)
            if 'wbmergeitems-from' in revision['comment']:
                self.perpetrator = revision['user']
                self.merged_from = revision['comment'].split('||')[1].split(' ')[0]
                # print(self.merged_from)
                self.merged_to_rev_id = revision['parentid']
                break

        search_back = False
        merged_from_revisions = self.get_revision_history(self.merged_from)
        self.merged_from_latest_rev_id = merged_from_revisions[0]['revid']
        for revision in merged_from_revisions:

            if search_back:
                if revision['user'] == self.perpetrator:
                    continue
                else:
                    self.merged_from_rev_id = revision['parentid']
                    break
            elif 'wbmergeitems-to' in revision['comment'] and revision['user'] == self.perpetrator \
                    and self.merged_to in revision['comment']:
                search_back = True
                continue

        print('merged to ', self.merged_to, ' merged from ', self.merged_from)
        print('merged to revision id ', self.merged_to_rev_id, ' merged from revision id', self.merged_from_rev_id)

        print('User name responsible for merge:', self.perpetrator)

        merged_to_item = PBB_Core.WDItemEngine(wd_item_id=self.merged_to)
        merged_from_item = PBB_Core.WDItemEngine(wd_item_id=self.merged_from)

        property_set = set(merged_to_item.get_property_list())

        # print(property_set)
        if conflict_set_1.issubset(property_set) and conflict_set_2.issubset(property_set):
            print(self.merged_to, 'Merged from undo: True')

            self.revert(qid=self.merged_to, undo_id=self.merged_to_latest_rev_id, undo_after_id=self.merged_to_rev_id)

        property_set = set(merged_from_item.get_property_list())

        # print(property_set)

        if conflict_set_1.issubset(property_set) and conflict_set_2.issubset(property_set):
            print(self.merged_from, 'Merged to undo: True')

            self.revert(qid=self.merged_from, undo_id=self.merged_from_latest_rev_id, undo_after_id=self.merged_from_rev_id)

    def get_merged_items(self):
        pass

    def get_revision_history(self, qid):

        params = {
            'action': 'query',
            'titles': qid,
            'prop': 'revisions',
            'rvprop': 'user|timestamp|comment|ids',
            # setting the revision start time is currently not necessary, but if set needs to be the GMT (WD time)
            'rvstart': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'format': 'json',
            'rvlimit': '50'
        }

        try:
            reply = requests.get(self.base_url, params=params)
            # pprint.pprint(reply.json())

            for i in reply.json()['query']['pages'].values():
                if 'revisions' in i:
                    return i['revisions']

        except requests.HTTPError as e:
            print('error while retrieving revision history', e)

    def revert(self, qid, undo_id, undo_after_id):

        params = {
            'action': 'edit',
            'title': qid,
            'token': self.login_obj.get_edit_token(),
            'undo': undo_id,
            'undoafter': undo_after_id,
            'format': 'json'
        }

        headers = {
            'content-type': 'multipart/form-data',
            'charset': 'utf-8',
        }

        try:
            r = requests.post(self.base_url, data=params, headers=headers, allow_redirects=True, cookies=self.login_obj.cookie_jar)

            pprint.pprint(r.json())

            PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}"'.format(
                        main_data_id=self.merged_to,
                        exception_type='',
                        message='successfully undid merge from {}'.format(self.merged_from),
                ))

        except Exception as e:
            print('error while reverting', e)
            PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}'.format(
                    main_data_id=self.merged_to,
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=self.merged_from,
                ))


def main():
    """
    This function undo gene to protein merges. For that, a query searches for WD items which have the
    Entrez gene ID (P351) and Uniprot ID (P352) on one item. Bases on that, it generates instances of MergeDefender
    and undoes the merges. 
    :return: None
    """
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    conflict_set_1 = {'P351'}
    conflict_set_2 = {'P352'}

    likely_merged_ids = PBB_Core.WDItemList(wdquery='CLAIM[351] AND CLAIM[352]')
    print(likely_merged_ids.wditems['items'])

    for count, x in enumerate(likely_merged_ids.wditems['items']):
        print('\n', count)
        print('Q{}'.format(x))

        try:

            MergeDefender(login, merge_target='Q{}'.format(x), conflict_set_1=conflict_set_1, conflict_set_2=conflict_set_2)

        except Exception as e:
            traceback.print_exc()
            PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}"'.format(
                        main_data_id=x,
                        exception_type=type(e),
                        message=e.__str__(),
                    ))


if __name__ == '__main__':
    sys.exit(main())