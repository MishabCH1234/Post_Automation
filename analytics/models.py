from django.db import models

class PostAnalytics(models.Model):
    plan = models.OneToOneField('planner.WeeklyPlan', on_delete=models.CASCADE)
    likes = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    reach = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.plan}"
