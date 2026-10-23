from datetime import datetime, timedelta, timezone as dt_timezone

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import Gym, User
from members.models import Member

from .models import MAX_VISIT_LENGTH, Visit
from .services import record_scan, toggle_visit
from .stats import member_stats
from .templatetags.visits import hours_minutes


class ScanTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Iron Works")
        self.other_gym = Gym.objects.create(name="Other")
        self.member = Member.objects.create(gym=self.gym, first_name="Ana", last_name="Diaz")
        self.t0 = timezone.now()

    def test_first_scan_checks_in(self):
        outcome = record_scan(self.gym, self.member.checkin_code.lower(), now=self.t0)
        self.assertEqual(outcome.kind, "in")
        self.assertTrue(outcome.visit.is_open)

    def test_second_scan_checks_out_with_duration(self):
        record_scan(self.gym, self.member.checkin_code, now=self.t0)
        outcome = record_scan(self.gym, self.member.checkin_code, now=self.t0 + timedelta(minutes=75))
        self.assertEqual(outcome.kind, "out")
        self.assertEqual(outcome.visit.duration, timedelta(minutes=75))
        self.assertEqual(Visit.objects.count(), 1)

    def test_quick_double_scan_does_not_check_out(self):
        record_scan(self.gym, self.member.checkin_code, now=self.t0)
        outcome = record_scan(self.gym, self.member.checkin_code, now=self.t0 + timedelta(seconds=20))
        self.assertEqual(outcome.kind, "repeat")
        self.assertTrue(outcome.visit.is_open)

    def test_forgotten_scan_out_closes_after_three_hours(self):
        record_scan(self.gym, self.member.checkin_code, now=self.t0)
        outcome = record_scan(self.gym, self.member.checkin_code, now=self.t0 + timedelta(hours=5))
        self.assertEqual(outcome.kind, "in")
        old = Visit.objects.order_by("checked_in_at").first()
        self.assertTrue(old.checkout_estimated)
        self.assertEqual(old.duration, MAX_VISIT_LENGTH)

    def test_frozen_and_cancelled_members_are_refused(self):
        for status in (Member.Status.FROZEN, Member.Status.CANCELLED):
            self.member.status = status
            self.member.save()
            outcome = record_scan(self.gym, self.member.checkin_code, now=self.t0)
            self.assertEqual(outcome.kind, "denied")
        self.assertEqual(Visit.objects.filter(result=Visit.Result.DENIED).count(), 2)
        self.assertFalse(Visit.objects.open().exists())

    def test_frozen_member_already_inside_can_still_check_out(self):
        record_scan(self.gym, self.member.checkin_code, now=self.t0)
        self.member.status = Member.Status.FROZEN
        self.member.save()
        outcome = record_scan(self.gym, self.member.checkin_code, now=self.t0 + timedelta(hours=1))
        self.assertEqual(outcome.kind, "out")

    def test_unknown_and_other_gyms_codes_rejected(self):
        self.assertEqual(record_scan(self.gym, "NOPE1234").kind, "unknown")
        self.assertEqual(record_scan(self.gym, "").kind, "unknown")
        self.assertEqual(record_scan(self.other_gym, self.member.checkin_code).kind, "unknown")


class StatsTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Iron Works")
        self.member = Member.objects.create(gym=self.gym, first_name="Ana", last_name="Diaz")

    def visit(self, start, minutes):
        Visit.objects.create(gym=self.gym, member=self.member, checked_in_at=start,
                             checked_out_at=start + timedelta(minutes=minutes))

    def test_stats(self):
        now = datetime(2026, 10, 22, 18, 0, tzinfo=dt_timezone.utc)  # a Thursday
        self.visit(now - timedelta(days=1), 60)       # this week
        self.visit(now - timedelta(days=2), 90)       # this week
        self.visit(now - timedelta(days=8), 30)       # last week
        self.visit(now - timedelta(days=15), 60)      # two weeks ago
        self.visit(now - timedelta(days=40), 60)      # September, breaks the streak
        Visit.objects.create(gym=self.gym, member=self.member, checked_in_at=now,
                             result=Visit.Result.DENIED)
        stats = member_stats(self.member, now=now)
        self.assertEqual(stats["total_visits"], 5)
        self.assertEqual(stats["visits_this_month"], 4)
        self.assertEqual(stats["time_this_week"], timedelta(minutes=150))
        self.assertEqual(stats["average_visit"], timedelta(minutes=60))
        self.assertEqual(stats["week_streak"], 3)

    def test_hours_minutes(self):
        self.assertEqual(hours_minutes(timedelta(minutes=45)), "45m")
        self.assertEqual(hours_minutes(timedelta(minutes=65)), "1h 05m")
        self.assertEqual(hours_minutes(None), "—")


class ViewTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Iron Works")
        self.user = User.objects.create_user("desk", password="pw", gym=self.gym)
        self.member = Member.objects.create(gym=self.gym, first_name="Ana", last_name="Diaz")
        other = Gym.objects.create(name="Other")
        self.stranger = Member.objects.create(gym=other, first_name="Zed", last_name="Other")
        self.client.force_login(self.user)

    def test_kiosk_scan_shows_welcome(self):
        resp = self.client.post(reverse("checkins:scan"), {"code": self.member.checkin_code})
        self.assertContains(resp, "Welcome, Ana")

    def test_kiosk_requires_login(self):
        self.client.logout()
        resp = self.client.post(reverse("checkins:scan"), {"code": self.member.checkin_code})
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Visit.objects.exists())

    def test_today_lists_who_is_inside(self):
        toggle_visit(self.member)
        resp = self.client.get(reverse("checkins:today"))
        self.assertContains(resp, "Ana Diaz")
        self.assertEqual(len(resp.context["inside"]), 1)

    def test_front_desk_toggle(self):
        url = reverse("checkins:toggle", args=[self.member.pk])
        self.client.post(url)
        self.assertTrue(Visit.objects.open().exists())

    def test_cannot_toggle_other_gyms_member(self):
        resp = self.client.post(reverse("checkins:toggle", args=[self.stranger.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_member_page_shows_stats(self):
        resp = self.client.get(reverse("members:detail", args=[self.member.pk]))
        self.assertContains(resp, "Week streak")
        self.assertContains(resp, "Check in")
