from django.core.management.base import BaseCommand

from planner.models import WeeklyPlan
from scheduler.tasks import process_plan


class Command(BaseCommand):
    help = 'Queue pending or failed weekly plans for image generation.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            default=WeeklyPlan.STATUS_PENDING,
            choices=[
                WeeklyPlan.STATUS_PENDING,
                WeeklyPlan.STATUS_FAILED,
                WeeklyPlan.STATUS_PROCESSING,
                WeeklyPlan.STATUS_SCHEDULED,
            ],
            help='Only queue plans with this status.',
        )

    def handle(self, *args, **options):
        plans = WeeklyPlan.objects.filter(status=options['status']).order_by('id')
        queued_count = 0

        for plan in plans:
            process_plan.delay(plan.id)
            queued_count += 1

        self.stdout.write(self.style.SUCCESS(f'Queued {queued_count} plan(s).'))
