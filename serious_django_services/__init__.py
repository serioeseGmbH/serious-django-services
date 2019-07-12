from abc import ABC, ABCMeta
import collections

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured, PermissionDenied, \
    ValidationError
from django.forms.models import model_to_dict
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


class CRUDMixinMetaclass(ServiceMetaclass):
    @classmethod
    def __new__(mcls, name, *args, **kwargs):
        cls = super().__new__(name, *args, **kwargs)
        if cls.__base__ == ABC:
            return cls

        mcls.check_required_config_params(cls)
        return cls

    @staticmethod
    def check_required_config_params(cls):
        """
        Checks if the config parameters for the mixin have been set.

        :raise ImproperlyConfigured: If at least one of the required_params is None
        :return: None
        """
        required_params = ['model',
                           'create_form',
                           'update_form']

        for config_param in required_params:
            config_param_value = getattr(cls, config_param, None)
            if config_param_value is None:
                raise ImproperlyConfigured(f'{config_param} has to be set in'
                                           ' the class using the Mixin!')


class CRUDMixin(ABC, metaclass=CRUDMixinMetaclass):
    """
    A Mixin to provide CRUD operations.

    You must define the config parameters on the class using the Mixin:
    model: The model you want to perform the operations on
    create_form: A ModelForm to create a new model instance
    update_form: A ModelForm to update a model instance.

    Usage: Implement the operation in your service class and call the corresponding
        _operation from this Mixin.
    Eg.:
    ```
    class UserProfileService(Service, CRUDMixin):

    model = UserProfile
    create_form = CreateUserProfileForm
    update_form = UpdateUserProfileForm

    @classmethod
    def create(cls, name: str, profile_picture: ImageFile):
        data = {'name': name}
        file_data = {'profile_picture': profile_picture}

        return cls._create(data, file_data)
    ```
    """
    @classmethod
    def _create(cls, data: dict, file_data: dict = None):
        """
        Create an instance of cls.model and save it to the db.

        :param data: Data of the instance to be created
        :param file_data: File data of the instance to be created

        :raise ValidationError: If the form validations fails
        :return: The newly created instance of cls.model
        """
        bound_form = cls.create_form(data, file_data)

        if bound_form.is_valid():
            return bound_form.save()

        else:
            raise ValidationError(bound_form.errors)

    @classmethod
    def _retrieve(cls, id: int):
        """
        Retrieve one single instance of cls.model from the db.

        :param id: ID of the instance to be retrieved

        :raise ObjectDoesNotExist: If an instance corresponding with id does not exist
        :raise ValueError: If id is not int
        :return: The instance of cls.model
        """
        if not isinstance(id, int):
            raise ValueError("id must be int")
        return cls.model.objects.get(id=id)

    @classmethod
    def _update(cls, id: int, data: dict, file_data: dict = None):
        """
        Update an instance of cls.model and save it to the db.

        :param id: ID of the instance to be updated
        :param data: Data to update on the instance
        :param file_data: File data to update on the instance

        :raise ValidationError: If the form validations fails
        :raise ObjectDoesNotExist: If an instance corresponding with id does not exist
        :raise TypeError: If no id is passed
        :return: The updated instance of cls.model
        """
        model_instance_to_be_updated = cls.model.objects.get(id=id)

        updated_model_data = dict(model_to_dict(model_instance_to_be_updated),
                                  **data)
        updated_model_file_data = dict(model_to_dict(model_instance_to_be_updated),
                                       **file_data if file_data else {})

        bound_form = cls.update_form(updated_model_data,
                                     updated_model_file_data,
                                     instance=model_instance_to_be_updated)

        if bound_form.is_valid():
            return bound_form.save()

        else:
            raise ValidationError(bound_form.errors)

    @classmethod
    def _delete(cls, id: int):
        """
        Delete an instance of cls.model from the db.

        :param id: ID of the instance to be deleted

        :raise ObjectDoesNotExist: If an instance corresponding with id does not exist
        :return True: If the instance was successfully deleted
        """
        model_instance_to_be_deleted = cls.model.objects.get(id=id)
        model_instance_to_be_deleted.delete()

        return True


class NotPassed:
    """
    A default value for named args not being passed to the function.
    """
    pass
