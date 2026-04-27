from django.core.management.base import BaseCommand

from analytics.tasks import fetch_analytics


class Command(BaseCommand):
    help = 'Fetch Instagram metrics for posted plans with Instagram media ids.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-id',
            type=int,
            help='Only refresh analytics for one WeeklyPlan id.',
        )

    def handle(self, *args, **options):
        updated_count = fetch_analytics(options.get('plan_id'))
        self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} analytics row(s).'))
