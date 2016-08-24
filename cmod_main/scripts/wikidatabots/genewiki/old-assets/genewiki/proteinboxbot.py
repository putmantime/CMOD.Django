
import wikitext, mygeneinfo, genewiki
import re, datetime, os, requests

from mwclient.errors import *

class ProteinBoxBot(object):

    def update(self, page):
        """
          Returns an updated infobox and summary from data gathered from the
          specified page.

          Arguments:
          - `page`: a mwclient Page
        """
        entrez = self.extractEntrezFromPageName(page)
        # Dictionary of fields to build a ProteinBox from
        mgibox = mygeneinfo.parse(entrez)

        # Returns processed ProteinBox object
        wptext = wikitext.parse(page.edit())
        # Run the comparision between the current box online
        # and the dictionary just generated from mygene
        return wptext.updateWith(mgibox)


    def write(self, page, proteinbox, summary):
        """
          Writes the wikitext representation of the protein box to MediaWiki.

          Returns (result, None) if successful, or (None, Error) if not.

          Arguments:
          - `page`: a mwclient.Page to write to
          - `proteinbox`: an updated proteinbox to write
        """
        error = None

        if not wikitext.bots_allowed(page.edit()):
            return (None, Exception("Bot edits prohibited."))

        try:
            result = page.save(str(proteinbox), summary, minor=True)
            return (result, None)
        except MwClientError as e:
            error = e
        return (None, error)


    def run(self, run_only=None, skip=[], verbose=True, debug=True):
        """
          Arguments:
          - `run_only`: a list of page names to update
          - `skip`: a list of already-parsed entrez ids or page names
          - `verbose`: be chatty
        """

        def run_only_generator():
            for page in run_only:
                page = ("Template:PBB/"+str(page)
                        if isinstance(page, int) else page)
                yield self.genewiki.wp.Pages[page]

        # Even if inputted as numbers, make them proper unicode strings
        skip = [unicode(x) for x in skip]

        # Run all the "Template:PBB/" Pages if no IDs were explicitly passed in
        source = (self.genewiki.infoboxes
                  if not run_only else run_only_generator)

        for infobox in source():
            if debug and verbose: print("Updating "+infobox.name)

            try:
                # 1) The updated ProteinBox object
                # 2) the delta message
                # 3) the delta dictionary
                updated, summary, updatedfields = self.update(infobox)
            except Exception as err:
                message = 'Failed to edit {title}. Error: {error}'.format(
                        title=infobox.name, error=err)
                self.logger(1, message, infobox.name, verbose)

            if debug:
                print(str(updated)+ "\n" +summary)
            else:
                # This is where data is written
                result, err = self.write(infobox, updated, summary)
                message = ''
                if result:
                    if 'oldrevid' in result:
                        message = (
                            '''Successfully edited {title}:
Old revision: {old}
New revision: {new}'''
                            .format(title = result['title'],
                                    old = result['oldrevid'],
                                    new = result['newrevid']))
                        for field in updatedfields:
                            message = (message+"\n{}: '{}' => '{}'"
                                       .format(field,
                                               updatedfields[field][0],
                                               updatedfields[field][1]))
                    else:
                        message = ('''No change was made to {title}.'''
                                   .format(title=result['title']))
                    self.logger(0, message, result['title'], verbose)
                else:
                    pass
                    message = 'Failed to edit {title}. Error: {error}'.format( title = infobox.name, error = err)
                    self.logger(1, message, infobox.name, verbose)

def main():
    bot = ProteinBoxBot(genewiki.GeneWiki())
    bot.run()


if __name__ == '__main__':
    main()
