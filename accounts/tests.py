from django.test import TestCase
from django.urls import reverse

from .models import Gym, User


class SignupTests(TestCase):
    def test_signup_creates_gym_and_owner(self):
        resp = self.client.post(reverse("signup"), {
            "gym_name": "Iron Works",
            "gym_address": "1 Main St",
            "first_name": "Sam",
            "last_name": "Lee",
            "username": "sam",
            "email": "sam@example.com",
            "password1": "a-strong-pass-123",
            "password2": "a-strong-pass-123",
        })
        self.assertRedirects(resp, reverse("members:list"))
        user = User.objects.get(username="sam")
        self.assertEqual(user.gym.name, "Iron Works")
        self.assertTrue(user.is_owner)


class StaffPermissionTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Iron Works")
        self.owner = User.objects.create_user("owner", password="pw", gym=self.gym, role=User.Role.OWNER)
        self.desk = User.objects.create_user("desk", password="pw", gym=self.gym, role=User.Role.FRONT_DESK)

    def test_front_desk_cannot_manage_staff(self):
        self.client.force_login(self.desk)
        self.assertEqual(self.client.get(reverse("staff_list")).status_code, 403)

    def test_owner_adds_staff_to_own_gym(self):
        self.client.force_login(self.owner)
        self.client.post(reverse("staff_create"), {
            "username": "newdesk",
            "role": User.Role.FRONT_DESK,
            "password1": "a-strong-pass-123",
            "password2": "a-strong-pass-123",
        })
        self.assertEqual(User.objects.get(username="newdesk").gym, self.gym)

    def test_staff_list_only_shows_own_gym(self):
        other = Gym.objects.create(name="Other")
        User.objects.create_user("stranger", password="pw", gym=other)
        self.client.force_login(self.owner)
        resp = self.client.get(reverse("staff_list"))
        self.assertNotContains(resp, "stranger")

    def test_login_required(self):
        resp = self.client.get(reverse("members:list"))
        self.assertRedirects(resp, f"{reverse('login')}?next={reverse('members:list')}")


class ThemeTests(TestCase):
    def setUp(self):
        self.gym = Gym.objects.create(name="Iron Works")
        self.owner = User.objects.create_user("owner", password="pw", gym=self.gym, role=User.Role.OWNER)
        self.desk = User.objects.create_user("desk", password="pw", gym=self.gym, role=User.Role.FRONT_DESK)

    def test_new_gyms_use_athletic_bold(self):
        self.client.force_login(self.desk)
        self.assertContains(self.client.get(reverse("members:list")), 'class="theme-bold"')

    def test_owner_changes_theme_for_whole_gym(self):
        self.client.force_login(self.owner)
        resp = self.client.post(reverse("settings"), {"name": "Iron Works", "address": "", "theme": "dark"})
        self.assertRedirects(resp, reverse("settings"))
        self.gym.refresh_from_db()
        self.assertEqual(self.gym.theme, Gym.Theme.DARK)
        self.client.force_login(self.desk)
        self.assertContains(self.client.get(reverse("members:list")), 'class="theme-dark"')

    def test_front_desk_cannot_open_settings(self):
        self.client.force_login(self.desk)
        self.assertEqual(self.client.get(reverse("settings")).status_code, 403)

    def test_logged_out_pages_use_default_theme(self):
        self.assertContains(self.client.get(reverse("login")), 'class="theme-bold"')
