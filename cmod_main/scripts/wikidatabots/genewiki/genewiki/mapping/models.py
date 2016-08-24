from django.db import models

from genewiki.mapping.managers import RelationshipManager


class Relationship(models.Model):
    entrez_id = models.IntegerField(blank=False)
    title = models.CharField(max_length=200, blank=False)

    updated = models.DateTimeField(auto_now=True)
    created = models.DateTimeField(auto_now_add=True)

    objects = RelationshipManager()

    def __unicode__(self):
        return '{0} << >> {1}'.format(self.entrez_id, self.title)


class Lookup(models.Model):
    relationship = models.ForeignKey(Relationship, blank=False)
    created = models.DateTimeField(auto_now_add=True)
