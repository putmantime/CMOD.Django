# Based on http://www.michelepasin.org/blog/2011/07/18/inspecting-an-ontology-with-rdflib/

from rdflib import ConjunctiveGraph, Namespace, exceptions

from rdflib import URIRef, RDFS, RDF, BNode

import OWL

class OntoInspector(object):

    """Class that includes methods for querying an RDFS/OWL ontology"""

    def __init__(self, uri, language=""):
        super(OntoInspector, self).__init__()

        self.rdfGraph = ConjunctiveGraph()
        try:
            self.rdfGraph.parse(uri, format="xml")
        except:
            try:
                self.rdfGraph.parse(uri, format="n3")
            except:
                raise exceptions.Error("Could not parse the file! Is it a valid RDF/OWL ontology?")

        finally:
            # let's cache some useful info for faster access
            self.baseURI = self.get_OntologyURI() or uri
            self.allclasses = self.__getAllClasses(classPredicate)
            self.toplayer = self.__getTopclasses()
            self.tree = self.__getTree()


    def get_OntologyURI(self, ....):
        """
        In [15]: [x for x in o.rdfGraph.triples((None, RDF.type, OWL.Ontology))]
        Out[15]:
        [(rdflib.URIRef('http://purl.com/net/sails'),
          rdflib.URIRef('http://www.w3.org/1999/02/22-rdf-syntax-ns#type'),
          rdflib.URIRef('http://www.w3.org/2002/07/owl#Ontology'))]

        Mind that this will work only for OWL ontologies.
        In other cases we just return None, and use the URI passed at loading time
        """

        test = [x for x, y, z in self.rdfGraph.triples((None, RDF.type, OWL.Ontology))]

        if test:
            if return_as_string:
                return str(test[0])
            else:
                return test[0]
        else:
            return None

    def __getAllClasses(self, classPredicate = "", removeBlankNodes = True):
        """
        Extracts all the classes from a model
        We use the RDFS and OWL predicate by default; also, we extract non explicitly declared classes
        """

        rdfGraph = self.rdfGraph
        exit = []

        if not classPredicate:
            for s, v, o in rdfGraph.triples((None, RDF.type , OWL.Class)):
                exit.append(s)
            for s, v, o in rdfGraph.triples((None, RDF.type , RDFS.Class)):
                exit.append(s)

            # this extra routine makes sure we include classes not declared explicitly
            # eg when importing another onto and subclassing one of its classes...
            for s, v, o in rdfGraph.triples((None, RDFS.subClassOf , None)):
                if s not in exit:
                    exit.append(s)
                if o not in exit:
                    exit.append(o)

            # this extra routine includes classes found only in rdfs:domain and rdfs:range definitions
            for s, v, o in rdfGraph.triples((None, RDFS.domain , None)):
                if o not in exit:
                    exit.append(o)
            for s, v, o in rdfGraph.triples((None, RDFS.range , None)):
                if o not in exit:
                    exit.append(o)

        else:
            if classPredicate == "rdfs" or classPredicate == "rdf":
                for s, v, o in rdfGraph.triples((None, RDF.type , RDFS.Class)):
                    exit.append(s)
            elif classPredicate == "owl":
                for s, v, o in rdfGraph.triples((None, RDF.type , OWL.Class)):
                    exit.append(s)
            else:
                raise exceptions.Error("ClassPredicate must be either rdf, rdfs or owl")

        exit = remove_duplicates(exit)

        if removeBlankNodes:
            exit = [x for x in exit if not self.__isBlankNode(x)]

        return sort_uri_list_by_name(exit)


    def __getTopclasses(self, ....):
            pass


    def __getTree(self, ....):
            # todo
            pass