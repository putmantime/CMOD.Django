

import sys, re, argparse, urllib
import mygeneinfo as mygene

class GeneWiki(object):

    def names_and_entrez(self):
        '''
          Returns a tuple (name, entrez) for all articles in the Gene Wiki
          where the entrez corresponds to the PBB template being used.
        '''
        for page in self.articles(strict=False):
            text = page.edit()
            match = re.search(r'\{\{\\s?PBB\s?\|\s?geneid=\s?([\d]*)\s?\}\}', text)
            if (match) and page.namespace == 0:
                yield urllib.quote(page.name.replace(' ','_')), match.group(1)


    def names_and_entrez_to_file(self, outfilename="/tmp/name_entrez.txt"):
        out = open(outfilename, 'w')
        out.write("Page_name\tEntrez_id\n")
        for page, entrez in self.names_and_entrez():
            out.write("{}\t{}\n".format(page, entrez))
        out.close()


    def upload(self, title, content):
        page = self.wp.Pages[title]
        if title.startswith('Template:PBB/'):
            summary = 'Created new GNF Protein box template for gene {} (user requested).'.format(title.replace('Template:PBB/',''))
        else:
            summary = 'Created new article stub (user requested).'

        try:
            page.save(content, summary)
            return 0
        except mwclient.errors.MwClientError:
            return 1
        except Exception:
            return 2


    def previous_actions(self):
        '''
          Prints the last 500 actions (title) the bot has taken
        '''
        lists = gw.wp.usercontributions(settings.wiki_user, start=None, end=None, dir='older', namespace=None, prop=None, show=None, limit=500)
        for item in lists:
            print item['title']
