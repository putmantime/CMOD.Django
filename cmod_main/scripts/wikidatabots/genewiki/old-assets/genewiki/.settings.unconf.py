# -*- coding: utf-8 -*-

'''
  ATTENTION:
  If this is a new installation of pygenewiki, edit this file (settings.example.py)
  with your username and password for wikipedia and any other custom settings
  and save it as settings.py in this directory. Modules rely on settings.py
  being present to operate.
'''


'''
Template Settings:
The page_prefix is the "namespace" of the infoboxes. All the respective pages are
in <base_site>/wiki/<page_prefix><entrez id>.
The template_name is the name of the template that the parser attempts to find
when parsing raw wikitext. It immediately follows the opening brackets.
'''
base_site = "en.wikipedia.org"
page_prefix = "Template:PBB/"
template_name = "GNF_Protein_box"


'''
Wikipedia User Settings:
This user should have bot and editing privileges.
'''
wiki_user = "{wpuser}"
wiki_pass = "{wppass}"


'''
Wikimedia Commons Settings:
These should be filled in if uploading images of proteins.
To use the same name and password as Wikipedia, leave these
blank.
'''
commons_user = "{cuser}"
commons_pass = "{cpass}"


'''
Pymol Configuration:
Directs to the installation path of pymol (www.pymol.org) molecular rendering
system. Value should be an absolute path to the pymol binary.
'''
pymol = "{pymol}"


'''
MyGene.Info Configuration
These are fairly static and should not need to be changed.
'''
mygene_base = "http://mygene.info/gene/"
mygene_meta = "http://mygene.info/metadata"
uniprot_url = "http://www.uniprot.org/uniprot/"


'''
ProteinBoxBot Configuration:
pbbhome is the root for all of pbb's working files, including a log and a
store of failed infoboxes, as well as any rendered PDB images.
'''
pbbhome = "{pbbhome}"
