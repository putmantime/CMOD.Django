# -*- coding: utf-8 -*-

'''
  gene2pubmed/redis.py

  Interface for a redis key:value store for rapid retrieval of pubmed:gene
  information.

  Requires redis (the server) and redis (the python module).
  Install the server according to instructions at http://redis.io.
'''

import subprocess, gzip

try:
    import redis
except ImportError:
    print("You must have the python redis adaptor installed.")
    raise

g2p_remote_file='ftp://ftp.ncbi.nih.gov/gene/DATA/gene2pubmed.gz'

def download_g2p():
    """Downloads the gene2pubmed file at
    ftp://ftp.ncbi.nih.gov/gene/DATA/gene2pubmed.gz
    """
    subprocess.check_call(["curl", "-O", g2p_remote_file])
    return "gene2pubmed.gz"


def init_redis(host='localhost', port=6379, db=1):
    ''' Returns a connection to the redis server with the specified options.
    Defaults localhost:6379, db 1.
    '''
    return redis.StrictRedis(host, port, db)



def import_to_redis(gene2pubmed_file, redis_connection, chatty=True):
    ''' Imports the data in a gene2pubmed file into redis.
    The data is stored in two parallel indexes:
    1. gene_id => set(pubmed_ids)
    2. pubmed_id => number of genes it cites
    Each gene key is prefixed with g: (i.e. g:1017) and each pmid prefixed with
    p: (i.e. p:12345) to avoid conflict between gene ids and pmids as key names.
    '''
    r = redis_connection
    with gzip.open(gene2pubmed_file, 'rb') as infile:
        if chatty: print("loading human genes...")
        human_entries = filter(lambda line: line.startswith('9606'),
                               infile.readlines())
        if chatty: print("loading data into redis...")
        # remove all previous data
        r.flushdb()
        for line in human_entries:
            line = line.split('\t')
            gene = 'g:'+line[1]
            pmid = 'p:'+line[2].rstrip('\n')
            if chatty: print("{}\t{}\r".format(gene, pmid)),
            # add each pmid to a set with the gene as a key
            r.sadd(gene, pmid)
            # increment the count on the pmid
            r.incr(pmid)
        if chatty: print


def get_pmids(gene, redis_connection, limit=None):
    '''Returns the pmids associated with a gene, with an optional limit (i.e.
    if a pmid references >= that number of genes, it is excluded).'''
    r = redis_connection
    if not gene.startswith('g:'):
        gene = 'g:'+gene
    pmids = []
    for pmid in r.smembers(gene):
        if limit and int(r.get(pmid)) < limit:
            pmids.append(pmid.replace('p:',''))
        elif not limit:
            pmids.append(pmid.replace('p:',''))
    return pmids


def fullstart():
    '''Downloads the most recent gene2pubmed file and imports into redis.
    Returns a connection to the redis server used (uses default options).
    '''
    r = init_redis()
    import_to_redis(download_g2p(), r)
    return r

if __name__ == '__main__':
    go = raw_input("""Fully initialize redis database?
This deletes all information stored on Redis DB1. [no] """)
    if not go or go.startswith('n'):
        print("Initialization cancelled.")
    else:
        fullstart()
