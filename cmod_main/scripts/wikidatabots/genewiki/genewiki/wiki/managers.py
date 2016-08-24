from django.db import models


class BotManager(models.Manager):

    def get_random_bot(self):
        '''
          This is documented as being potentially expensive, we may want to do something like
          http://stackoverflow.com/a/6405601 instead
        '''
        return self.filter(service_type='wiki').order_by('?')[0]

    def get_pbb(self):
        return self.filter(service_type='wiki').first()


class ArticleManager(models.Manager):

    def all_infoboxes(self):
        return self.filter(article_type=self.model.INFOBOX).all()

    def get_infobox_for_entrez(self, entrez):
        title = 'Template:PBB/{0}'.format(entrez)
        return self.filter(title=title).first()

    def get_talk_for_entrez(self, entrez):
        pass

