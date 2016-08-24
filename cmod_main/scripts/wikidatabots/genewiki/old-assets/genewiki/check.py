# -*- coding: utf-8 -*-
'''
  Tries, as fast as possible, to check the presence of titles passed to it as
  the first command-line argument.
'''

api = 'http://en.wikipedia.org/w/api.php?action=query&titles={title}&prop=info&redirects&format=json'

def check(titles):
    import urllib, json
    titles = [titles] if isinstance(titles, str) else titles
    qtitles = [urllib.quote(x) for x in titles]
    querystr = '|'.join(qtitles)
    j = json.loads(urllib.urlopen(api.format(title=querystr)).read())
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

if __name__ == '__main__':
    import sys
    print check(sys.argv[1].split('|'))

