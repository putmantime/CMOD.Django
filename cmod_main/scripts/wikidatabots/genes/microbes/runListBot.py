__author__ = 'timputman'


import MicrobeBotResources as MBR
import MicrobeBotGenes as MBG
import MicrobeBotProteins as MBP
import MicrobeBotEncoder as MBE
import MicrobeBotStrains as MBS
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../ProteinBoxBot_Core")
import PBB_login
import datetime

__author__ = 'timputman'




# Login to Wikidata with bot credentials
login = PBB_login.WDLogin(sys.argv[1], sys.argv[2])

# Retrieve Current Bacterial Reference Genomes from NCBI
print('Retrieving current list of NCBI Bacterial Reference Genomes')
print('Standby...')

runs_list = [115713, 211586, 100226, 568707, 226185, 394, 243090, 196627, 190485, 386585, 333849, 264732, 1133852,
               243231, 871585, 257313, 511145, 441771, 309807, 272560, 413999, 272562, 223283, 224308, 272563, 402612,
               220341, 321967, 246196, 190650, 366394, 260799, 224324, 362948, 233413, 36809, 243274, 198094, 206672,
               266834, 1028307, 226900, 1208660, 99287, 243160, 365659, 281309, 205918, 265311, 585056, 197221, 749927,
               160490, 300267, 685038, 272623, 272624, 272631, 272632, 272634, 702459, 220668, 716541]

taxids = {}
count = 0
genome_records = MBR.get_ref_microbe_taxids()
for i in runs_list:
    count += 1
    taxids['run{}'.format(count)] = i
print('{} reference genomes retrieved'.format(genome_records.shape[0]))

genome_log = open('{}_{}.log'.format(sys.argv[3], sys.argv[4]), 'w')

print('{} {}'.format(sys.argv[3], sys.argv[4]), 'start time: {}'.format(datetime.datetime.now()), file=genome_log)

for tid in taxids[sys.argv[3]]:
    spec_strain = genome_records[genome_records['taxid'] == tid]

    print('taxa: {} {}'.format(spec_strain.iloc[0]['organism_name'], spec_strain.iloc[0]['taxid']), file=genome_log)
    # Check for the organism wikidata item and skip if not created
    if spec_strain.iloc[0]['wd_qid'] is 'None':
        print('No Wikidata item for {}'.format(spec_strain['organism_name']), file=genome_log)
        continue
    # Retrieve gene and protein records from UniProt and Mygene.info by taxid
    print('Retrieving gene records for {} taxid:{}'.format(spec_strain.iloc[0]['organism_name'], tid))
    gene_records = MBR.mgi_qg_resources(tid)  # PANDAS DataFrame
    print('{} gene_records retrieved'.format(len(gene_records)), file=genome_log)
    # Iterate through gene_records for reading and writing to Wikidata
    print('Commencing {} bot run  for {}'.format(sys.argv[4], spec_strain.iloc[0]['organism_name']))
    gene_count = 0
    for record in gene_records:

        print('{}/{}'.format(gene_count, len(gene_records)), spec_strain['organism_name'])
        if sys.argv[4] == 'genes':
            gene = MBG.wd_item_construction(record, spec_strain, login)
            if gene == 'success':
                gene_count += 1
        if sys.argv[4] == 'proteins':
            protein = MBP.wd_item_construction(record, spec_strain, login)
            if protein == 'success':
                gene_count += 1
        if sys.argv[4] == 'encoder':
            encoder = MBE.encodes(record, login)
            if encoder == 'success':
                gene_count += 1
        if sys.argv[4] == 'strains':
            strains = MBS.organism_item_creator(record, login)

    print('{}/{} items succesfully written'.format(gene_count, len(gene_records)), file=genome_log)
print('end time: {}'.format(datetime.datetime.now()), file=genome_log)
genome_log.close()
