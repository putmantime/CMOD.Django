import requests
import pprint
import re
# import PBB_Core
from bs4 import BeautifulSoup
from string import ascii_lowercase
import time
import os
import gc


def parse_compound(cas_nr):
    comp_url = 'http://chem.sis.nlm.nih.gov/chemidplus/rn/{}'.format(cas_nr)
    print(comp_url)
    comp_results = requests.get(comp_url)
    # print(comp_results.text)
    print(results.status_code)
    raw_html = comp_results.text

    file_name = './chemidplus_pages/{}.html'.format(cas_nr)
    if not os.path.exists(file_name) or os.path.getsize(file_name) < 1500:
        f = open(file_name, 'w')
        f.write(comp_results.text)
        f.close()
        wait_required = True
    else:
        f = open(file_name, 'r')
        raw_html = f.read()
        f.close()
        wait_required = False
        print('I read from the file')

    site_parse = BeautifulSoup(raw_html, 'html.parser')

    unii = ''
    inchi_key = ''
    inchi = ''
    smiles = ''

    for chem_id in site_parse.find_all("div", class_="lc2Left"):

        for i in chem_id.br.find_all('span'):
            if i.text.startswith('UNII:'):
                unii = i.text.split('\xa0')[1]
                print(unii)

            elif i.text.startswith('InChIKey:'):
                inchi_key = i.text.split('\xa0')[1]
                print(inchi_key)

        # extract compound name from <h1> tag
        tag_gen = chem_id.h1.descendants
        for zz in tag_gen:
            chem_name = zz
            print(zz)
            break

    for chem_id in site_parse.find_all("div", id="structureDescs"):
        for xyz in chem_id.find_all('div', class_="scrollWrapper"):
            if hasattr(xyz, 'wbr') and xyz.wbr is not None:
                smiles = str(xyz.wbr.text[:-10])
            smiles = str(xyz.contents[1].string).strip() + smiles

        xy = chem_id.find_all('div')
        # print(xy.text)
        for xx in xy:
            chem_id_type = ''
            for xxx in xx.children:
                if xxx.string is None or len(xxx) <= 1:
                    if hasattr(xxx, 'h3'):
                        chem_id_type = xxx.string
                else:
                    if chem_id_type == 'InChI':
                        inchi = xxx.string.strip()

    print(inchi)
    print(smiles)
    comp_results.close()
    del raw_html
    del site_parse

    return inchi, inchi_key, smiles, unii, wait_required

# parse_compound(cas_nr='52-53-9')

# base_url = 'http://chem.sis.nlm.nih.gov/chemidplus/name/startswith/20a'
# base_url = 'http://chem.sis.nlm.nih.gov/chemidplus/rn/145-14-2'
# base_url = 'http://chem.sis.nlm.nih.gov/chemidplus/name/startswith/a?DT_START_ROW=1&DT_ROWS_PER_PAGE=10'
base_url = 'http://chem.sis.nlm.nih.gov/chemidplus/name/startswith/{}?DT_START_ROW={}&DT_ROWS_PER_PAGE={}'

if not os.path.exists('./chemidplus_pages'):
    os.makedirs('./chemidplus_pages')

wait_required = True

start_letters = []
start_letters.extend(list(range(0, 10)))
start_letters.extend(list(ascii_lowercase))
start_letters.extend(['(', '#', "'"])

search_results = {}

total_results_count = 0
start = time.time()

for start_letter in start_letters:
    rs = requests.get(base_url.format(start_letter, '1', '2'))
    sp = BeautifulSoup(rs.text, 'html.parser')

    print(rs.status_code)

    letter_results_count = 0
    for res_bar in sp.find('div', class_='resultsBar'):
        try:
            letter_results_count = int(str(res_bar.string).split(' ')[0])
        except ValueError:
            pass

    print(letter_results_count)
    bu = 'http://chem.sis.nlm.nih.gov/chemidplus/name/startswith/{}?'.format(start_letter)
    processed_count = 0
    time.sleep(3)

    for subquery_count in range(0, -(-letter_results_count//10000)):
        print('NEW query')
        results = requests.get(base_url.format(start_letter, subquery_count * 10000 + 1, 10000))
        time.sleep(3)

        print(base_url.format(start_letter, subquery_count * 10000 + 1, '10000'))
        soup = BeautifulSoup(results.text, 'html.parser')

        for count, x in enumerate(soup.find_all('div', class_='resultCol1')):
            chem_name = str(x.span.string)
            cas = str(x.br.string)
            print('Found:', count, chem_name)

            if cas not in search_results:
                search_results[cas] = {
                    'name': chem_name,
                    'new': ''
                }

            processed_count += 1
            letter_results_count -= 1

        print(count, len(search_results))
        results.close()
        del soup
        gc.collect()

    time.sleep(3)

    for count, cas in enumerate(search_results):
        # 'new' flag processing required to avoid reprocessing of earlier search results.
        if 'new' in search_results[cas]:
            print(count, 'Retrieving CAS #:', cas)
            inchi, inchi_key, smiles, unii, wait_required = parse_compound(cas)

            # the server enforces a minimum of 3 seconds wait before next request
            if wait_required:
                time.sleep(3)

            search_results[cas] = {
                'inchi': inchi,
                'inchi_key': inchi_key,
                'smiles': smiles,
                'unii': unii
            }

            del search_results[cas]['new']

    rs.close()
    del sp
    gc.collect()

print(len(search_results))

end = time.time()

print('duration:', (end - start)/60)
