import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_Core
import PBB_login
import pprint
import MicrobeBotWDFunctions as wdo
import time

__author__ = 'timputman'




def wd_item_construction(gene_record, spec_strain, login):
    """
    identifies and modifies or writes new wd items for proteins
    :param gene_record: pandas dataframe
    :param login: bot account login credentials
    :return: PBB_Core wd item object
    """

    go_props = {'Function': 'P680',
                'Component': 'P681',
                'Process': 'P682'
                }
    go_evidence_codes = {
        'EXP': 'Q23173789',
        'IDA': 'Q23174122',
        'IPI': 'Q23174389',
        'IMP': 'Q23174671',
        'IGI': 'Q23174952',
        'IEP': 'Q23175251',
        'ISS': 'Q23175558',
        'ISO': 'Q23190637',
        'ISA': 'Q23190738',
        'ISM': 'Q23190825',
        'IGC': 'Q23190826',
        'IBA': 'Q23190827',
        'IBD': 'Q23190833',
        'IKR': 'Q23190842',
        'IRD': 'Q23190850',
        'RCA': 'Q23190852',
        'TAS': 'Q23190853',
        'NAS': 'Q23190854',
        'IC': 'Q23190856',
        'ND': 'Q23190857',
        'IEA': 'Q23190881',
        'IMR': 'Q23190842'
    }

    item_name = '{}    {}'.format(gene_record['name'], gene_record['locus_tag'])
    item_description = 'microbial protein found in {}'.format(spec_strain.iloc[0]['organism_name'])


    uniprot = str(list(gene_record['uniprot'].values())[0])

    def protein_item_statements():
        """
        construct list of referenced statements to pass to PBB_Core Item engine
        :return:
        """
        uniprot_ref = wdo.reference_store(source='uniprot', identifier=uniprot)

        WD_String_CLAIMS = {'P637': str(gene_record['refseq']['protein']),  # set refseq protein id
                            'P352': uniprot  # Set uniprot ID
                            }

        WD_Item_CLAIMS = {'P703': [spec_strain.iloc[0]['wd_qid']],  # get strain taxid qid from strain record
                          'P279': ['Q8054'],  # subclass of protein
                          }

        statements = []
        #generate go term claims
        for gt in gene_record['GOTERMS']:
            goprop = go_props[gt[1]]
            govalue = wdo.WDSparqlQueries(prop='P686', string=gt[0]).wd_prop2qid() #  Get GeneOntology Item by GO ID
            evprop = 'P459'
            try:
                evvalue = go_evidence_codes[gt[2]]
                evstat = PBB_Core.WDItemID(value=evvalue, prop_nr=evprop, is_qualifier=True)
                statements.append(PBB_Core.WDItemID(value=govalue, prop_nr=goprop, references=[uniprot_ref], qualifiers=[evstat]))
            except Exception as e:
                statements.append(PBB_Core.WDItemID(value=govalue, prop_nr=goprop, references=[uniprot_ref]))


        # generate list of pbb core value objects for all valid claims
        for k, v in WD_Item_CLAIMS.items():
            if v:
                for i in v:
                    statements.append(PBB_Core.WDItemID(value=i, prop_nr=k, references=[uniprot_ref]))

        for k, v in WD_String_CLAIMS.items():
            if v:
                statements.append(PBB_Core.WDString(value=v, prop_nr=k, references=[uniprot_ref]))

        return statements

    start = time.time()

    try:
        # find the appropriate item in wd or make a new one
        wd_item_protein = PBB_Core.WDItemEngine(item_name=item_name, domain='genes', data=protein_item_statements(),
                                                use_sparql=True)
        wd_item_protein.set_label(item_name)
        wd_item_protein.set_description(item_description, lang='en')
        wd_item_protein.set_aliases([gene_record['symbol'], gene_record['locus_tag'], 'protein'])
        #pprint.pprint(wd_item_protein.get_wd_json_representation())
        # attempt to write json representation of item to wd
        wd_item_protein.write(login=login)

        # log the experience
        new_mgs = ''
        if wd_item_protein.create_new_item:
            new_mgs = ': New item'
        PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
            main_data_id=gene_record['refseq']['protein'],
            exception_type='',
            message='success{}'.format(new_mgs),
            wd_id=wd_item_protein.wd_item_id,
            duration=time.time() - start
        ))

        print('success')
        return 'success'

    except Exception as e:
        pprint.pprint(e)
        PBB_Core.WDItemEngine.log('ERROR',
                                  '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                                      main_data_id=gene_record['refseq']['protein'],
                                      exception_type=type(e),
                                      message=e.__str__(),
                                      wd_id='',
                                      duration=time.time() - start
                                  ))
        print('no go')

    end = time.time()
    print('Time elapsed:', end - start)

    return protein_item_statements()



