# 
# overwritten implementaion of MethodView of Flask
# Added capability to docorate middleware to individual route
# Added database getconnection method
#

from flask.views import MethodView
from app.database import Database

class MethodView(MethodView):

    _decorators = {}

    def dispatch_request(self, *args, **kwargs):
        """Derived MethodView dispatch to allow for decorators to be
            applied to specific individual request methods - in addition
            to the standard decorator assignment.
            
            Example decorator use:
            decorators = [user_required] # applies to all methods
            _decorators = {
                'post': [admin_required, format_results]
            }    
        """

        view = super(MethodView, self).dispatch_request
        decorators = self._decorators.get(request.method.lower())
        if decorators:
            for decorator in decorators:
                view = decorator(view)

        return view(*args, **kwargs)

    def getConnection(self):
        instance = Database.getInstance()
        return instance.getConnection()