#!usr/bin/env python
# -*- coding: utf-8 -*-

'''
Authors: 
  Andra Waagmeester (andra' at ' micelio.be)

This file is part of ProteinBoxBot.

ProteinBoxBot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ProteinBoxBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ProteinBoxBot.  If not, see <http://www.gnu.org/licenses/>.
'''

def getmyGeneInfoUrl():
    return 'http://mygene.info/v2/gene/'
    
def getHumanGenesUrl():
    return "http://mygene.info/v2/query?q=__all__&species=human&entrezonly=true&size=100000"
    
def getGeneAnnotationsURL():
    return "http://mygene.info/v2/gene/"
    
def getUniprotUrl():
    return "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+taxonomy%3a%3chttp%3a%2f%2fpurl.uniprot.org%2ftaxonomy%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0aSELECT+%3funiprot+%3fplabel+%3fecName+%0d%0a+++++++(group_concat(distinct+%3falias%3b+separator%3d%22%3b+%22)+as+%3fupalias)%0d%0a+++++++(group_concat(distinct+%3fpdb%3b+separator%3d%22%3b+%22)+as+%3fpdbid)%0d%0a+++++++(group_concat(distinct+%3frefseq%3b+separator%3d%22%3b+%22)+as+%3frefseqid)%0d%0a+++++++(group_concat(distinct+%3fensP%3b+separator%3d%22%3b+%22)+as+%3fensemblp)%0d%0aWHERE%0d%0a%7b%0d%0a%09%09%3funiprot+a+up%3aProtein+.%0d%0a%09%09%3funiprot+up%3aorganism+taxonomy%3a9606+.%0d%0a++++++++%3funiprot+rdfs%3alabel+%3fplabel+.%0d%0a++++++++%3funiprot+up%3aversion+%3fupversion+.%0d%0a++++++++OPTIONAL+%7b%3funiprot+up%3aalternativeName+%3fupAlias+.%0d%0a++++++++++++++++++%3fupAlias+up%3aecName+%3fecName+.%7d%0d%0a++++++++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fpdb+.%0d%0a+++++++++++++++++%3fpdb+up%3adatabase+database%3aPDB+.%7d%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3frefseq+.%0d%0a+++++++++++++++++%3frefseq+up%3adatabase+database%3aRefSeq+.%7d++%0d%0a++++++++OPTIONAL%7b%3funiprot+rdfs%3aseeAlso+%3fensT+.%0d%0a+++++++++++++++++%3fensT+up%3adatabase+database%3aEnsembl+.%0d%0a+++++++++++++++++%3fensT+up%3atranslatedTo+%3fensP+.%7d%0d%0a%7d%0d%0agroup+by+%3fupAlias+%3funiprot+%3fplabel+%3fecName&format=srj"

# def getGeneWikiLinks():
#    return "http://sparql.uniprot.org/sparql?query=PREFIX+up%3a%3chttp%3a%2f%2fpurl.uniprot.org%2funiprot%2f%3e+%0d%0aPREFIX+upc%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fcore%2f%3e%0d%0aPREFIX+database%3a%3chttp%3a%2f%2fpurl.uniprot.org%2fdatabase%2f%3e%0d%0a%0d%0aSELECT+*+%0d%0aWHERE%0d%0a%7b%0d%0a%09%09%3fprotein+rdfs%3aseeAlso+%3fgwiki+.%0d%0a++++++++%3fgwiki+upc%3adatabase+database%3aGeneWiki+.%0d%0a%7d&format=srj"