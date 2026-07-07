from django import forms
from django.contrib.auth import get_user_model


class UserAdminForm(forms.ModelForm):
    password1 = forms.CharField(
        label="รหัสผ่าน",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="ยืนยันรหัสผ่าน",
        required=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser"]
        labels = {
            "username": "Username",
            "first_name": "ชื่อ",
            "last_name": "นามสกุล",
            "email": "Email",
            "is_active": "เปิดใช้งาน",
            "is_staff": "สิทธิ์จัดการระบบ",
            "is_superuser": "ผู้ดูแลระบบสูงสุด",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "autocomplete": "username"}),
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "autocomplete": "email"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_staff": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_superuser": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_create = self.instance.pk is None
        if self.is_create:
            self.fields["password1"].required = True
            self.fields["password2"].required = True
        else:
            self.fields["password1"].help_text = "เว้นว่างไว้หากไม่ต้องการเปลี่ยนรหัสผ่าน"

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "รหัสผ่านไม่ตรงกัน")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        if commit:
            user.save()
            self.save_m2m()
        return user