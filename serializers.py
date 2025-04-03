
from andesOBIS.models import Event
from rest_framework import serializers


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = [
            'eventID',
            'eventType',
            'parentEventID',
            'eventDate',
            'year',
            'decimalLatitude',
            'decimalLongitude',
            'geodeticDatum',
            'coordinatePrecision',
            'coordinateUncertaintyInMeters',
            'geodeticDatum',
            'continent',
            'maximumDepthInMeters',
            'minimumDepthInMeters',
            'language',
            'license',
            'institutionID',
            'institutionCode',
            'datasetID',
            'datasetName',
            'fieldNumber',
            'footprintWKT',
            'footprintSRS',
            'countryCode',
            'country',
            'eventRemarks',
        ]