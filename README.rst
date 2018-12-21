========================
Serious Django: Services
========================

https://github.com/serioeseGmbH/serious-django-services

serious-django-services defines a Service pattern for Django.

What a Service does is abstracting operations (first and foremost: operations on models)
and their business logic away from endpoints, so you can reuse business logic both for your
API, your Graphene endpoints, and your classic HTML Django Views.

Each Service also defines ``service_exceptions``, a list of exceptions that it specifically
can throw. If you don't have any of those for your serivce, make sure to just set ``service_exceptions = []``.
Otherwise you'll get an error on the definition of the class, to enforce being explicit about which
exceptions your Service can throw.

--------------------------------------------------------------------------------

In this package, we just define a ``Service`` base class that you need to inherit to write your own
services. Here's a toy example::

    class WeAreClosedException(Exception):
        pass

    class OrderTakeoutService(Service):
        service_exceptions = (WeAreClosedException,)

	@classmethod
	def create_order(cls, customer, item_no):
	    if datetime.datetime.now().hour > 22:
	        raise WeAreClosedException("Sorry, we're closed after 10pm.")
            if not customer.has_perm(PermissionToOrder):
                raise PermissionDenied("Sorry, you can't order right now.") # when someone was too rude
            order = Order.objects.create(customer=customer, item=item_no)
	    return order

Now you can keep this business logic local to this service, and use it anywhere you might need to
create an order. For instance, in a Graphene mutation::

    class OrderTakeoutMutation(graphene.Mutation):
        class Arguments:
            item_no = graphene.String()

        success = graphene.NonNull(graphene.Boolean)
	error = graphene.String()
        order_no = graphene.ID()

	def mutate(self, info, item_no):
	    # get_user_from_info() is from `serious-django-graphene`
	    customer = get_user_from_info(info)
	    try:
		order = OrderTakeoutService.create_order(customer, item_no)
            except OrderTakeoutService.exceptions as e:
	        return OrderTakeoutMutation(success=False, error=str(e))

	    return OrderTakeoutMutation(success=True, order_no=order.pk)

You can then do something very similar for a REST API or a Django View. And none of your view-level
logic needs to ever know about your closing hours or that some customers can be banned from ordering.


Quick start
-----------

1. Install the package with pip::

    pip install serious-django-services

2. Add "serious_django_services" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'serious_django_services',
    ]

3. Import ``serious_django_services.Service`` and subclass it for each Service you want to define.

4. Define the operations you need on your service, each as a ``@classmethod``.

5. Use your Service's operations in your view-level code.
