import requests


def uniprot_acc_for_entrez_id(entrez):
    '''
        Returns either one reviewed uniprot id or None.
    '''
    payload = {
        'from': 'P_ENTREZGENEID',
        'to': 'ACC',
        'format': 'list',
        'reviewed': '',
        'query': entrez
    }
    response = requests.get('http://www.uniprot.org/mapping/', params=payload)
    accns = response.text.split('\n')
    for acc in [_f for _f in accns if _f]:
        if is_reviewed(acc):
            return acc
    return None


def is_reviewed(uniprot):
    url = 'http://www.uniprot.org/uniprot/?query=reviewed:yes+AND+accession:{}&format=list'.format(uniprot)
    return bool(requests.get(url).text.strip('\n'))

