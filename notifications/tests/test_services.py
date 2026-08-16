import datetime
from unittest.mock import patch

import pytest
from django.core import mail

from accounts.roles import Roles
from notifications.models import NotificationLog
from notifications.services import (
    broadcast_to_group,
    get_bot_debtors_text,
    notify_schedule_change,
    remind_debtors_telegram,
    send_class_reminders,
    send_payment_reminders,
    send_telegram_message,
)
from payments.models import Payment
from schedule.models import Group, Schedule
from students.models import Parent, Student


@pytest.fixture
def student_with_chat(django_user_model):
    user = django_user_model.objects.create_user(
        username="student_chat", role=Roles.STUDENT, telegram_chat_id=111
    )
    return Student.objects.create(full_name="Студент", user=user, email="student@test.com")


@pytest.fixture
def parent_with_chat(django_user_model, student_with_chat):
    user = django_user_model.objects.create_user(
        username="parent_chat", role=Roles.PARENT, telegram_chat_id=222
    )
    parent = Parent.objects.create(full_name="Батько", user=user, email="parent@test.com")
    parent.students.add(student_with_chat)
    return parent


# ---------------------------------------------------------------------------
# send_telegram_message - the only function that actually touches the network
# ---------------------------------------------------------------------------


class TestSendTelegramMessage:
    @patch("notifications.services.requests.post")
    def test_returns_true_on_success(self, mock_post):
        mock_post.return_value.status_code = 200
        assert send_telegram_message(123, "text") is True

    @patch("notifications.services.requests.post")
    def test_returns_false_on_non_200(self, mock_post):
        mock_post.return_value.status_code = 400
        assert send_telegram_message(123, "text") is False

    @patch("notifications.services.requests.post")
    def test_returns_false_on_network_error(self, mock_post):
        import requests

        mock_post.side_effect = requests.RequestException("timeout")
        assert send_telegram_message(123, "text") is False


# ---------------------------------------------------------------------------
# get_bot_debtors_text
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetBotDebtorsText:
    def test_no_debtors_returns_celebratory_message(self):
        assert get_bot_debtors_text() == "Боржників немає 🎉"

    def test_lists_debtors_with_amounts(self, student_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=500, date="2026-08-15", status="debt"
        )

        text = get_bot_debtors_text()

        assert "Студент" in text
        assert "500" in text

    def test_ignores_non_debt_payments(self, student_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=500, date="2026-08-15", status="paid"
        )

        assert get_bot_debtors_text() == "Боржників немає 🎉"


# ---------------------------------------------------------------------------
# remind_debtors_telegram
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRemindDebtorsTelegram:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_notifies_student_and_parent(self, mock_send, student_with_chat, parent_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=300, date="2026-08-15", status="debt"
        )

        sent, skipped = remind_debtors_telegram()

        assert sent == 2  # student + parent
        assert skipped == 0
        assert mock_send.call_count == 2
        assert NotificationLog.objects.filter(notification_type="payment_reminder").count() == 2

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_student_without_chat_id_counted_as_skipped(self, mock_send, django_user_model):
        user = django_user_model.objects.create_user(username="no_chat", role=Roles.STUDENT)
        student = Student.objects.create(full_name="Без чату", user=user)
        Payment.objects.create(student=student, amount=100, date="2026-08-15", status="pending")

        sent, skipped = remind_debtors_telegram()

        assert skipped == 1
        assert sent == 0
        mock_send.assert_not_called()

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_student_without_user_counted_as_skipped(self, mock_send):
        student = Student.objects.create(full_name="Без юзера")
        Payment.objects.create(student=student, amount=100, date="2026-08-15", status="debt")

        sent, skipped = remind_debtors_telegram()

        assert skipped == 1

    @patch("notifications.services.send_telegram_message", return_value=False)
    def test_failed_send_not_counted_as_sent(self, mock_send, student_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="debt"
        )

        sent, skipped = remind_debtors_telegram()

        assert sent == 0
        log = NotificationLog.objects.get(notification_type="payment_reminder")
        assert log.status == "failed"

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_only_paid_status_is_excluded(self, mock_send, student_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="paid"
        )

        sent, skipped = remind_debtors_telegram()

        assert sent == 0
        assert skipped == 0
        mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# send_payment_reminders - email version
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendPaymentReminders:
    def test_sends_email_to_student_and_parent(self, student_with_chat, parent_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=400, date="2026-08-15", status="debt"
        )

        send_payment_reminders()

        assert len(mail.outbox) == 2
        recipients = [m.to[0] for m in mail.outbox]
        assert "student@test.com" in recipients
        assert "parent@test.com" in recipients

    def test_skips_student_without_email(self, django_user_model):
        user = django_user_model.objects.create_user(username="no_email_user", role=Roles.STUDENT)
        student = Student.objects.create(full_name="Без email", user=user)
        Payment.objects.create(student=student, amount=100, date="2026-08-15", status="debt")

        send_payment_reminders()

        assert len(mail.outbox) == 0

    def test_skips_parent_without_email(self, student_with_chat, django_user_model):
        user = django_user_model.objects.create_user(username="parent_no_email", role=Roles.PARENT)
        parent = Parent.objects.create(full_name="Батько без email", user=user)
        parent.students.add(student_with_chat)
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="debt"
        )

        send_payment_reminders()

        assert len(mail.outbox) == 1  # only the student

    @patch("notifications.services.send_mail", side_effect=Exception("SMTP down"))
    def test_send_failure_is_logged_not_raised(self, mock_send_mail, student_with_chat):
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="debt"
        )

        send_payment_reminders()  # must not raise

        log = NotificationLog.objects.get(recipient="student@test.com")
        assert log.status == "failed"


# ---------------------------------------------------------------------------
# broadcast_to_group
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestBroadcastToGroup:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_sends_to_all_students_with_chat_id(self, mock_send, django_user_model):
        group = Group.objects.create(name="Група")
        for i in range(3):
            user = django_user_model.objects.create_user(
                username=f"member_{i}", role=Roles.STUDENT, telegram_chat_id=1000 + i
            )
            Student.objects.create(full_name=f"Студент {i}", user=user, group=group)

        sent, skipped = broadcast_to_group(group.id, "Привіт усім")

        assert sent == 3
        assert mock_send.call_count == 3

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_excludes_students_from_other_groups(self, mock_send, django_user_model):
        group_a = Group.objects.create(name="A")
        group_b = Group.objects.create(name="B")
        user_a = django_user_model.objects.create_user(
            username="in_a", role=Roles.STUDENT, telegram_chat_id=1
        )
        user_b = django_user_model.objects.create_user(
            username="in_b", role=Roles.STUDENT, telegram_chat_id=2
        )
        Student.objects.create(full_name="A", user=user_a, group=group_a)
        Student.objects.create(full_name="B", user=user_b, group=group_b)

        broadcast_to_group(group_a.id, "Тільки для A")

        assert mock_send.call_count == 1

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_students_without_chat_id_are_excluded_from_query(self, mock_send, django_user_model):
        group = Group.objects.create(name="Група")
        user = django_user_model.objects.create_user(username="no_chat", role=Roles.STUDENT)
        Student.objects.create(full_name="Без чату", user=user, group=group)

        sent, skipped = broadcast_to_group(group.id, "Привіт")

        assert sent == 0
        mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# send_class_reminders - time-window based, uses real current time
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSendClassReminders:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_notifies_students_and_teacher_for_upcoming_class(self, mock_send, django_user_model):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        target = now + datetime.timedelta(hours=2)

        teacher = django_user_model.objects.create_user(
            username="teacher_reminder", role=Roles.TEACHER, telegram_chat_id=999
        )
        group = Group.objects.create(name="Група", teacher=teacher)
        student_user = django_user_model.objects.create_user(
            username="student_reminder", role=Roles.STUDENT, telegram_chat_id=888
        )
        Student.objects.create(full_name="Студент", user=student_user, group=group)
        Schedule.objects.create(
            group=group,
            weekday=now.weekday(),
            start_time=target.time().replace(second=0, microsecond=0),
            end_time=(target + datetime.timedelta(hours=1)).time(),
        )

        send_class_reminders()

        assert mock_send.call_count == 2  # student + teacher
        assert NotificationLog.objects.filter(notification_type="class_reminder").count() == 2

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_class_outside_window_is_not_notified(self, mock_send):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        far_away = (now + datetime.timedelta(hours=8)).time()

        group = Group.objects.create(name="Пізніше")
        Schedule.objects.create(
            group=group, weekday=now.weekday(), start_time=far_away, end_time=far_away
        )

        send_class_reminders()

        mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# notify_schedule_change
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestNotifyScheduleChange:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_notifies_student_parent_and_teacher(
        self, mock_send, django_user_model, student_with_chat, parent_with_chat
    ):
        teacher = django_user_model.objects.create_user(
            username="teacher_notify", role=Roles.TEACHER, telegram_chat_id=777
        )
        group = Group.objects.create(name="Група", teacher=teacher)
        student_with_chat.group = group
        student_with_chat.save()
        schedule = Schedule.objects.create(
            group=group, weekday=0, start_time="10:00", end_time="11:00"
        )

        notify_schedule_change(schedule.id)

        assert mock_send.call_count == 3  # student + parent + teacher

    def test_missing_schedule_does_not_raise(self):
        notify_schedule_change(999999)  # must simply return, no exception

        assert NotificationLog.objects.count() == 0


@pytest.mark.django_db
class TestRemindDebtorsTelegramEdgeCases:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_parent_without_user_is_skipped(self, mock_send, student_with_chat):
        Parent.objects.create(full_name="Батько без юзера").students.add(student_with_chat)
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="debt"
        )

        remind_debtors_telegram()

        mock_send.assert_called_once()  # тільки студент, не батько без user

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_parent_without_chat_id_is_skipped(
        self, mock_send, student_with_chat, django_user_model
    ):
        parent_user = django_user_model.objects.create_user(
            username="parent_no_chat", role=Roles.PARENT
        )
        parent = Parent.objects.create(full_name="Батько без чату", user=parent_user)
        parent.students.add(student_with_chat)
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="debt"
        )

        remind_debtors_telegram()

        mock_send.assert_called_once()  # той самий сценарій - без другого виклику на батька


@pytest.mark.django_db
class TestSendPaymentRemindersParentFailure:
    @patch("notifications.services.send_mail")
    def test_parent_email_failure_logged_independently_of_student(
        self, mock_send_mail, student_with_chat, parent_with_chat
    ):
        # перший виклик (студент) успішний, другий (батько) падає
        mock_send_mail.side_effect = [None, Exception("SMTP down")]
        Payment.objects.create(
            student=student_with_chat, amount=100, date="2026-08-15", status="debt"
        )

        send_payment_reminders()

        student_log = NotificationLog.objects.get(recipient="student@test.com")
        parent_log = NotificationLog.objects.get(recipient="parent@test.com")
        assert student_log.status == "sent"
        assert parent_log.status == "failed"


@pytest.mark.django_db
class TestBroadcastToGroupPartialFailure:
    @patch("notifications.services.send_telegram_message", side_effect=[True, False])
    def test_failed_send_counted_as_skipped_not_sent(self, mock_send, django_user_model):
        group = Group.objects.create(name="Група")
        for i in range(2):
            user = django_user_model.objects.create_user(
                username=f"broadcast_{i}", role=Roles.STUDENT, telegram_chat_id=500 + i
            )
            Student.objects.create(full_name=f"Студент {i}", user=user, group=group)

        sent, skipped = broadcast_to_group(group.id, "Текст")

        assert sent == 1
        assert skipped == 1


@pytest.mark.django_db
class TestSendClassRemindersEdgeCases:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_student_without_user_is_skipped(self, mock_send):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        target = now + datetime.timedelta(hours=2)
        group = Group.objects.create(name="Група")
        Student.objects.create(full_name="Без юзера", group=group)
        Schedule.objects.create(
            group=group,
            weekday=now.weekday(),
            start_time=target.time().replace(second=0, microsecond=0),
            end_time=(target + datetime.timedelta(hours=1)).time(),
        )

        send_class_reminders()

        mock_send.assert_not_called()

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_student_without_chat_id_is_skipped(self, mock_send, django_user_model):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        target = now + datetime.timedelta(hours=2)
        user = django_user_model.objects.create_user(username="no_chat_class", role=Roles.STUDENT)
        group = Group.objects.create(name="Група")
        Student.objects.create(full_name="Без чату", user=user, group=group)
        Schedule.objects.create(
            group=group,
            weekday=now.weekday(),
            start_time=target.time().replace(second=0, microsecond=0),
            end_time=(target + datetime.timedelta(hours=1)).time(),
        )

        send_class_reminders()

        mock_send.assert_not_called()


@pytest.mark.django_db
class TestNotifyScheduleChangeEdgeCases:
    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_student_without_user_is_skipped(self, mock_send):
        group = Group.objects.create(name="Група")
        Student.objects.create(full_name="Без юзера", group=group)
        schedule = Schedule.objects.create(
            group=group, weekday=0, start_time="10:00", end_time="11:00"
        )

        notify_schedule_change(schedule.id)

        mock_send.assert_not_called()

    @patch("notifications.services.send_telegram_message", return_value=True)
    def test_parent_without_user_is_skipped(self, mock_send, student_with_chat):
        group = Group.objects.create(name="Група")
        student_with_chat.group = group
        student_with_chat.save()
        Parent.objects.create(full_name="Батько без юзера").students.add(student_with_chat)
        schedule = Schedule.objects.create(
            group=group, weekday=0, start_time="10:00", end_time="11:00"
        )

        notify_schedule_change(schedule.id)

        mock_send.assert_called_once()  # тільки студент
