from django.test import TestCase
from django.urls import reverse

from accounts.models import Gym, User

from .models import CODE_LENGTH, Member


class MemberTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Iron Works")
        self.other_gym = Gym.objects.create(name="Other Gym")
        self.user = User.objects.create_user("desk", password="pw", gym=self.gym)
        self.client.force_login(self.user)
        self.mine = Member.objects.create(gym=self.gym, first_name="Ana", last_name="Diaz")
        self.theirs = Member.objects.create(gym=self.other_gym, first_name="Zed", last_name="Other")

    def test_checkin_code_generated(self):
        self.assertEqual(len(self.mine.checkin_code), CODE_LENGTH)

    def test_list_only_shows_own_gym(self):
        resp = self.client.get(reverse("members:list"))
        self.assertContains(resp, "Ana Diaz")
        self.assertNotContains(resp, "Zed Other")

    def test_cannot_open_other_gyms_member(self):
        self.assertEqual(self.client.get(reverse("members:detail", args=[self.theirs.pk])).status_code, 404)
        self.assertEqual(self.client.get(reverse("members:edit", args=[self.theirs.pk])).status_code, 404)

    def test_search(self):
        Member.objects.create(gym=self.gym, first_name="Bob", last_name="Smith")
        resp = self.client.get(reverse("members:list"), {"q": "smi"})
        self.assertContains(resp, "Bob Smith")
        self.assertNotContains(resp, "Ana Diaz")

    def test_search_by_code_htmx_returns_table_only(self):
        resp = self.client.get(reverse("members:list"), {"q": self.mine.checkin_code.lower()}, HTTP_HX_REQUEST="true")
        self.assertContains(resp, "Ana Diaz")
        self.assertNotContains(resp, "<nav")

    def test_create_member_in_own_gym(self):
        resp = self.client.post(reverse("members:create"), {
            "first_name": "Cy", "last_name": "Park", "status": "active", "checkin_code": "",
        })
        member = Member.objects.get(first_name="Cy")
        self.assertRedirects(resp, reverse("members:detail", args=[member.pk]))
        self.assertEqual(member.gym, self.gym)
        self.assertTrue(member.checkin_code)

    def test_duplicate_code_rejected_within_gym(self):
        resp = self.client.post(reverse("members:create"), {
            "first_name": "Cy", "last_name": "Park", "status": "active",
            "checkin_code": self.mine.checkin_code.lower(),
        })
        self.assertContains(resp, "Another member already uses this code.")

    def test_same_code_allowed_in_different_gyms(self):
        resp = self.client.post(reverse("members:create"), {
            "first_name": "Cy", "last_name": "Park", "status": "active",
            "checkin_code": self.theirs.checkin_code,
        })
        self.assertEqual(resp.status_code, 302)
