#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Sebastian Burgstaller'
__licence__ = 'GPLv3'

import PBB_Core
import pandas as pd
import requests
import os


col_names = ['QID', 'Wikidata label', 'Wikipedia title', 'Wikipedia pageid', 'has interwiki link']

data_types = {x: object for x in col_names}
data_types.update({'has interwiki link': bool})


append = True

if os.path.isfile('./WD_to_WP_disease_map.csv') and append:
    wd_to_wp_map = pd.read_csv('./WD_to_WP_disease_map.csv', index_col=0, dtype=data_types)
else:
    wd_to_wp_map = pd.DataFrame(columns=col_names)

wd_disease_items = PBB_Core.WDItemList('CLAIM[279:12136] or CLAIM[279:929833] or CLAIM[31:12136] '
                                       'or CLAIM[31:929833] or CLAIM[557] or CLAIM[699] or claim[493] '
                                       'or claim[494] or claim[1995]').wditems['items']

print(wd_to_wp_map.dtypes)

print('Total number of items to match:', len(wd_disease_items))

for count, item in enumerate(wd_disease_items):
    print(item)
    if str(item) in wd_to_wp_map['QID'].values and append:
        print('skipping', item)
        count += 1
        continue

    wd_object = PBB_Core.WDItemEngine(wd_item_id='Q{}'.format(item))
    wd_json = wd_object.wd_json_representation

    wd_to_wp_map.loc[count, 'QID'] = item

    label = ''
    sitelink = ''

    if 'labels' in wd_json:
        if 'en' in wd_json['labels']:
            label = wd_json['labels']['en']['value']
            # print(count, label)
            wd_to_wp_map.loc[count, 'Wikidata label'] = label

    if 'sitelinks' in wd_json:
        if 'enwiki' in wd_json['sitelinks']:
            sitelink = wd_json['sitelinks']['enwiki']['title']
            # print(count, sitelink)

            wd_to_wp_map.loc[count, 'Wikipedia title'] = sitelink
            wd_to_wp_map.loc[count, 'has interwiki link'] = True

    aliases = []
    if 'aliases' in wd_json:
            for lang in wd_json['aliases']:
                if lang == 'en':
                    for alias in wd_json['aliases'][lang]:
                        aliases.append(alias['value'])

    names = [label]
    names.extend(aliases)
    for name in names:
        try:
            params = {
                'action': 'query',
                'titles': name,
                'format': 'json'
            }

            reply = requests.get('https://en.wikipedia.org/w/api.php', params=params)

            reply_json = reply.json()
            print(reply_json)

            if name != '':
                for pageid in reply_json['query']['pages']:
                    if pageid != '-1':
                        wd_to_wp_map.loc[count, 'Wikipedia pageid'] = pageid
                        wd_to_wp_map.loc[count, 'Wikipedia title'] = reply_json['query']['pages'][pageid]['title']
                        break
                break
        except requests.HTTPError as e:
            print(e)

    print(
        'Q{}'.format(wd_to_wp_map.loc[count, 'QID']),
        wd_to_wp_map.loc[count, 'Wikidata label'],
        wd_to_wp_map.loc[count, 'Wikipedia pageid'],
        wd_to_wp_map.loc[count, 'Wikipedia title']
    )

    # if count > 100:
    #     break

    if count % 100 == 0:
            wd_to_wp_map.to_csv('./WD_to_WP_disease_map.csv', index=True, encoding='utf-8', header=True)
            print('count:', count)

wd_to_wp_map.to_csv('./WD_to_WP_disease_map.csv', index=True, encoding='utf-8', header=True)

