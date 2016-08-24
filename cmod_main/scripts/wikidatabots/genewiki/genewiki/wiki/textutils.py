from django.conf import settings
from django.db import models

import re, copy, json, datetime, urllib.request, urllib.parse, urllib.error, html.parser, PBB_Core, PBB_login, mygene
import xml.etree.ElementTree as etree

citation_tool_url = "http://tools.wmflabs.org/citation-template-filling/cgi-bin/index.cgi?ddb=&type=pubmed_id&id=%s&format=xml"


def check(titles):
    '''
        Tries, as fast as possible, to check the presence of titles passed to it as
        the first command-line argument.
    '''
    titles = [titles] if isinstance(titles, str) else titles
    qtitles = [urllib.parse.quote(x) for x in titles]
    querystr = '|'.join(qtitles)
    api = 'http://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=info&redirects&format=json'
    j = json.loads(urllib.request.urlopen(api.format(title=querystr)).read().decode())
    results = {}
    pages = j['query']['pages']
    if 'redirects' in j['query']:
        redirects = j['query']['redirects']
        for r in redirects:
            results[r['from']] = r['to']
    for pid in pages:
        title = pages[pid]['title']
        results[title] = title if int(pid) > 0 else ''
    return results


def create_stub(gene_id):
    '''
        Contains templates and functions for generating article stubs for the Gene Wiki
        Project on Wikipedia.
    '''

    try:
        from genewiki.bio.mygeneinfo import get_response
        root, meta, homolog, entrez, uniprot = get_response(gene_id)
    except Exception as e:
        print(e)
        return None

    summary = root.get('summary', '')
    footer = ''
    if summary != '':
        summary = '==Function==\n\n' + summary
        footer = '{{NLM content}}'

    genomic_pos = root.get('genomic_pos')[0] if isinstance(root.get('genomic_pos'), list) else root.get('genomic_pos')
    if genomic_pos:
        chromo = '-' + genomic_pos.get('chr')
    else:
        chromo = ''
    values = {
        'id': root.get('entrezgene'),
        'name': root.get('name')[0].capitalize() + root.get('name')[1:],
        'symbol': root.get('symbol'),
        'summary': summary,
        'chromosome': chromo,
        'currentdate': datetime.date.today().isoformat(),  # adjust if not in CA
        'citations': '',
        'footer': footer
    }
    values['entrezcite'] = settings.ENTREZ_CITE.format(**values)

    # build out the citations
    mg = mygene.MyGeneInfo()
    generif = mg.getgene(gene_id, fields="generif")
    pmids = []
    if 'generif' in generif:
        pmids = str(generif['generif'][0]['pubmed']).split(",")

    limit = 9 if len(pmids) > 9 else len(pmids)
    citations = ''
    for pmid in pmids[:limit]:
        url_string = urllib.request.urlopen(citation_tool_url % (pmid))
        xml_string = url_string.read()
        root = etree.fromstring(xml_string)
        dict = {}
        for group in root:
            for elem in group:
                dict[elem.tag] = elem.text
                print(elem.tag)
                print(elem.text)
        print(dict['content'])
        citations = citations + '*' + dict['content'] + '\n'

    # replace encoded accents in names
    h = html.parser.HTMLParser()
    values['citations'] = h.unescape(citations)

    stub = settings.STUB_SKELETON.format(**values)
    return stub


def create(entrez, force=False):
    results = {'titles': {}, 'template': '', 'stub': ''}

    try:
        from genewiki.bio.mygeneinfo import get_response
        root, meta, homolog, entrez, uniprot = get_response(entrez)
    except ValueError:
        # invalid entrez
        return None

    # Query wikidata for existance of entrez_id don't create new pages for entrez_ids not in wikidata

    entrez_query = """
        SELECT ?entrez_id  WHERE {
        ?cid wdt:P351 ?entrez_id  .
        FILTER(?entrez_id ='""" + str(entrez) + """') .
    }
    """

    wikidata_results = PBB_Core.WDItemEngine.execute_sparql_query(prefix=settings.PREFIX, query=entrez_query)['results']['bindings']
    entrez_id = ''
    for x in wikidata_results:
        entrez_id = x['entrez_id']['value']
    if entrez_id != str(entrez):
        return None
    else:
        # Dictionary of each title key and tuple of it's (STR_NAME, IF_CREATED_ON_WIKI)
        titles = {'name': (root['name'].capitalize(), False),
                  'symbol': (root['symbol'], False),
                  'test': (entrez_id, False),
                  'altsym': ('{0} (gene)'.format(root['symbol']), False)}

        # For each of the titles, build out the correct names and
        # corresponding Boolean for if they're on Wikipedia
        checked = check([titles[key][0] for key in list(titles.keys())])
        for key, value in list(titles.items()):
            if checked.get(value[0]):
                titles[key] = (value[0], True)
        results['titles'] = titles

        # Generate the Stub code if the Page (for any of the possible names) isn't on Wikipedia
        if not (titles['name'][1] or titles['symbol'][1] or titles['altsym'][1]) or force:
            results['stub'] = create_stub(entrez)

        return results


def interwiki_link(entrez, name):
    # Query wikidata for Q-item id (cid)

    cid_query = """
        SELECT ?cid  WHERE {
        ?cid wdt:P351 ?entrez_id  .
        FILTER(?entrez_id ='""" + str(entrez) + """') .
    }
    """

    wikidata_results = PBB_Core.WDItemEngine.execute_sparql_query(prefix=settings.PREFIX, query=cid_query)['results']['bindings']
    cid = ''
    for x in wikidata_results:
        cid = x['cid']['value'].split('/')[-1]

    # create interwiki link
    username = models.CharField(max_length=200, blank=False)
    password = models.CharField(max_length=200, blank=False)
    # create your login object with your user and password (or the ProteinBoxBot account?)
    login_obj = PBB_login.WDLogin(user=username, pwd=password)
    # load the gene Wikidata object
    wd_gene_item = PBB_Core.WDItemEngine(wd_item_id=cid)
    # set the interwiki link to the correct Wikipedia page
    wd_gene_item.set_sitelink(site='enwiki', title=name)
    # write the changes to the item
    wd_gene_item.write(login_obj)


def strip_references(wikitext):
    '''
      Strips the references from wikitext, replacing them with a unique id.
      Returns both the stripped wikitext and a list of the references in order by
      which they were removed, usually left-right, top-down.

      Arguments:
        - `wikitext`: the wikitext to be stripped of references.
    '''

    source = copy.copy(wikitext)
    # First we ensure that UNIQ really is unique by appending characters
    UNIQ = 'x7fUNIQ'
    while UNIQ in source:
        UNIQ = UNIQ + 'f'

    # Then we do the replacements
    reftags = []
    refcount = 0
    for match in re.finditer(r'<ref\b[^>]*>(.*?)</ref>', source):
        reftags.append(match.group())
        source = source.replace(match.group(), UNIQ + str(refcount))
        refcount += 1

    # Finally, return the stripped wikitext, the list of references, and the
    # unique salt used to mark them
    return source, reftags, UNIQ


def restore_references(wikitext, references, salt):
    '''
      Restores the references removed by strip_references().
      Can be used on a fragment of the original, as long as the salt representing
      the reference location remains intact.

      Arguments:
        - `wikitext`: wikitext where the references have been stripped
        - `references`: a list of references in order of removal
        - `salt`: the unique salt used to replace the references
    '''

    restored = wikitext
    while salt in restored:
        ref_id = int(restored[restored.index(salt) + len(salt)])
        restored = restored.replace(salt + str(ref_id), references[ref_id])

    return restored

