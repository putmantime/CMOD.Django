import urllib.request
import gzip
import pandas as pd
import subprocess
import os, os.path
import glob
import shutil
import tempfile
from SPARQLWrapper import SPARQLWrapper, JSON


class PrepareRefSeqs(object):
    def __init__(self):
        self.tid_query = "SELECT ?taxid WHERE { ?species wdt:P171* wd:Q10876; wdt:P685 ?taxid; wdt:P2249 ?RefSeq. }"
        self.tids = self.query_results()
        species_count = 0
        for tid in self.tids:
            species_count += 1
            print(species_count, tid)
            self.generate_tracks_conf(tid)
            genome = self.get_ref_ftp_path(tid)

            with gzip.open(genome, 'rb') as f:
                chroms = {}
                current_fasta = f.read()

                with tempfile.NamedTemporaryFile() as temp:
                    temp.write(current_fasta)
                    temp.flush()

                    prep_rs = '/Users/timputman/django-projects/cmod_dev/CMOD.Django/cmod_main/static/cmod_main/JBrowse-1.12.1-dev/bin/prepare-refseqs.pl'
                    sub_args = [prep_rs, "--fasta", temp.name, "--out",
                                '/Users/timputman/django-projects/cmod_dev/CMOD.Django/cmod_main/static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/'.format(tid)]
                    subprocess.call(sub_args)

    def execute_query(self):
        endpoint = SPARQLWrapper(endpoint="https://query.wikidata.org/sparql")
        endpoint.setQuery(self.tid_query)
        endpoint.setReturnFormat(JSON)
        wd_query = endpoint.query().convert()
        return wd_query['results']['bindings']

    def query_results(self):
        tid_results = self.execute_query()
        taxids = []
        for result in tid_results:
            taxids.append(result['taxid']['value'])
        return taxids

    @staticmethod
    def generate_tracks_conf(taxid):
        """
        generates the tracks.conf file that holds the SPARQL query for JBrowse to get gene annotations from Wikidata
        :param taxid:
        :return: tracks.conf with formatted sparql query
        """
        # basic jbrowse configurations
        jbrowse_conf_prefix = '''[tracks.genes_canvas_mod]
        key = SPARQL Genes Tracks.conf
        type = JBrowse/View/Track/CanvasFeatures
        storeClass = JBrowse/Store/SeqFeature/SPARQL
        urlTemplate = https://query.wikidata.org/sparql
        disablePreflight = true'''
        # add each line to list
        jbrowse_conf_prefix = jbrowse_conf_prefix.split("\n")
        jbrowse_conf_prefix = [x.lstrip() for x in jbrowse_conf_prefix]
        # sparql query is in one long line...jbrowse was only taking first line of query when it was multiline (this held me up for a while)
        query1 = ["queryTemplate = PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/>",
                  "PREFIX qualifier: <http://www.wikidata.org/prop/qualifier/>",
                  "SELECT ?start ?end ?uniqueID ?strand ?uri ?entrezGeneID ?name ?description ?refSeq",
                  "WHERE { ?gene wdt:P279 wd:Q7187; wdt:P703 ?strain; wdt:P351 ?uniqueID; wdt:P351 ?entrezGeneID;",
                  "wdt:P2393 ?name; rdfs:label ?description; wdt:P644 ?start; wdt:P645 ?end; wdt:P2548 ?wdstrand ;",
                  "p:P644 ?chr.",
                  "OPTIONAL {?chr qualifier:P2249 ?refSeq.} FILTER(?refSeq = \"{ref}\") "
                  "?strain wdt:P685",
                  "'" + taxid + "'.",
                  "bind( IF(?wdstrand = wd:Q22809680, '1', '-1') as ?strand). bind(str(?gene) as ?uri).",
                  "filter ( !(xsd:integer(?start) > {end} || xsd:integer(?end) < {start}))",
                  "}"
                  ]
        query = " ".join(query1)

        jbrowse_conf_prefix.append(query)
        # create the tracks.conf file and print each line to it

        def ensure_dir(f):
            d = os.path.dirname(f)
            if not os.path.exists(d):
                os.makedirs(d)

        ensure_dir('../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/'.format(taxid))
        tracks_conf = open(
            '../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/tracks.conf'.format(taxid), 'w')
        for i in jbrowse_conf_prefix:
            print(i, file=tracks_conf)
        tracks_conf.close()

    @staticmethod
    def get_ref_ftp_path(taxid):
        """
        using taxid, get the ftp file path from the assembly summary file on NCBI's ftp site and retrieve the genome
        sequence to use as ref seq in jbrowse
        :param taxid:
        :return:
        """

        assembly = urllib.request.urlretrieve("ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt")
        columns = ['assembly_accession', 'bioproject', 'biosample', 'wgs_master', 'refseq_category', 'taxid',
                   'species_taxid', 'organism_name', 'infraspecific_name', 'isolate', 'version_status',
                   'assembly_level',
                   'release_type', 'genome_rep', 'seq_rel_date', 'asm_name', 'submitter', 'gbrs_paired_asm',
                   'paired_asm_comp', 'ftp_path', 'excluded_from_refseq']

        data = pd.read_csv(assembly[0], sep="\t", dtype=object, skiprows=2, names=columns)
        # get row with taxid
        selected = data[data['taxid'] == taxid]

        ftp_path = selected.iloc[0]['ftp_path']
        file_name = ftp_path.split('/')[-1]
        url = ftp_path + '/' + file_name + '_genomic.fna.gz'
        genome = urllib.request.urlretrieve(url)[0]
        # return the genome fasta file as a tempfile
        return genome

tester = PrepareRefSeqs()