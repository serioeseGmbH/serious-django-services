from django.test import TestCase
from django.core.exceptions import ImproperlyConfigured

from serious_django_services import Service, CRUDMixin

from tests.models import Foo
from tests.forms import CreateFooForm, UpdateFooForm


class CRUDMixinTest(TestCase):
    def test_properly_configured(self):
        class FooService(Service, CRUDMixin):
            service_exceptions = ()

            model = Foo
            create_form = CreateFooForm
            update_form = UpdateFooForm

            @classmethod
            def create(cls):
                data = {}
                return cls._create(data)

        new_foo = FooService.create()

        self.assertTrue(new_foo)
        self.assertTrue(Foo.objects.get(id=new_foo.id))

    def test_missing_create_form(self):
        expected_error_message = "create_form has to be set in the class using the Mixin!"

        with self.assertRaises(ImproperlyConfigured) as e:
            class FooService(Service, CRUDMixin):
                service_exceptions = ()

                model = Foo
                update_form = UpdateFooForm
            pass
        self.assertIn(expected_error_message, str(e.exception))

    def test_missing_model(self):
        expected_error_message = "model has to be set in the class using the Mixin!"

        with self.assertRaises(ImproperlyConfigured) as e:
            class FooService(Service, CRUDMixin):
                service_exceptions = ()

                create_form = CreateFooForm
                update_form = UpdateFooForm
        self.assertIn(expected_error_message, str(e.exception))
