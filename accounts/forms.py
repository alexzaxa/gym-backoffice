from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Gym, User


class GymSignupForm(UserCreationForm):
    gym_name = forms.CharField(max_length=200, label="Gym name")
    gym_address = forms.CharField(max_length=300, required=False, label="Gym address")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("gym_name", "gym_address", "first_name", "last_name", "username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.gym = Gym.objects.create(
            name=self.cleaned_data["gym_name"],
            address=self.cleaned_data["gym_address"],
        )
        user.role = User.Role.OWNER
        if commit:
            user.save()
        return user


class StaffCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("first_name", "last_name", "username", "email", "role")


class GymSettingsForm(forms.ModelForm):
    class Meta:
        model = Gym
        fields = ("name", "address", "theme")
        labels = {"name": "Gym name", "theme": "Look"}
        widgets = {"theme": forms.RadioSelect}
