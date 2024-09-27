from django.core.management.base import BaseCommand

from andesOBIS.views import make_obis_events

class Command(BaseCommand):
    def handle(self, **options):
        print("exporting obis")
        make_obis_events()
