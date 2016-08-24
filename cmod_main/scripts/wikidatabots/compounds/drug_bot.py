#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pprint
import time
import copy
import datetime
import zipfile
import pandas as pd
import numpy as np

import PBB_Core
from PBB_login import WDLogin

__author__ = 'Sebastian Burgstaller'
__licence__ = 'GPLv3'


class DrugBot(object):
    def __init__(self, user, pwd):
        properties = ['P279', 'P769', 'P31', 'P636', 'P267', 'P231', 'P486', 'P672', 'P662', 'P661', 'P652', 'P665', 'P683',
                      'P274', 'P715', 'P646', 'P592', 'P233', 'P234', 'P235',
                      'P18', 'P373', 'P2275', 'P657', 'P595', 'P2115']
        # these property names do not match those in Wikidata!!
        property_names = ['subclass of', 'significant drug interaction', 'instance of', 'route of administration', 'ATC code',
                          'CAS number', 'MeSH ID', 'MeSH Code',
                          'PubChem ID (CID)', 'ChemSpider', 'UNII', 'KEGG Drug', 'ChEBI', 'Molecular Formula', 'Drugbank ID',
                          'Freebase identifier', 'ChEMBL',
                          'SMILES', 'InChI', 'InChIKey', 'image', 'Commons category',
                          'WHO INN', 'RTECS Number', 'Guide to Pharmacology', 'NDF-RT NUI']

        prop_to_name = dict(zip(properties, property_names))
        name_to_prop = dict(zip(property_names, properties))

        login_obj = WDLogin(user=user, pwd=pwd, server='www.wikidata.org')

        drug_data = pd.read_csv('./drugbank_data/drugbank.csv', index_col=0, engine='c', encoding='utf-8',
                                dtype={'PubChem ID (CID)': np.str,
                                       'ChEBI': np.str,
                                       'ChEMBL': np.str,
                                       'ChemSpider': np.str,
                                       'Guide to Pharmacology': np.str
                                       })

        # extract creation date of Drugbank file from Drugbank zip file
        drugbank_zip = zipfile.ZipFile('./drugbank_data/drugbank.xml.zip')
        self.drugbank_date = datetime.datetime(
            *[x for x in drugbank_zip.infolist()[0].date_time]).strftime('+%Y-%m-%dT00:00:00Z')

        print(drug_data.dtypes)

        base_ref = {
            'ref_properties': ['P248'],
            'ref_values': ['Q1122544']
        }

        # remove potential 'InChI=' and 'InChIKey=' prefixes
        for i in drug_data['InChI'].index:
            if pd.notnull(drug_data['InChI'].at[i]):
                if 'InChI=' in drug_data['InChI'].at[i]:
                    drug_data['InChI'].at[i] = drug_data['InChI'].at[i][6:]
                if 'InChIKey=' in drug_data['InChIKey'].at[i]:
                    drug_data['InChIKey'].at[i] = drug_data['InChIKey'].at[i][9:]

        # remove DB prefix from Drugbank ID (should be corrected in the Wikidata property)
        for i in drug_data['Drugbank ID'].index:
            if pd.notnull(drug_data['Drugbank ID'].at[i]):
                drug_data['Drugbank ID'].at[i] = drug_data['Drugbank ID'].at[i][2:]

        # Iterate though all drugbank compounds and add those to Wikidata which are either FDA-approved or have been
        # withdrawn from the market. Add all non-missing values for each drug to Wikidata.
        for count in drug_data.index:
            print('Count is:', count)

            if drug_data.loc[count, 'Status'] == 'approved' or drug_data.loc[count, 'Status'] == 'withdrawn':
                data = []
                special_cases = ['WHO INN', 'ATC code']
                for col in drug_data.columns.values:
                    data_value = drug_data.loc[count, col]

                    # no values and values greater than 400 chars should not be added to wikidata.
                    if pd.isnull(data_value) or col not in name_to_prop:
                        continue
                    elif len(data_value) > 400:
                        continue

                    if col in property_names and col not in special_cases:
                        data.append(PBB_Core.WDString(value=str(data_value).strip(), prop_nr=name_to_prop[col]))

                # add instances of (P31) of chemical compound (Q11173), pharmaceutical drug (Q12140),
                # Biologic medical product (Q679692) and  monoclonal antibodies (Q422248)
                data.append(PBB_Core.WDItemID(value='Q11173', prop_nr='P31'))
                data.append(PBB_Core.WDItemID(value='Q12140', prop_nr='P31'))

                if drug_data.loc[count, 'Drug type'] == 'biotech':
                    data.append(PBB_Core.WDItemID(value='Q679692', prop_nr='P31'))

                if drug_data.loc[count, 'Name'][-3:] == 'mab':
                    data.append(PBB_Core.WDItemID(value='Q422248', prop_nr='P31'))

                # for instance of, do not overwrite what other users have put there
                append_value = ['P31', 'P2275']

                # Monolingual value WHO INN requires special treatment
                if pd.notnull(drug_data.loc[count, 'WHO INN']):
                    data.append(PBB_Core.WDMonolingualText(value=drug_data.loc[count, 'WHO INN'], prop_nr='P2275',
                                                           language='en'))

                # split the ATC code values present as one string in the csv file
                if pd.notnull(drug_data.loc[count, 'ATC code']):
                    for atc in drug_data.loc[count, 'ATC code'].split(';'):
                        data.append(PBB_Core.WDString(value=atc, prop_nr='P267'))

                drugbank_source = ['instance of', 'ATC code', 'CAS number', 'Drugbank ID', 'Molecular Formula',  'InChI', 'InChIKey']
                chembl_source = ['ChEMBL', 'ChemSpider', 'KEGG Drug', 'ChEBI', 'SMILES', 'WHO INN', 'Guide to Pharmacology']
                pubchem_source = ['MeSH ID', 'PubChem ID (CID)']
                ndfrt_source = ['NDF-RT NUI', 'UNII']

                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in chembl_source]:
                        # if no ChEMBL ID exists, data is from Drugbank, therefore add Drugbank as ref
                        if pd.isnull(drug_data.loc[count, 'ChEMBL']):
                            drugbank_source.append(prop_to_name[i.get_prop_nr()])
                            continue
                        i.set_references(self.make_reference(stated_in='Q6120337',
                                                             source_element=drug_data.loc[count, 'ChEMBL'],
                                                             source_element_name=drug_data.loc[count, 'Name'],
                                                             source_element_prop=name_to_prop['ChEMBL']))

                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in drugbank_source]:
                        i.set_references(self.make_reference(stated_in='Q1122544',
                                                             source_element=drug_data.loc[count, 'Drugbank ID'],
                                                             source_element_name=drug_data.loc[count, 'Name'],
                                                             source_element_prop=name_to_prop['Drugbank ID'],
                                                             date=self.drugbank_date,
                                                             date_property='P577'))

                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in pubchem_source] and pd.notnull(drug_data.loc[count, 'PubChem ID (CID)']):
                        i.set_references(self.make_reference(stated_in='Q278487',
                                                             source_element=drug_data.loc[count, 'PubChem ID (CID)'],
                                                             source_element_name=drug_data.loc[count, 'Name'],
                                                             source_element_prop=name_to_prop['PubChem ID (CID)']))

                for i in data:
                    if i.get_prop_nr() in [name_to_prop[x] for x in ndfrt_source] and pd.notnull(drug_data.loc[count, 'NDF-RT NUI']):
                        i.set_references(self.make_reference(stated_in='Q21008030',
                                                             source_element=drug_data.loc[count, 'NDF-RT NUI'],
                                                             source_element_name=drug_data.loc[count, 'Name'].upper(),
                                                             source_element_prop=name_to_prop['NDF-RT NUI']))

                label = drug_data.loc[count, 'Name']
                domain = 'drugs'

                # If label in aliases list, remove the label from it. If an alias is longer than 250 chars, also remove
                # Aliases longer than 250 characters will trigger an WD API error.
                if pd.notnull(drug_data.loc[count, 'Aliases']):
                    aliases = drug_data.loc[count, 'Aliases'].split(';')
                    for i in aliases:
                        if i == label or i == label.lower() or len(i) > 250 or len(i) == 0:
                            aliases.remove(i)

                start = time.time()

                # pprint.pprint(data)
                # pprint.pprint(references)
                print('Drug name:', label)
                try:

                    wd_item = PBB_Core.WDItemEngine(item_name=label, domain=domain, data=data,
                                                    use_sparql=True, append_value=append_value)

                    # overwrite only certain descriptions
                    descriptions_to_overwrite = {'chemical compound', 'chemical substance', ''}
                    if wd_item.get_description() in descriptions_to_overwrite:
                        wd_item.set_description(description='pharmaceutical drug', lang='en')

                    wd_item.set_label(label=label, lang='en')

                    if pd.notnull(drug_data.loc[count, 'Aliases']):
                        wd_item.set_aliases(aliases=aliases, lang='en', append=True)

                    # pprint.pprint(wd_item.get_wd_json_representation())

                    wd_item.write(login_obj)

                    new_mgs = ''
                    if wd_item.create_new_item:
                        new_mgs = ': New item'

                    PBB_Core.WDItemEngine.log('INFO', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=drug_data['Drugbank ID'].at[count],
                        exception_type='',
                        message='success{}'.format(new_mgs),
                        wd_id=wd_item.wd_item_id,
                        duration=time.time() - start
                    ))
                    print('success')

                except Exception as e:
                    print(e)

                    PBB_Core.WDItemEngine.log('ERROR', '{main_data_id}, "{exception_type}", "{message}", {wd_id}, {duration}'.format(
                        main_data_id=drug_data['Drugbank ID'].at[count],
                        exception_type=type(e),
                        message=e.__str__(),
                        wd_id='',
                        duration=time.time() - start
                    ))

                end = time.time()
                print('Time elapsed:', end - start)

    def make_reference(self, stated_in, source_element, source_element_name, source_element_prop, date=time.strftime('+%Y-%m-%dT00:00:00Z'),
                       date_property='P813'):
        ref = [[
            PBB_Core.WDItemID(value=stated_in, prop_nr='P248', is_reference=True),  # stated in
            PBB_Core.WDString(value=source_element, prop_nr=source_element_prop, is_reference=True),  # source element
            PBB_Core.WDItemID(value='Q1860', prop_nr='P407', is_reference=True),  # language of work
            PBB_Core.WDMonolingualText(value=source_element_name, language='en',
                                       prop_nr='P1476', is_reference=True),
            PBB_Core.WDTime(time=date, prop_nr=date_property, is_reference=True)  # publication date
        ]]

        # this will overwrite all existing references of a WD claim value.
        for x in ref[0]:
            x.overwrite_references = True

        return ref
