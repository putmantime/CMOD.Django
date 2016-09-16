import urllib.request
import gzip
import pandas as pd
import subprocess
import os, os.path
import glob
import shutil
from SPARQLWrapper import SPARQLWrapper, JSON

ref_taxids = ["251221", "115713", "471472", "272561", "300852", "36809", "224324", "309807", "243274", "197221",
              "227377", "208964", "242231", "257313", "386585", "585056", "585057", "685038", "1133852", "511145",
              "1125630", "393305", "223926", "269796", "176280", "210007", "208435", "160490", "272623", "226900",
              "224308", "441771", "413999", "272621", "233413", "83332", "525284", "243160", "189518", "85962",
              "272624", "122586", "568707", "300267", "214092", "312309", "295405", "93061", "568814", "171101",
              "226185", "333849", "272562", "321967", "169963", "196627", "272631", "272560", "1208660", "107806",
              "243275", "177416", "205918", "266834", "1028307", "198214", "380703", "71421", "272947", "324602",
              "243230", "198094", "260799", "281309", "272563", "220668", "246196", "100226", "272632", "272634",
              "365659", "99287", "220341", "243231", "224326", "160488", "190485", "871585", "716541", "272943",
              "362948", "702459", "190650", "265311", "264732", "211586", "190304", "749927", "206672", "194439",
              "402612", "394", "192222", "167539", "243090", "366394", "243277", "882", "223283"]


class PrepareRefSeqs(object):
    def __init__(self):
        self.tid_query = "SELECT ?taxid WHERE { ?species wdt:P171* wd:Q10876; wdt:P685 ?taxid; wdt:P2249 ?RefSeq. }"
        self.tids = self.query_results()
        print(self.tids)
        for tid in self.tids:
            self.generate_tracks_conf(tid)
            genome = self.get_ref_ftp_path(tid)
            with gzip.open(genome, 'rb') as f:
                file_content = f.read().decode().split('\n')
                seq = "".join(file_content[1:])
                seqlen = len(seq)
                f_genome = [file_content[0], seq]
                # display the genome data at the terminal
                full_genome = "\n".join(f_genome)
                refseq = file_content[0].lstrip(">").split()[0]
                jbrowse = [{"length": seqlen, "name": refseq, "seqChunkSize": 20000, "end": seqlen, "start": 0}]
                f.close()
            current_fasta = './reference_genomes/{}_reference.fasta'.format(tid)
            refseq_fasta = open(current_fasta, 'w')
            for line in f_genome:
                print(line, file=refseq_fasta)
            refseq_fasta.close()
            # run the jbrowse prepare-refseqs.pl perl script
            prep_rs = '../../static/cmod_main/JBrowse-1.12.1-dev/bin/prepare-refseqs.pl'
            subprocess.call([prep_rs, "--fasta", current_fasta,
                             "--out",
                             '../../static/cmod_main/JBrowse-1.12.1-dev/sparql_data/sparql_data_{}/'.format(tid)])

            print((full_genome[:200] + '...', jbrowse))

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
                  "SELECT ?start ?end ?uniqueID ?strand ?uri ?entrezGeneID ?name ?description",
                  "WHERE { ?gene wdt:P279 wd:Q7187; wdt:P703 ?strain; wdt:P351 ?uniqueID; wdt:P351 ?entrezGeneID;",
                  "wdt:P2393 ?name; rdfs:label ?description; wdt:P644 ?start; wdt:P645 ?end; wdt:P2548 ?wdstrand .",
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

