from flask import request
from app.MethodView import SuperView
import json
from app.ConnectionBusinessException import BussinessException
import time
from jose import JWTError, jwt
import six
from werkzeug.exceptions import Unauthorized
from app.AuthzModule import Authz
import json

# Production: update jwt_secret after each update to jwt logic
# to secure by not logging out / expire tokens before the logic 
# change. This guarantee no log in with old token
JWT_ISSUER = 'sharity'
JWT_SECRET = 'hvdfs43^fx'
JWT_LIFETIME_SECONDS = 60 * 60 * 24 * 2
JWT_ALGORITHM = 'HS256'

class AuthView(SuperView): 
    """ Create Auth service
    """
    method_decorators = []
    _decorators = []

    def login(self):
        body = request.json
        if body['password'] != body['confirmpassword']:
            raise BussinessException("error",400,"confirm password mismatch") 
        db = self.getConnection()
        payload = {}
        if body['isNgo']:
            result = db.ngo.find_one({'email':body['email'],'password':body['password']},{'_id':True, 'name': True})
            if not result:
                raise BussinessException("error",400,"Check your username and passsword!")
            payload['id'] = str(result['_id'])
            payload['role'] = 'ngo'
            payload['name'] = result['name']

        else:
            result = db.user.find_one({'email':body['email'],'password':body['password']},{'_id':True,'isAdmin':True, 'firstName': True, 'lastName': True})
            if not result:
                raise BussinessException("error",400,"Check your username and passsword!")
            payload['id'] = str(result['_id'])
            payload['firstName'] = result['firstName']
            payload['lastName'] = result['lastName']
            if result.get('isAdmin',None):
                payload['role'] = 'admin'
            else:
                payload['role'] = 'user'
        timestamp = self._current_timestamp()
        payload = {
            "iss": JWT_ISSUER,
            "iat": int(timestamp),
            "exp": int(timestamp + JWT_LIFETIME_SECONDS),
            "sub": json.dumps(payload),
        }
        # token must contain role and id of the user under sub key
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # connexion library needs decode_token without self
    @staticmethod
    def decode_token(token):
        try:
            decoded_token =  jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            authz = Authz.getInstance()
            allow = authz.checkAuthz(request,decoded_token)
            if not allow:
                raise BussinessException("Forbidden",403,"No permission")
            return decoded_token
        except JWTError as e:
            six.raise_from(Unauthorized, e)

    def _current_timestamp(self) -> int:
        return int(time.time())