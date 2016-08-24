from genewiki.mapping.models import Relationship
from rest_framework import serializers


class RelationshipSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Relationship
        fields = ('id', 'entrez_id', 'title')
