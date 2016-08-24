STRICT = True

'''
    Template Settings:
    The page_prefix is the 'namespace' of the infoboxes. All the respective pages are
    in <base_site>/wiki/<page_prefix><entrez id>.
    The template_name is the name of the template that the parser attempts to find
    when parsing raw wikitext. It immediately follows the opening brackets.
'''
BASE_SITE = 'en.wikipedia.org'
PAGE_PREFIX = 'Template:PBB/'
TEMPLATE_NAME = 'GNF_Protein_box'

'''
    Pymol Configuration:
    Directs to the installation path of pymol (www.pymol.org) molecular rendering
    system. Value should be an absolute path to the pymol binary.
'''
PYMOL = '/usr/bin/pymol'

MOUSE_TAXON_ID = 10090

G2P_DATABASE = 'g2p.db'  # change this if different

# An unfortunate collision between the {} system used for Python's str.format()
# and Mediawiki's template syntax requires all {{templates}} to be escaped like
# so: {{{{templates}}}} (single {'s => {{).
STUB_SKELETON = """{{{{Infobox_gene}}}}

'''{name}''' is a [[protein]] that in humans is encoded by the {symbol} [[gene]].{entrezcite}
{summary}

== References ==

{{{{reflist}}}}

== Further reading ==

{{{{refbegin | 2}}}}
{citations}
{{{{refend}}}}


{{{{gene{chromosome}-stub}}}}
{footer}
"""

ENTREZ_CITE = """
<ref name="entrez">
{{{{cite web
| title = Entrez Gene: {name}
| url = http://www.ncbi.nlm.nih.gov/gene/{id}
| accessdate = {currentdate}
}}}}</ref>
"""

