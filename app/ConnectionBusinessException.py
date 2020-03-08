from connexion import ProblemException

class BussinessException(ProblemException):
    def __init__(self, title=None, status=None, detail=None, **kwargs):
        super(BussinessException, self).__init__(title=title,status=status,detail=detail,**kwargs)
