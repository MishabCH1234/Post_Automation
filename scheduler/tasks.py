from celery import shared_task
from planner.models import WeeklyPlan
from generator.service import generate_image_bytes
import requests
from django.core.files.base import ContentFile
from django.conf import settings
from urllib.parse import urljoin

@shared_task(bind=True, max_retries=3)
def process_plan(self, plan_id):
    plan = None
    try:
        plan = WeeklyPlan.objects.get(id=plan_id)
        plan.status = WeeklyPlan.STATUS_PROCESSING
        plan.save(update_fields=['status'])

        # Generate Image
        prompt = f"{plan.title} - {plan.content}"
        image_content = generate_image_bytes(prompt)

        plan.image.save(
            f"{plan.id}.png",
            ContentFile(image_content)
        )
        plan.status = WeeklyPlan.STATUS_SCHEDULED
        plan.save(update_fields=['image', 'status'])

        # Schedule Post
        schedule_post.apply_async(
            args=[plan.id],
            eta=plan.scheduled_time
        )

    except Exception as e:
        if plan is not None and self.request.retries + 1 >= self.max_retries:
            plan.status = WeeklyPlan.STATUS_FAILED
            plan.save(update_fields=['status'])
        self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=3)
def schedule_post(self, plan_id):
    plan = None
    try:
        plan = WeeklyPlan.objects.get(id=plan_id)
        user_profile = plan.user.userprofile

        token = user_profile.get_token()
        if not token:
            raise RuntimeError("Instagram access token is not configured for this user.")
        if not plan.image:
            raise RuntimeError("Plan image has not been generated.")
        if not settings.SITE_URL:
            raise RuntimeError("SITE_URL must be configured with a public URL for Instagram image publishing.")

        url = f"https://graph.facebook.com/v18.0/me/media"
        image_url = urljoin(f"{settings.SITE_URL}/", plan.image.url.lstrip("/"))

        response = requests.post(url, data={
            "image_url": image_url,
            "caption": plan.description,
            "access_token": token
        })
        response.raise_for_status()

        creation_id = response.json()['id']

        publish_url = f"https://graph.facebook.com/v18.0/me/media_publish"

        publish_response = requests.post(publish_url, data={
            "creation_id": creation_id,
            "access_token": token
        })
        publish_response.raise_for_status()

        plan.status = WeeklyPlan.STATUS_POSTED
        plan.save()

    except Exception as e:
        if plan is not None and self.request.retries + 1 >= self.max_retries:
            plan.status = WeeklyPlan.STATUS_FAILED
            plan.save(update_fields=['status'])
        self.retry(exc=e, countdown=120)
