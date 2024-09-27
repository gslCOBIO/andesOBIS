import logging

from andesOBIS.models import Event, InvalidSpecies, Occurrence
from shared_models.models import Cruise, Set, Operation
from ecosystem_survey.models import Catch

# from andesOBIS.forms import EventForm

from shared_models.common_views import CommonCreateView
from shared_models.mixins import AndesLeadRequiredMixin

from shared_models.utils import get_active_cruise





# class EventCreateView(AndesLeadRequiredMixin, CommonCreateView):
#     model = Event
#     form_class = EventForm


def make_obis_events():


    cruise = get_active_cruise()
    top_parent = Event()
    top_parent._init_from_cruise(cruise)
    top_parent.save()


    for set in Set.objects.filter(cruise=cruise):
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







