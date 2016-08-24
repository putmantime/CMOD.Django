from SPARQLWrapper import SPARQLWrapper, JSON

from raven import Client

try:
    import simplejson as json
except ImportError as e:
    import json
	
sparql = SPARQLWrapper("http://sparql.uniprot.org/")
sparql.setQuery("""
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX v: <http://www.wikidata.org/prop/statement/>
PREFIX up:<http://purl.uniprot.org/core/> 
PREFIX database:<http://purl.uniprot.org/database/>

SELECT DISTINCT ?wd_url ?uniprot ?proteinLabel (group_concat(distinct ?pfam ;separator="; ") as ?pfam_id) 
   (group_concat(distinct ?pdb; separator="; ") as ?pdbId)
   (group_concat(distinct ?refseq; separator="; ") as ?RefSeq_Id) WHERE {
SERVICE <http://wdqs-beta.wmflabs.org/bigdata/namespace/wdq/sparql>{
   ?wd_url wdt:P279 wd:Q8054 .
   ?wd_url rdfs:label ?proteinLabel .
   ?wd_url wdt:P352 ?wduniprot .
   FILTER(lang(?proteinLabel) = "en")
}
BIND(IRI(CONCAT("http://purl.uniprot.org/uniprot/", ?wduniprot)) as ?uniprot) 

?uniprot rdfs:seeAlso ?pfam .
?pfam up:database database:Pfam .
?uniprot rdfs:seeAlso ?pdb .
?pdb up:database database:PDB .
?uniprot rdfs:seeAlso ?refseq .
?refseq up:database database:RefSeq .
}
GROUP BY ?uniprot ?proteinLabel ?wd_url
""")
results = sparql.query().convert()