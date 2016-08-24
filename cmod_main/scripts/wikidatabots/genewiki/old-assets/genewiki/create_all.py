# -*- coding: utf-8 -*-

import json
from urllib import quote
import mygeneinfo as mgi
import articlestub as article
from check import check

def create_all(entrez, force=False):
    results = {'titles':{},
               'checked':{},
               'template':'',
               'stub':''}

    try:
        jdocs = mgi.get_json_documents(entrez)
    except ValueError:
        # invalid entrez
        return None

    t = {}
    titles = []
    genejson = jdocs['gene_json']
    t['name'] = genejson['name'].capitalize()
    t['symbol'] = genejson['symbol']
    t['altsym'] = t['symbol']+' (gene)'
    t['templatename'] = 'Template:PBB/'+entrez

    titles = [t[x] for x in t]
    checked = check(titles)

    if checked[t['templatename']] == 'missing' or force:
        results['template'] = str(mgi.parse_json(**jdocs))
    if not (checked[t['name']] or checked[t['symbol']]
            or checked[t['altsym']]) or force:
        results['stub'] = article.create_stub(entrez)

    results['titles'] = t
    results['checked'] = checked
    return results

if __name__ == '__main__':
    import sys
    print create_all(sys.argv[1], force=len(sys.argv) > 2)
