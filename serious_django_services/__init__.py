from abc import ABC, ABCMeta
import collections
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.utils.translation import gettext as _


class ServiceMetaclass(ABCMeta):
    def __new__(mcls, name, *args, **kwargs):
        cls = super(ServiceMetaclass, mcls).__new__(mcls, name, *args, **kwargs)
        if cls.__base__ == ABC:
            return cls

        if not name.endswith('Service'):
            raise ImproperlyConfigured(
                "A Service subclass's name must end with 'Service'."
            )

        svc_excs = getattr(cls, 'service_exceptions')
        if svc_excs is None or\
           not isinstance(svc_excs, tuple) or\
           not all(type(c) is type and issubclass(c, Exception) for c in svc_excs):
            raise ImproperlyConfigured(
                "Defined a service without an `service_exceptions` property. "
                "Define a `service_exceptions` property which should be a tuple "
                "of subclasses of Exception, and enumerates all service-specific "
                "exceptions that a service can throw."
            )

        cls.exceptions = tuple(cls.service_exceptions or []) +\
            tuple(cls.base_exceptions or [])

        return cls


class Service(ABC, metaclass=ServiceMetaclass):
    base_exceptions = (PermissionDenied,)

    @classmethod
    def require_permissions(cls, user, permissions, obj=None):
        """
        Checks if:
        1. the given user is signed in (i.e. not None and not anonymous)
        2. the user has a certain set of permissions
        and raises a PermissionDenied exception otherwise.

        :param user: The user to check
        :param permissions: One permission or a list of permissions that the
            user is expected to have. Should all have the Permission type
            defined in this file.
        :param obj: If obj is passed in, this method won’t check for permissions for the model,
                    but for the specific object. (Only if you use an external library like django-guardian)

        """
        cls.require_signed_in(user)
        if not isinstance(permissions, collections.Iterable):
            permissions = [permissions]
        for permission in permissions:
            if not user.has_perm(permission, obj=obj):
                raise PermissionDenied(
                    _("You do not have permission '{perm}'.").format(
                        perm=str(permission)
                    )
                )

    @classmethod
    def require_signed_in(cls, user):
        """
        Checks if the given user is signed in, and raises a PermissionDenied
        exception otherwise.

        :param user: The user to check
        """
        if not isinstance(user, get_user_model()) or user.is_anonymous:
            raise PermissionDenied(_("You are not logged in."))
