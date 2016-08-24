# README #

This repository contains the proteinBoxBots. ProteinBoxBots aim at enriching WikiData with Molecular life science databases (e.g. Entrez, Ensembl, Disease ontology, etc).

Different bots are made to import different resources (Genes, Diseases, Compounds). The bots are organized around two main libraries, being ProteinBoxBotFunctions.py and 
ProteinBoxBotKnowledge.py. The ProteinBoxBotFunctions.py contains different functions to interact with the WikiData api at https://www.wikidata.org/w/api.php. ProteinBoxBotKnowledge.py 
contains links to WikiData identifiers that are needed to create links in WikiData claims. e.g. To claim on which chromosome a gene is located, and make that claim contain a
link to WikiData entry of that chromosome, the identifier of that WikiData entry is stored in ProteinBoxBotKnowledge.py. 


