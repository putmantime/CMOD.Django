import pandas as pd
import numpy as np
import PBB_Core
import PBB_login
import sys
import time
import pprint

__author__ = 'Sebastian Burgstaller'


class PDBImageFix(object):
    def __init__(self, login):

        self.login_obj = login

        image_data = pd.read_csv('./image_data/gene_wiki_images_with_preferred.txt', encoding='utf-8', sep='\t',
                                 dtype={'entrez': np.str})

        wdq_results = PBB_Core.WDItemList('CLAIM[351] and CLAIM[703:5]', '351').wditems
        wd_entrez_ids = list(map(lambda z: z[2], wdq_results['props']['351']))
        entrez_qid_list = list(map(lambda z: 'Q{}'.format(z[0]), wdq_results['props']['351']))

        print(len(wd_entrez_ids))

        for index in image_data.index:
            start = time.time()
            # print(image_data.loc[index, 'other_images'])
            image_names = image_data.loc[index, 'other_images']

            preferred_image = image_data.loc[index, 'primary_image']

            image_file_extension = ['.png', '.jpg', '.jpeg', '.pdf']
            if pd.notnull(preferred_image) and '|' in preferred_image:
                for splt in preferred_image.split('|'):
                    for ending in image_file_extension:
                        if ending in splt:
                            preferred_image = splt
                            break

            entrez = image_data.loc[index, 'entrez']
            # print(entrez)

            protein_images = []
            protein_image_value_store = []
            genex_images = []
            genex_value_store = []

            if entrez not in wd_entrez_ids:
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=entrez,
                        exception_type='',
                        message='Entrez ID not yet in Wikidata!!',
                        wd_id='',
                        duration=time.time() - start
                    ))
                continue
            else:
                curr_qid = entrez_qid_list[wd_entrez_ids.index(entrez)]

            if pd.isnull(image_names):
                PBB_Core.WDItemEngine.log('WARNING', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=entrez,
                        exception_type='',
                        message='No images available for this Entrez ID',
                        wd_id=curr_qid,
                        duration=time.time() - start
                    ))
                continue

            for sub_string in image_names.split('|'):
                if 'PBB GE ' in sub_string:
                    value = sub_string[5:]

                    # if value[-6:-4] == 'tn':
                    #     value = value[:-6] + 'fs' + value[-4:]


                    # Gene Expression reference: https://www.wikidata.org/wiki/Q21074956

                    genex_images.append(value)
                    genex_value_store.append(PBB_Core.WDCommonsMedia(value=value, prop_nr='P692'))
                elif 'PDB ' in sub_string:
                    value = sub_string[5:]
                    protein_images.append(value)

                    protein_image_value_store.append(PBB_Core.WDCommonsMedia(value, prop_nr=''))

            entrez_id_value = PBB_Core.WDString(value=entrez, prop_nr='P351')

            data = [entrez_id_value]
            data.extend(genex_value_store)

            if pd.notnull(preferred_image):
                data.append(PBB_Core.WDCommonsMedia(value=preferred_image, prop_nr='P18'))

            try:
                gene_item = PBB_Core.WDItemEngine(wd_item_id=curr_qid, domain='genes', data=data)
                # pprint.pprint(gene_item.get_wd_json_representation())

                gene_item.write(self.login_obj)

                PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=entrez,
                        exception_type='',
                        message='success',
                        wd_id=curr_qid,
                        duration=time.time() - start
                ))
                print(index, 'success', curr_qid, entrez, gene_item.get_label(lang='en'))

            except Exception as e:
                print(index, 'error', curr_qid, entrez)
                PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                    main_data_id=entrez,
                    exception_type=type(e),
                    message=e.__str__(),
                    wd_id=curr_qid,
                    duration=time.time() - start
                ))

            # if index > 10:
            #     break


def main():
    print(sys.argv[1])
    # pwd = input('Password:')
    login = PBB_login.WDLogin(user='ProteinBoxBot', pwd=sys.argv[1])

    PDBImageFix(login)


if __name__ == '__main__':
    sys.exit(main())
