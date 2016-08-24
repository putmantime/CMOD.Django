# -*- coding: utf-8 -*-

'''
  Contains templates and functions for generating article stubs for the Gene Wiki
  Project on Wikipedia.
'''

import datetime, sys
import g2p_redis as g2p
import mygeneinfo as mygene

G2P_DATABASE = "g2p.db" # change this if different

# An unfortunate collision between the {} system used for Python's str.format()
# and Mediawiki's template syntax requires all {{templates}} to be escaped like
# so: {{{{templates}}}} (single {'s => {{).

stub_skeleton = """{{{{PBB|geneid={id}}}}}

'''{name}''' is a [[protein]] that in humans is encoded by the {symbol} [[gene]].{entrezcite}
{summary}

== References ==

{{{{reflist}}}}

== Further Reading ==

{{{{refbegin | 2}}}}
{citations}
{{{{refend}}}}

{{{{gene-{chromosome}-stub}}}}
{footer}
"""

entrez_cite = """
<ref name="entrez">
{{{{cite web
| title = Entrez Gene: {name}
| url = http://www.ncbi.nlm.nih.gov/gene/{id}
| accessdate = {currentdate}
}}}}</ref>
"""

def create_stub(gene_id):

    try:
        json = mygene.getJson(mygene.BASE_URL+gene_id)
    except IOError:
        sys.stderr.write("Could not retrieve JSON at {}.\n".format(mygene.BASE_URL+gene_id))
        return None

    get = mygene.get

    summary = get(json, u'summary')
    footer = ''
    if summary != '':
        summary = "==Function==\n\n"+summary
        footer = "{{NLM content}}"
    values = {
        'id':gene_id,
        'name':get(json, u'name')[0].capitalize() + get(json, u'name')[1:],
        'symbol':get(json, u'symbol'),
        'summary':summary,
        'chromosome':get(get(json, u'genomic_pos'), u'chr'),
        'currentdate':datetime.datetime.now().isoformat('T') + "-08:00", # adjust if not in CA
        'citations':"",
        'footer': footer
        }
    values['entrezcite'] = entrez_cite.format(**values)
    pmids = g2p.get_pmids(gene_id, g2p.init_redis(), 100)
    limit = 9 if len(pmids) > 9 else len(pmids)
    citations = ""
    for pmid in pmids[:limit]:
        citations = "{}*{{{{Cite pmid|{} }}}}\n".format(citations,pmid)
    values['citations'] = citations
    stub = stub_skeleton.format(**values)
    return stub


if __name__ == '__main__':
    import sys
    print create_stub(sys.argv[1])
