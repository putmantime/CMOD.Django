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
        self.taxids = self.execute_query()
        self.assembly_summary = self.aggregate_ftp_summaries()
        species_count = 0
        for tid in self.taxids:
            species_count += 1
            print(tid, species_count)
            self.generate_tracks_conf(tid)
            genome = self.get_ftp_file(taxid=tid, data=self.assembly_summary)
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


    @staticmethod
    def execute_query():
        tid_query = """
                SELECT DISTINCT ?taxid WHERE {
                {?strain wdt:P171* wd:Q764.}
                UNION{?strain wdt:P171* wd:Q10876.}
                ?strain wdt:P171 ?parent;
                wdt:P685 ?taxid.
                ?parent wdt:P105 wd:Q7432.
                ?gene wdt:P703 ?strain;
                wdt:P279 wd:Q7187.
                }"""

        taxids = []
        endpoint = SPARQLWrapper(endpoint="https://query.wikidata.org/sparql")
        endpoint.setQuery(tid_query)
        endpoint.setReturnFormat(JSON)
        wd_query = endpoint.query().convert()
        tid_results = wd_query['results']['bindings']
        for result in tid_results:
            taxids.append(result['taxid']['value'])
        return taxids

    @staticmethod
    def aggregate_ftp_summaries():
        """

        :return:

        """
        ftp_list = ['ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/Saccharomyces_cerevisiae/assembly_summary.txt',
                    'ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt'
                   ]
        columns = ['assembly_accession', 'bioproject', 'biosample', 'wgs_master', 'refseq_category', 'taxid',
                       'species_taxid', 'organism_name', 'infraspecific_name', 'isolate', 'version_status',
                       'assembly_level',
                       'release_type', 'genome_rep', 'seq_rel_date', 'asm_name', 'submitter', 'gbrs_paired_asm',
                       'paired_asm_comp', 'ftp_path', 'excluded_from_refseq']
        ftp_data = []
        for ftp_url in ftp_list:
            assembly = urllib.request.urlretrieve(ftp_url)
            data = pd.read_csv(assembly[0], sep="\t", dtype=object, skiprows=2, names=columns)
            ftp_data.append(data)
        newframe = pd.concat(ftp_data)
        return newframe

    @staticmethod
    def get_ftp_file(taxid, data):
        selected = data[data['taxid'] == taxid]

        ftp_path = selected.iloc[0]['ftp_path']
        file_name = ftp_path.split('/')[-1]
        url = ftp_path + '/' + file_name + '_genomic.fna.gz'
        genome = urllib.request.urlretrieve(url)[0]
        # return the genome fasta file as a tempfile
        return genome

    @staticmethod
    def generate_tracks_conf(taxid):
        """
        generates the tracks.conf file that holds the SPARQL query for JBrowse to get gene annotations from Wikidata
        :param taxid:
        :return: tracks.conf with formatted sparql query
        """
        # basic jbrowse configurations
        print("genes")
        jbrowse_genes_conf_prefix = '''
        [trackSelector]
        type = Faceted

        [tracks.genes_canvas_mod]
        key = Genes
        type = JBrowse/View/Track/CanvasFeatures
        storeClass = JBrowse/Store/SeqFeature/SPARQL
        urlTemplate = https://query.wikidata.org/sparql
        disablePreflight = true
        style.color = function(feature) { return '#5C99F3'; }
        fmtDetailValue_Name = function(name) { return 'alert(name)'; }
        '''

        # add each line to list
        jbrowse_genes_conf_prefix = jbrowse_genes_conf_prefix.split("\n")
        jbrowse_genes_conf_prefix = [x.lstrip() for x in jbrowse_genes_conf_prefix]

        # sparql query is in one long line...jbrowse was only taking first line of query when it was multiline (this held me up for a while)
        querygenes = [
                  "queryTemplate = PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/>",
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
        querygenes = " ".join(querygenes)

        jbrowse_genes_conf_prefix.append(querygenes)
        # create the tracks.conf file and print each line to it

        def ensure_dir(f):
            d = os.path.dirname(f)
            if not os.path.exists(d):
                os.makedirs(d)

        ensure_dir('../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/'.format(taxid))
        tracks_conf = open(
            '../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/tracks.conf'.format(taxid), 'w')
        for i in jbrowse_genes_conf_prefix:
            print(i, file=tracks_conf)

        print("operons")
        jbrowse_operons_conf_prefix = '''
        [tracks.operons_canvas_mod]
        key = Operons
        type = JBrowse/View/Track/CanvasFeatures
        storeClass = JBrowse/Store/SeqFeature/SPARQL
        urlTemplate = https://query.wikidata.org/sparql
        disablePreflight = true
        style.color = function(feature) { return '#385d94';}
        '''
        jbrowse_operons_conf_prefix = jbrowse_operons_conf_prefix.split("\n")
        jbrowse_operons_conf_prefix = [x.lstrip() for x in jbrowse_operons_conf_prefix]

        queryoperons = ["queryTemplate = PREFIX wdt: <http://www.wikidata.org/prop/direct/>",
                        "PREFIX wd: <http://www.wikidata.org/entity/> ",
                        "PREFIX qualifier: <http://www.wikidata.org/prop/qualifier/> ",
                        "SELECT ?uniqueID ?description ?strand ",
                        "(MIN(?gstart) AS ?start) ",
                        "(MAX(?gend) AS ?end) ?uri ",
                        "WHERE { ",
                        "?strain wdt:P685 '" + taxid + "'.",
                        "?operon wdt:P279 wd:Q139677; ",
                        "wdt:P703 ?strain; ",
                        "rdfs:label ?description; ",
                        "wdt:P2548 ?wdstrand; ",
                        "wdt:P527 ?genes. ",
                        "?genes wdt:P644 ?gstart; ",
                        "wdt:P645 ?gend. ",
                        "bind( IF(?wdstrand = wd:Q22809680, '1', '-1') as ?strand). ",
                        "bind(str(?operon) as ?uri) ",
                        "bind( strafter( str(?operon), \"entity/\" ) as ?uniqueID ).",
                        "} ",
                        "GROUP BY ?uniqueID ?description ?strand ?uri ?prefix"
                        ]
        queryoperons = " ".join(queryoperons)

        jbrowse_operons_conf_prefix.append(queryoperons)
        for i in jbrowse_operons_conf_prefix:
            print(i, file=tracks_conf)
        tracks_conf.close()


PrepareRefSeqs()

#
#
#
# class PrepareRefSeqs(object):
#     def __init__(self):
#         self.tid_query = """
#         SELECT DISTINCT ?taxid WHERE {
#         {?strain wdt:P171* wd:Q764.}
#   	    UNION{?strain wdt:P171* wd:Q10876.}
#         ?strain wdt:P171 ?parent;
#                 wdt:P685 ?taxid.
#   	    ?parent wdt:P105 wd:Q7432.
#   	    ?gene wdt:P703 ?strain;
#               wdt:P279 wd:Q7187.
#         }"""
#         self.tids = self.query_results()
#         print(self.tids)
#         species_count = 0
#         for tid in self.tids:
#             species_count += 1
#             print(species_count, tid)
#             self.generate_tracks_conf(tid)
#             genome = self.get_ref_ftp_path(tid)
#
#             with gzip.open(genome, 'rb') as f:
#                 chroms = {}
#                 current_fasta = f.read()
#
#                 with tempfile.NamedTemporaryFile() as temp:
#                     temp.write(current_fasta)
#                     temp.flush()
#
#                     prep_rs = '/Users/timputman/django-projects/cmod_dev/CMOD.Django/cmod_main/static/cmod_main/JBrowse-1.12.1-dev/bin/prepare-refseqs.pl'
#                     sub_args = [prep_rs, "--fasta", temp.name, "--out",
#                                 '/Users/timputman/django-projects/cmod_dev/CMOD.Django/cmod_main/static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/'.format(tid)]
#                     subprocess.call(sub_args)
#
#     def execute_query(self):
#         endpoint = SPARQLWrapper(endpoint="https://query.wikidata.org/sparql")
#         endpoint.setQuery(self.tid_query)
#         endpoint.setReturnFormat(JSON)
#         wd_query = endpoint.query().convert()
#         return wd_query['results']['bindings']
#
#     def query_results(self):
#         tid_results = self.execute_query()
#         taxids = []
#         for result in tid_results:
#             taxids.append(result['taxid']['value'])
#         return taxids
#
#     @staticmethod
#     def generate_tracks_conf(taxid):
#         """
#         generates the tracks.conf file that holds the SPARQL query for JBrowse to get gene annotations from Wikidata
#         :param taxid:
#         :return: tracks.conf with formatted sparql query
#         """
#         # basic jbrowse configurations
#         print("genes")
#         jbrowse_genes_conf_prefix = '''
#         [trackSelector]
#         type = Faceted
#
#         [tracks.genes_canvas_mod]
#         key = SPARQL Genes Tracks.conf
#         type = JBrowse/View/Track/CanvasFeatures
#         storeClass = JBrowse/Store/SeqFeature/SPARQL
#         urlTemplate = https://query.wikidata.org/sparql
#         disablePreflight = true
#         style.color = function(feature) { return '#FF00AC'; }
#         fmtDetailValue_Name = function(name) { return 'alert(name)'; }
#         '''
#
#         # add each line to list
#         jbrowse_genes_conf_prefix = jbrowse_genes_conf_prefix.split("\n")
#         jbrowse_genes_conf_prefix = [x.lstrip() for x in jbrowse_genes_conf_prefix]
#
#         # sparql query is in one long line...jbrowse was only taking first line of query when it was multiline (this held me up for a while)
#         querygenes = [
#                   "queryTemplate = PREFIX wdt: <http://www.wikidata.org/prop/direct/> PREFIX wd: <http://www.wikidata.org/entity/>",
#                   "PREFIX qualifier: <http://www.wikidata.org/prop/qualifier/>",
#                   "SELECT ?start ?end ?uniqueID ?strand ?uri ?entrezGeneID ?name ?description ?refSeq",
#                   "WHERE { ?gene wdt:P279 wd:Q7187; wdt:P703 ?strain; wdt:P351 ?uniqueID; wdt:P351 ?entrezGeneID;",
#                   "wdt:P2393 ?name; rdfs:label ?description; wdt:P644 ?start; wdt:P645 ?end; wdt:P2548 ?wdstrand ;",
#                   "p:P644 ?chr.",
#                   "OPTIONAL {?chr qualifier:P2249 ?refSeq.} FILTER(?refSeq = \"{ref}\") "
#                   "?strain wdt:P685",
#                   "'" + taxid + "'.",
#                   "bind( IF(?wdstrand = wd:Q22809680, '1', '-1') as ?strand). bind(str(?gene) as ?uri).",
#                   "filter ( !(xsd:integer(?start) > {end} || xsd:integer(?end) < {start}))",
#                   "}"
#                   ]
#         querygenes = " ".join(querygenes)
#
#         jbrowse_genes_conf_prefix.append(querygenes)
#         # create the tracks.conf file and print each line to it
#
#         def ensure_dir(f):
#             d = os.path.dirname(f)
#             if not os.path.exists(d):
#                 os.makedirs(d)
#
#         ensure_dir('../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/'.format(taxid))
#         tracks_conf = open(
#             '../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/tracks.conf'.format(taxid), 'w')
#         for i in jbrowse_genes_conf_prefix:
#             print(i, file=tracks_conf)
#
#         print("operons")
#         jbrowse_operons_conf_prefix = '''
#         [tracks.operons_canvas_mod]
#         key = Operons
#         type = JBrowse/View/Track/CanvasFeatures
#         storeClass = JBrowse/Store/SeqFeature/SPARQL
#         urlTemplate = https://query.wikidata.org/sparql
#         disablePreflight = true
#         style.color = function(feature) { return '#385d94';}
#         '''
#         jbrowse_operons_conf_prefix = jbrowse_operons_conf_prefix.split("\n")
#         jbrowse_operons_conf_prefix = [x.lstrip() for x in jbrowse_operons_conf_prefix]
#
#         queryoperons = ["queryTemplate = PREFIX wdt: <http://www.wikidata.org/prop/direct/>",
#                         "PREFIX wd: <http://www.wikidata.org/entity/> ",
#                         "PREFIX qualifier: <http://www.wikidata.org/prop/qualifier/> ",
#                         "SELECT ?uniqueID ?description ?strand ",
#                         "(MIN(?gstart) AS ?start) ",
#                         "(MAX(?gend) AS ?end) ?uri ",
#                         "WHERE { ",
#                         "?strain wdt:P685 '" + taxid + "'.",
#                         "?operon wdt:P279 wd:Q139677; ",
#                         "wdt:P703 ?strain; ",
#                         "rdfs:label ?description; ",
#                         "wdt:P2548 ?wdstrand; ",
#                         "wdt:P527 ?genes. ",
#                         "?genes wdt:P644 ?gstart; ",
#                         "wdt:P645 ?gend. ",
#                         "bind( IF(?wdstrand = wd:Q22809680, '1', '-1') as ?strand). ",
#                         "bind(str(?operon) as ?uri) ",
#                         "bind( strafter( str(?operon), \"entity/\" ) as ?uniqueID ).",
#                         "} ",
#                         "GROUP BY ?uniqueID ?description ?strand ?uri ?prefix"
#                         ]
#         queryoperons = " ".join(queryoperons)
#
#         jbrowse_operons_conf_prefix.append(queryoperons)
#         for i in jbrowse_operons_conf_prefix:
#             print(i, file=tracks_conf)
#         tracks_conf.close()
#
#
#
#
#
#     @staticmethod
#     def get_ref_ftp_path(ftp_url, taxid):
#         """
#         using taxid, get the ftp file path from the assembly summary file on NCBI's ftp site and retrieve the genome
#         sequence to use as ref seq in jbrowse
#         :param taxid:
#         :return:
#         """
#
#         assembly = urllib.request.urlretrieve()
#         columns = ['assembly_accession', 'bioproject', 'biosample', 'wgs_master', 'refseq_category', 'taxid',
#                    'species_taxid', 'organism_name', 'infraspecific_name', 'isolate', 'version_status',
#                    'assembly_level',
#                    'release_type', 'genome_rep', 'seq_rel_date', 'asm_name', 'submitter', 'gbrs_paired_asm',
#                    'paired_asm_comp', 'ftp_path', 'excluded_from_refseq']
#
#         data = pd.read_csv(assembly[0], sep="\t", dtype=object, skiprows=2, names=columns)
#         # get row with taxid
#         selected = data[data['taxid'] == taxid]
#
#         ftp_path = selected.iloc[0]['ftp_path']
#         file_name = ftp_path.split('/')[-1]
#         url = ftp_path + '/' + file_name + '_genomic.fna.gz'
#         genome = urllib.request.urlretrieve(url)[0]
#         # return the genome fasta file as a tempfile
#         return genome
#
#
#
# bacteria_ftp = "ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt"
# yeist_ftp = 'ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/Saccharomyces_cerevisiae/assembly_summary.txt'
# # new = PrepareRefSeqs()