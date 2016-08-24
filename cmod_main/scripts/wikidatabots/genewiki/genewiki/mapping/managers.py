from django.db import models


class RelationshipManager(models.Manager):

    def get_for_entrez(self, entrez):
        return self.filter(entrez_id=entrez).first()

    def get_title_for_entrez(self, entrez):
        return self.filter(entrez_id=entrez).values_list('title', flat=True).first()


