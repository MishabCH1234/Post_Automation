from django.conf import settings
from django.db import models

class WeeklyPlan(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_POSTED = 'posted'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_POSTED, 'Posted'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    content = models.TextField()
    scheduled_time = models.DateTimeField()
    image = models.FileField(upload_to='posts/', null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )

    def __str__(self):
        return self.title
