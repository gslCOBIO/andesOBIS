
from andesOBIS.models import Event
from django import forms

class EventForm(forms.ModelForm):

    class Meta:
        model = Event
        fields = [
            'eventID',
            'eventType',
            '_parentEvent',
            '_event_start_dt',
            '_event_start_dt_p',
            '_event_end_dt',
            '_event_end_dt_p',
            'decimalLatitude',
            'decimalLongitude',
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
