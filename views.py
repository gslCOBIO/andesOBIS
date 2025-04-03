import logging

from andesOBIS.models import Event, InvalidSpecies, Occurrence
from andesOBIS.serializers import EventSerializer
from shared_models.common_views import CommonListView, CommonSingleTableListView
from shared_models.mixins import AndesLoginRequiredMixin
from shared_models.utils import get_active_mission

from shared_models.models import Sample, Catch

from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated

logging.getLogger().setLevel(logging.DEBUG)


class EventListView(AndesLoginRequiredMixin, CommonListView):
    model = Event
    home_url_name = "index"
    field_list = [
        {"name": 'eventID', "class": "", "width": ""},
        {"name": 'eventType', "class": "", "width": ""},
        {"name": 'parentEventID'},
        {"name": 'eventDate', "class": "", "width": ""},
        {"name": 'year'},
        {"name": 'decimalLatitude'},
        {"name": 'decimalLongitude'},
        {"name": 'geodeticDatum'},
        {"name": 'coordinatePrecision'},
        {"name": 'coordinateUncertaintyInMeters'},
        {"name": 'continent'},
        {"name": 'maximumDepthInMeters'},
        {"name": 'minimumDepthInMeters'},
        {"name": 'language'},
        {"name": 'license'},
        {"name": 'institutionID'},
        {"name": 'institutionCode'},
        {"name": 'datasetID'},
        {"name": 'datasetName'},
        {"name": 'fieldNumber'},
        {"name": 'footprintWKT'},
        {"name": 'footprintSRS'},
        {"name": 'countryCode'},
        {"name": 'country'},
        {"name": 'eventRemarks'},
    ]

    def __init__(self, *args, **kwargs):
        super().__init__()
        print(self.queryset)
        return


class EventViewSet(ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    allowed_methods = ["GET"]



def make_obis_events():
    cruise = get_active_mission()
    top_parent = Event()
    top_parent._init_from_mission(cruise)
    top_parent.save()
    for set in Sample.objects.filter(cruise=cruise):
        print(set)
        if len(set.operations.filter(is_fishing=True)) == 0:
            continue
        set_event = Event(_parentEvent=top_parent)
        set_event._init_from_fishing_set(set)
        set_event.save()

        for catch in Catch.objects.filter(set=set):

            if catch.species.is_mixed_catch:
                pass
                # try:
                #     occurrence = Occurrence(_event=set_event)
                #     occurrence._init_from_mixed_catch(catch)
                #     occurrence.save()
                # except InvalidSpecies as exc:
                #     print(exc)
                #     pass
            else:
                try:
                    occurrence = Occurrence(_event=set_event)
                    occurrence._init_from_catch(catch)
                    occurrence.save()
                except InvalidSpecies as exc:
                    print(exc)
                    pass
