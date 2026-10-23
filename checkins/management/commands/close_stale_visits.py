from django.core.management.base import BaseCommand

from checkins.models import Visit


class Command(BaseCommand):
    help = "Close visits with no scan out after 3 hours. Run on a schedule, e.g. every 15 minutes."

    def handle(self, *args, **options):
        closed = Visit.objects.close_stale()
        self.stdout.write(f"Closed {closed} visit(s).")
