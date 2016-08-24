__author__ = 'Sebastian Burgstaller'

import PBB_Core
import PBB_login
import requests
import sys


class LabelReplacement:

    def __init__(self, wd_item_list, replacement_map, lang, login):
        for count, i in enumerate(wd_item_list):
            qid = 'Q{}'.format(i)
            wd_item = PBB_Core.WDItemEngine(wd_item_id=qid)

            description = wd_item.get_description(lang)

            if description in replacement_map:
                print('entered')
                en_label = ''
                if 'en' in wd_item.get_wd_json_representation()['labels']:
                    en_label = wd_item.get_wd_json_representation()['labels']['en']['value']
                print('\n')
                print('Label: {}'.format(en_label), 'QID: ', wd_item.wd_item_id)
                print(count)

                try:
                    edit_token = login.get_edit_token()
                    cookies = login.get_edit_cookie()

                    params = {
                        'action': 'wbsetdescription',
                        'id': qid,
                        'language': lang,
                        'value': replacement_map[description],
                        'token': edit_token,
                        'bot': '',
                        'format': 'json',
                    }

                    reply = requests.post('https://www.wikidata.org/w/api.php', data=params, cookies=cookies)
                    # print(reply.text)

                except requests.HTTPError as e:
                    print(e)

                except Exception as e:
                    print(e)

            else:
                print('No action required for QID: ', wd_item.wd_item_id, ' |count: ', count)

def main():
    pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=pwd)

    # for mouse genes
    # LabelReplacement(PBB_Core.WDItemList('CLAIM[351] and CLAIM[703:83310]').wditems['items'], {'gène': 'gène de souris'},
    #                  'fr', login)

    # for human genes
    LabelReplacement(PBB_Core.WDItemList('CLAIM[351] and CLAIM[703:5]').wditems['items'], {'gène': 'gène humain'},
                     'fr', login)

if __name__ == '__main__':
    sys.exit(main())

