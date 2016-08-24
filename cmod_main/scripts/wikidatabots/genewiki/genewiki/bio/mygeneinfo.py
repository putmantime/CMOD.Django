from django.conf import settings

from genewiki.bio.uniprot import uniprot_acc_for_entrez_id
from raven.contrib.django.raven_compat.models import client

import re, mygene


def findReviewedUniprotEntry(entries, entrez):
    '''
      Attempts to return the first reviewed entry in a given dict of dbname:id
      pairs for a gene's UniProt entries.
      If a reviewed entry is not found, it attempts to query Uniprot directly for one.
      If this still is unsuccessful, it returns one from TrEMBL at random.

      Arguments:
      - `entries`: a dict of entries, e.g {'Swiss-Prot':'12345', 'TrEMBL':'67890'}
    '''
    if not isinstance(entries, dict) and not entrez:
        return ''
    elif entrez:
        return uniprot_acc_for_entrez_id(entrez)

    if 'Swiss-Prot' in entries:
        entry = entries['Swiss-Prot']
    else:
        entry = entries['TrEMBL']

    if isinstance(entry, list):
        for acc in entry:
            if uniprot.isReviewed(acc):
                return acc
        # if no reviewed entries, check Uniprot directly
        canonical = uniprot_acc_for_entrez_id(entrez)
        if canonical:
            return canonical
        else:
            return entry[0]
    else:
        canonical = uniprot_acc_for_entrez_id(entrez)
        if canonical:
            return canonical
        else:
            return entry


def get_homolog(json_res):
    '''
      Returns the homologous gene for a given gene for the mouse taxon

      Arguments:
      - `json_res`:  the mygene.info json document for original gene
    '''
    if json_res.get('genes') is None:
        return None
    else:
        homologs = json_res.get('homologene').get('genes')
        # isolate our particular taxon (returns [[taxon, gene]])
        if homologs:
            pair = [x for x in homologs if x[0] == settings.MOUSE_TAXON_ID]
            if pair:
                return pair[0][1]
            else:
                return None
        else:
            return None


def get_response(entrez):
    mg = mygene.MyGeneInfo()
    try:
        root = mg.getgene(entrez, 'name,summary,entrezgene,uniprot,pdb,HGNC,symbol,alias,MIM,ec,homologene,ensembl,refseq,genomic_pos,go', species='human')
        meta = mg.metadata
        homolog = get_homolog(root)
        homolog = mg.getgene(homolog, 'name,summary,entrezgene,uniprot,pdb,HGNC,symbol,alias,MIM,ec,homologene,ensembl,refseq,genomic_pos,go') if homolog else None
        entrez = root.get('entrezgene')
        uniprot = findReviewedUniprotEntry(root.get('uniprot'), entrez)
        return root, meta, homolog, entrez, uniprot
    except Exception as e:
        client.captureException()
        return e

