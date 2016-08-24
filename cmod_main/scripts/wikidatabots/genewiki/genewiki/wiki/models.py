from django.db import models
from django.conf import settings

from genewiki.wiki.managers import BotManager, ArticleManager

from raven.contrib.django.raven_compat.models import client

import mwclient, re, logging
from mwclient.errors import *
logger = logging.getLogger(__name__)


class Bot(models.Model):
    username = models.CharField(max_length=200, blank=False)
    password = models.CharField(max_length=200, blank=False)

    SERVICE_TYPE_CHOICE = (
        ('wiki', 'Wikipedia User'),
        ('commons', 'Wikimedia Commons User'),
        ('data', 'Wikidata User'),
    )
    service_type = models.CharField(max_length=10, choices=SERVICE_TYPE_CHOICE, blank=True, default='wiki')

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = BotManager()

    def connection(self):
        useragent = 'Protein Box Bot, Run by The Scripps Research Institute: nanis@scripps.edu'
        connection = mwclient.Site(('https', settings.BASE_SITE), clients_useragent=useragent)

        connection.login(self.username, self.password)
        return connection

    def previous_actions(self, limit=500):
        '''
            Prints the last 500 actions (title) the bot has taken
        '''
        connection = self.connection()
        lists = connection.usercontributions(self.username, start=None, end=None, dir='older', namespace=None, prop=None, show=None, limit=limit)
        for item in lists:
            print((item['title']))

    def fetch_update_articles(self):
        connection = self.connection()
        gpb = connection.Pages['Template:GNF_Protein_box']
        for page in gpb.embeddedin('10'):
            if 'Template:PBB/' in page.name:
                article, created = Article.objects.get_or_create(title=page.name, article_type=Article.INFOBOX)
                article.text = page.edit()
                article.save()
                if created:
                    logger.info('Article Added', exc_info=True, extra={'article': article, 'title': page.name})

    def __unicode__(self):
        return '{0} ({1})'.format(self.username, self.service_type)


class Article(models.Model):
    title = models.CharField(max_length=200, blank=False)
    text = models.TextField()

    PAGE = 0
    INFOBOX = 1
    TEMPLATE = 2
    TALK = 3
    ARTICLE_TYPE_CHOICE = (
        (PAGE, 'Standard Page'),
        (INFOBOX, 'Infobox'),
        (TEMPLATE, 'Template'),
        (TALK, 'Talk page'),
    )
    article_type = models.IntegerField(max_length=1, choices=ARTICLE_TYPE_CHOICE, blank=True, default=PAGE)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)
    force_update = models.BooleanField(default=False)

    objects = ArticleManager()

    def __unicode__(self):
        return '{0}'.format(self.title)

    class Meta:
        ordering = ('-updated',)

    def url_for_article(self):
        return 'http://{0}/wiki/{1}'.format(settings.BASE_SITE, self.title)

    def get_page(self):
        bot = Bot.objects.get_pbb()
        connection = bot.connection()
        return connection.Pages[self.title]

    def bots_allowed(self):
        '''
          Returns true if the deny_bots regex finds no matches.
        '''
        return not (re.search(r'\{\{(nobots|bots\|(allow=none|deny=.*?' +
                              "ProteinBoxBot" + r'.*?|optout=all|deny=all))\}\}',
                              self.text))

    def write(self, proteinbox=None, summary=None):
        '''
          Writes the wikitext representation of the protein box to MediaWiki.
          Returns (result, None) if successful, or (None, Error) if not.
          Arguments:
          - `proteinbox`: an updated proteinbox to write
        '''
        page = self.get_page()

        if not self.bots_allowed():
            logger.warn('Bots Blocked', exc_info=True, extra={'page': page, 'bot': self})

        try:
            result = page.save(self.text, summary, minor=True)
            self.force_update = False
            self.save()

        except MwClientError:
            client.captureException
