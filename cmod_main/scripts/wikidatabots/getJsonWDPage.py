import pywikibot
import pprint
import ProteinBoxBotFunctions
import sys
import time
import datetime

pp = pprint.PrettyPrinter(indent=4)

# Login to wikidata
site = pywikibot.Site("wikidata", "wikidata")
# site = pywikibot.Site("wikidata", "test")
repo = site.data_repository()


# OR you may also get the site by language code/family:
# repo = pywikibot.getSite('wikidata', 'wikidata')
 
# We also can create a DataPage by its ID in two ways
# First by site and title:
#//data = pywikibot.DataPage(repo, "Q42")
#OR the second way by the ID number:
print "test: "+sys.argv[1]
data = ProteinBoxBotFunctions.getItem(site, sys.argv[1], "\\__")
pp.pprint(data)
ts = time.time()
st = datetime.datetime.fromtimestamp(ts).strftime('+0000000%Y-%m-%dT00:00:00Z')
print st
