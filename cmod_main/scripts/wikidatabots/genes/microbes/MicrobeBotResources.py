import urllib.request
import requests
import pandas as pd
import MicrobeBotWDFunctions as wdo
import pprint
import time
__author__ = 'timputman'





def get_ref_microbe_taxids():
    """
    Download the latest bacterial genome assembly summary from the NCBI genome ftp site
    and generate a pd.DataFrame of relevant data for strain items based on taxids of the bacterial reference genomes.
    :return: pandas dataframe of bacteria reference genome data
    """
    assembly = urllib.request.urlretrieve("ftp://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt")

    columns = ['assembly_accession', 'bioproject', 'biosample', 'wgs_master', 'refseq_category', 'taxid',
               'species_taxid', 'organism_name', 'infraspecific_name', 'isolate', 'version_status', 'assembly_level',
               'release_type', 'genome_rep', 'seq_rel_date', 'asm_name', 'submitter', 'gbrs_paired_asm',
               'paired_asm_comp', 'ftp_path', 'excluded_from_refseq']

    data = pd.read_csv(assembly[0], sep="\t", dtype=object, skiprows=2, names=columns)
    data = data[data['refseq_category'] == 'reference genome']

    def sparql_qid(taxid):
        qidobj = wdo.WDSparqlQueries(string=taxid, prop='P685')
        return qidobj.wd_prop2qid()
    data['wd_qid'] = data['taxid'].apply(sparql_qid)
    return data


def mgi_qg_resources(taxid):
    """
    gathers and combines resources from MyGene.info and QuickGo REST APIs
    :param taxid:
    :return: dictionary with mgi data and updated with (goid, aspect, evidence)
    """
    def quick_go_query():
        """
        request to quick go REST API for all gene ontology term records for a given taxid
        :param taxid:
        :return:pandas dataframe
        """
        url = 'https://www.ebi.ac.uk/QuickGO/GAnnotation?format=tsv&tax={}'.format(taxid)
        data = urllib.request.urlretrieve(url)
        df = pd.read_csv(data[0], sep="\t")
        df_joined = pd.pivot_table(df, index=['ID'], values=['GO ID', 'Evidence', 'Aspect', 'With'], aggfunc=lambda x: list(x))
        goterms = {}
        for index, row in df_joined.iterrows():
            ecnumber = df_joined.loc[index]['With']
            ec2 = []
            for ec in ecnumber:
                if ec.startswith('EC:'):
                    ec2.append(ec)
                else:
                    ec2.append('None')
            goterms[index] = set(list(zip(df_joined.loc[index]['GO ID'],
                                          df_joined.loc[index]['Aspect'],
                                          ec2,
                                          df_joined.loc[index]['Evidence'])))

        return goterms

    def mygeneinfo_rest_query():
        """
        Downloads the latest list of microbial genes by taxid to a pandas dataframe
        :return: pandas data frame
        """
        url = 'http://mygene.info/v2/query/'
        params = dict(q="__all__", species=taxid, entrezonly="true", size="10000", fields="all")
        data = requests.get(url=url, params=params).json()
        # Reads mgi json hits into dataframe
        return data['hits']

    mgi_data = mygeneinfo_rest_query()
    qg_terms = quick_go_query()
    all_list = []
    for i in mgi_data:
        if 'locus_tag' not in i.keys():
            continue
        elif 'uniprot' not in i.keys():
            continue
        else:
            up = str(list(i['uniprot'].values())[0])
            if up in qg_terms.keys():
                i['GOTERMS'] = qg_terms[up]
            else:
                i['GOTERMS'] = {}
        all_list.append(i)

    return all_list


