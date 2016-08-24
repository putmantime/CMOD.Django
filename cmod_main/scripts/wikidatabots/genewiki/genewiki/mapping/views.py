from django.shortcuts import redirect
from django.conf import settings

from rest_framework import viewsets
from genewiki.mapping.models import Relationship, Lookup
from genewiki.mapping.serializers import RelationshipSerializer

import PBB_Core

class RelationshipViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Relationship.objects.all()
    serializer_class = RelationshipSerializer


def wiki_mapping(request, entrez_id):
    article_query = """
        SELECT ?article WHERE {
        ?cid wdt:P351 '"""+str(entrez_id)+"""'.
        ?cid wdt:P703 wd:Q5 . 
        OPTIONAL { ?cid rdfs:label ?label filter (lang(?label) = "en") .}
        ?article schema:about ?cid .
        ?article schema:inLanguage "en" .
        FILTER (SUBSTR(str(?article), 1, 25) = "https://en.wikipedia.org/") . 
        FILTER (SUBSTR(str(?article), 1, 38) != "https://en.wikipedia.org/wiki/Template")
        } 
        limit 1
    """
    wikidata_results = PBB_Core.WDItemEngine.execute_sparql_query(prefix=settings.PREFIX, query=article_query)['results']['bindings']
    article = ''
    for x in wikidata_results:
        article = x['article']['value']
    
    if wikidata_results:
        return redirect(article)
    else:
        return redirect('genewiki.wiki.views.article_create', entrez_id)

