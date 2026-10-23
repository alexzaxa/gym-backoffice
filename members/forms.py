from django import forms

from .models import Member


class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ("first_name", "last_name", "email", "phone", "photo", "checkin_code", "status", "notes")
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}
        help_texts = {
            "checkin_code": "Leave blank to generate one, or scan an existing keyfob or card.",
        }

    def __init__(self, *args, gym, **kwargs):
        super().__init__(*args, **kwargs)
        self.gym = gym
        self.fields["checkin_code"].required = False

    def clean_checkin_code(self):
        code = self.cleaned_data["checkin_code"].strip().upper()
        if code:
            clash = Member.objects.filter(gym=self.gym, checkin_code=code)
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise forms.ValidationError("Another member already uses this code.")
        return code

    def save(self, commit=True):
        self.instance.gym = self.gym
        return super().save(commit)
