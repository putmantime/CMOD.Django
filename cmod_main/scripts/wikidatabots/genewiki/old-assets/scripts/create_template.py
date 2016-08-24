# -*- coding: utf-8 -*-

'''
  Creates a Gene Wiki protein box template around a gene specified by
  the first argument passed to it on the command line.

  Usage: `python create_template.py <entrez_id>`
'''

import sys
from genewiki.mygeneinfo import parse

if len(sys.argv[1]) > 1:
    entrez = sys.argv[1]
    try: int(entrez)
    except ValueError:
        sys.stderr.write("Entrez ids must contain only digits.")
        sys.exit(1)
    sys.stdout.write(str(parse(entrez)))

