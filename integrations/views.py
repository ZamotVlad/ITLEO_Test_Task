import os

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import redirect

from integrations.models import GoogleAccount
from integrations.services.calendar_sync import (
    get_google_flow,
    sync_group_to_calendar,
)

os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


@staff_member_required
def google_connect(request):
    flow = get_google_flow()
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        code_challenge=None,
        code_challenge_method=None,
    )
    return redirect(auth_url)


@staff_member_required
def google_callback(request):
    code = request.GET.get("code")
    if not code:
        return JsonResponse({"error": "No code provided"}, status=400)

    flow = get_google_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials

    google_account, _ = GoogleAccount.objects.get_or_create(user=request.user)
    google_account.access_token = credentials.token
    google_account.refresh_token = credentials.refresh_token
    google_account.is_connected = True
    google_account.save()

    return JsonResponse(
        {"status": "✅ Google Calendar підключено успішно!"},
        json_dumps_params={"ensure_ascii": False},
    )


@staff_member_required
def google_sync_group(request, group_id):
    from schedule.models import Group

    try:
        group = (
            Group.objects.prefetch_related(
                "schedule_entries",
                "students",
            )
            .select_related("teacher")
            .get(pk=group_id)
        )
    except Group.DoesNotExist:
        return JsonResponse({"error": "Групу не знайдено"}, status=404)

    sync_group_to_calendar(group)
    return JsonResponse(
        {"status": f"✅ Групу '{group.name}' синхронізовано"},
        json_dumps_params={"ensure_ascii": False},
    )


@staff_member_required
def google_sync_all(request):
    from schedule.models import Group

    groups = (
        Group.objects.prefetch_related("schedule_entries", "students")
        .select_related("teacher")
        .all()
    )

    synced = 0
    for group in groups:
        try:
            sync_group_to_calendar(group)
            synced += 1
        except Exception:
            pass

    return JsonResponse(
        {"status": f"✅ Синхронізовано {synced} груп"},
        json_dumps_params={"ensure_ascii": False},
    )
