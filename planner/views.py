import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from accounts.models import UserProfile
from analytics.models import PostAnalytics
from .models import WeeklyPlan
from .forms import UploadFileForm
from scheduler.tasks import process_plan


REQUIRED_COLUMNS = ['Title', 'Description', 'Content', 'Scheduled Time']


def _coerce_datetime(value):
    if pd.isna(value):
        raise ValidationError('Scheduled Time is required.')

    if hasattr(value, 'to_pydatetime'):
        value = value.to_pydatetime()
    elif isinstance(value, str):
        value = parse_datetime(value)
        if value is None:
            raise ValidationError('Scheduled Time must be a valid date and time.')

    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone.get_current_timezone())

    return value


def _coerce_text(value, field_name):
    if pd.isna(value) or not str(value).strip():
        raise ValidationError(f'{field_name} is required.')
    return str(value).strip()


def _queue_plan_processing(request, plan):
    if not settings.CELERY_BROKER_URL:
        messages.warning(
            request,
            'Plan saved, but background processing is not configured.',
        )
        return

    def enqueue():
        try:
            process_plan.delay(plan.id)
        except Exception:
            plan.status = WeeklyPlan.STATUS_FAILED
            plan.save(update_fields=['status'])
            messages.warning(
                request,
                'Plan saved, but background processing could not start. Please start Redis/Celery and retry processing.',
            )

    transaction.on_commit(enqueue)


@login_required
def dashboard(request):
    posts = WeeklyPlan.objects.filter(user=request.user).order_by('-scheduled_time')
    today = timezone.localdate()
    report_dates = [today - timezone.timedelta(days=offset) for offset in range(4, -1, -1)]
    report_start = report_dates[0]
    recent_posts = list(
        posts.filter(
            Q(posted_at__date__gte=report_start)
            | Q(posted_at__isnull=True, scheduled_time__date__gte=report_start)
        )
    )
    analytics_by_plan = {
        item.plan_id: item
        for item in PostAnalytics.objects.filter(plan__in=recent_posts)
    }

    daily_report = []
    for report_date in report_dates:
        day_posts = [
            post for post in recent_posts
            if timezone.localtime(post.posted_at or post.scheduled_time).date() == report_date
        ]
        day_analytics = [analytics_by_plan.get(post.id) for post in day_posts]
        daily_report.append({
            'date': report_date,
            'post_count': len(day_posts),
            'views': sum(item.impressions for item in day_analytics if item),
            'likes': sum(item.likes for item in day_analytics if item),
        })

    recent_post_report = []
    for post in recent_posts:
        analytics = analytics_by_plan.get(post.id)
        recent_post_report.append({
            'title': post.title,
            'status': post.get_status_display(),
            'scheduled_time': post.scheduled_time,
            'has_ai_image': bool(post.image),
            'views': analytics.impressions if analytics else 0,
            'likes': analytics.likes if analytics else 0,
            'reach': analytics.reach if analytics else 0,
            'metadata': {
                'caption': post.description,
                'content': post.content,
                'image': post.image.name if post.image else '',
            },
        })

    report_totals = {
        'views': sum(item['views'] for item in daily_report),
        'likes': sum(item['likes'] for item in daily_report),
        'posts': sum(item['post_count'] for item in daily_report),
    }

    context = {
        'posts': posts,
        'scheduled_count': posts.filter(
            status__in=[WeeklyPlan.STATUS_PENDING, WeeklyPlan.STATUS_PROCESSING, WeeklyPlan.STATUS_SCHEDULED]
        ).count(),
        'posted_count': posts.filter(status=WeeklyPlan.STATUS_POSTED).count(),
        'daily_report': daily_report,
        'recent_post_report': recent_post_report,
        'report_totals': report_totals,
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        token = request.POST.get('token', '').strip()
        if token:
            profile_obj.set_token(token)
            profile_obj.save(update_fields=['instagram_token'])
            messages.success(request, 'Instagram token saved.')
        else:
            messages.error(request, 'Please enter a token before saving.')
        return redirect('profile')

    return render(request, 'profile.html', {'has_token': bool(profile_obj.instagram_token)})


@login_required
def upload_plan(request):
    form = UploadFileForm()

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                df = pd.read_excel(form.cleaned_data['file'])
            except Exception:
                form.add_error('file', 'Could not read this Excel file.')
            else:
                missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
                if missing_columns:
                    form.add_error('file', f"Missing required columns: {', '.join(missing_columns)}.")
                else:
                    created_count = 0
                    for index, row in df.iterrows():
                        try:
                            title = _coerce_text(row['Title'], 'Title')
                            description = _coerce_text(row['Description'], 'Description')
                            content = _coerce_text(row['Content'], 'Content')
                            scheduled_time = _coerce_datetime(row['Scheduled Time'])
                        except ValidationError as exc:
                            form.add_error('file', f"Row {index + 2}: {exc.message}")
                            continue

                        plan = WeeklyPlan.objects.create(
                            user=request.user,
                            title=title,
                            description=description,
                            content=content,
                            scheduled_time=scheduled_time,
                            status=WeeklyPlan.STATUS_PENDING,
                        )
                        _queue_plan_processing(request, plan)
                        created_count += 1

                    if created_count:
                        messages.success(request, f'{created_count} plan item(s) uploaded.')
                        return redirect('dashboard')

    return render(request, 'upload.html', {'form': form})
