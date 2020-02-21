
import logging
import re
import sys

import connexion.utils as utils
from connexion.exceptions import ResolverError

logger = logging.getLogger('connexion.resolver')

from connexion.resolver import Resolver

class CustomViewResolver(Resolver):
    """
    Resolves endpoint functions based on Flask's MethodView semantics, e.g. ::
            paths:
                /foo_bar:
                    get:
                        # Implied function call: api.FooBarView().get
            class FooBarView(MethodView):
                def get(self):
                    return ...
                def post(self):
                    return ...
    """

    def resolve_function_from_operation_id(self, operation_id):
        """
        Invokes the function_resolver
        :type operation_id: str
        """

        try:
            module_name, view_name, meth_name = operation_id.rsplit('.', 2)
            if operation_id and not view_name.endswith('View'):
                # If operation_id is not a view then assume it is a standard function
                return self.function_resolver(operation_id)

            mod = __import__(module_name, fromlist=[view_name])
            view_cls = getattr(mod, view_name)
            # Find the class and instantiate it
            view = view_cls()
            func = getattr(view, meth_name)
            # Return the method function of the class
            return func
        except ImportError as e:
            msg = 'Cannot resolve operationId "{}"! Import error was "{}"'.format(
                operation_id, str(e))
            raise ResolverError(msg, sys.exc_info())
        except (AttributeError, ValueError) as e:
            raise ResolverError(str(e), sys.exc_info())