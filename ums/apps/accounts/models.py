from django.contrib.auth.base_user import AbstractBaseUser
from django.core.mail import send_mail
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import PermissionsMixin, UserManager, Group
from django.contrib.auth.validators import UnicodeUsernameValidator

from .utils import RoleChoices, GroupTypeChoices


class OCTUser(AbstractBaseUser, PermissionsMixin):
    """
        An abstract base class implementing a fully featured User model with
        admin-compliant permissions.
        Username and password are required. Other fields are optional.
        """

    username_validator = UnicodeUsernameValidator()
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$',
                                 message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")

    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    name = models.CharField(_("name"), max_length=150, blank=True)
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)  # Validators should be a list
    department = models.CharField(_("department"), max_length=150, blank=True)
    role = models.IntegerField(choices=RoleChoices.choices, verbose_name=_('role'),null=True)
    email = models.EmailField(_("email address"), blank=True)
    mime = models.URLField(_('头像'), max_length=255, blank=True)
    is_staff = models.BooleanField(
        _("staff status"),
        default=False,
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField(_("date joined"), default=timezone.now)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        # abstract = True

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = "%s" % self.name
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def __str__(self):
        return self.name + " | " + self.username


class GroupType(models.Model):
    group = models.ManyToManyField(Group, related_name='group_type',
                                   related_query_name='types', verbose_name=_('团组'))
    type = models.CharField(_('类型'), max_length=50, choices=GroupTypeChoices.choices)

    def __str__(self):
        return self.get_type_display()


class GroupProfile(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE,unique=True)
    supervisor = models.OneToOneField(OCTUser, on_delete=models.CASCADE, related_name='supervisor_op',limit_choices_to={'role':RoleChoices.PROJECT_SPONSOR.value})
    leader = models.ManyToManyField(OCTUser, related_name='leader_of',limit_choices_to={'role':RoleChoices.APPROVAL_LEADER.value})

    def __str__(self):
        return self.group.name
