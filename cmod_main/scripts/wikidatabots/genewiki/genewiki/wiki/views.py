from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.conf import settings

from genewiki.wiki.models import Article

from genewiki.wiki.textutils import create, interwiki_link

import PBB_Core, urllib.parse


@require_http_methods(['GET', 'POST'])
def article_create(request, entrez_id):

    results = create(entrez_id)
    # We failed to gather information then return the ID error
    if results is None:
        return HttpResponse('Invalid or missing Entrez Identifier')

    titles = results.get('titles')
    article = Article.objects.get_infobox_for_entrez(entrez_id)
    title = wiki_title(entrez_id)

    vals = {'results': results,
            'article': article,
            'titles': titles,
            'title': title,
            'entrez': entrez_id}

    if request.method == 'POST':
        # Only assign this 'title' var internally if the online article status is False (not a Wikipedia page)
        uploadopt = request.POST.get('page_type')
        if uploadopt is None:
            return HttpResponse('Must select title option.')

        title = titles[uploadopt][0] if titles[uploadopt][1] is False else None

        # The page title that they wanted to create is already online
        if title is None:
            return HttpResponse('Article or template already exists.')

        vals['title'] = title
        content = results['stub']
        Article.objects.get_or_create(title=title, text=content, article_type=Article.PAGE, force_update=True)

        # create corresponding talk page with appropriate project banners
        talk_title = 'Talk:{0}'.format(title)
        talk_content = """{{WikiProjectBannerShell|
                          {{WikiProject Gene Wiki|class=stub|importance=low}}
                          {{Wikiproject MCB|class=stub|importance=low}}
                          }}"""
        Article.objects.get_or_create(title=talk_title, text=talk_content, article_type=Article.TALK, force_update=True)
        # create interwiki link
        interwiki_link(entrez_id, title)
        # save article again
        Article.objects.get_or_create(title=title, text=content, article_type=Article.PAGE, force_update=True)

        return redirect('genewiki.wiki.views.article_create', entrez_id)

    return render(request, 'wiki/create.jade', vals)


def wiki_title(entrez_id):
    article_query = """
        SELECT ?article WHERE {
        ?cid wdt:P351 '""" + str(entrez_id) + """'.
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
        if article is not None:
            title = article.split("/")
            str_title = urllib.parse.unquote(title[-1])
            return str_title

