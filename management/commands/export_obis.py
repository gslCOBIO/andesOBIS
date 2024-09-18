from django.core.management.base import BaseCommand

from andesOBIS.views import make_event_from_cruise
from andesOBIS.views import make_obis_events

from shared_models.utils import get_active_cruise
from andesOBIS.models import Event
class Command(BaseCommand):
    def handle(self, **options):
        print("exporting obis")
        # e = make_event_from_cruise()
        make_obis_events()
