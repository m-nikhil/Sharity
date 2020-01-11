# 
# Overwritten implementaion of ResponseValidator of swagger connexion
# Added trim function to trim unnecessay keys from response object before passing to validator
#

import functools
from connexion import decorators
from jsonschema import ValidationError
from connexion.exceptions import (NonConformingResponseBody,
                          NonConformingResponseHeaders)
from connexion.utils import all_json, has_coroutine

ResponseBodyValidator = decorators.validation.ResponseBodyValidator

#Link: https://github.com/zalando/connexion/blob/f55cb1c923a2b51f402513fc6bdd3c9ebe31353a/connexion/decorators/response.py#L16
class ResponseValidator(decorators.response.ResponseValidator):

    def response_trim(self, response_schema, data):
        trim_data = {}
        properties = response_schema['properties']
        for key in properties.keys():
            if key in data:
                if properties[key].get('writeOnly'):
                    continue
                trim_data[key] = data[key]
        return trim_data

    def validate_response(self, data, status_code, headers, url):
        """
        Validates the Response object based on what has been declared in the specification.
        Ensures the response body matches the declated schema.
        :type data: dict
        :type status_code: int
        :type headers: dict
        :rtype bool | None
        """
        # check against returned header, fall back to expected mimetype
        content_type = headers.get("Content-Type", self.mimetype)
        content_type = content_type.rsplit(";", 1)[0]  # remove things like utf8 metadata

        response_definition = self.operation.response_definition(str(status_code), content_type)
        response_schema = self.operation.response_schema(str(status_code), content_type)

        if self.is_json_schema_compatible(response_schema):
            v = ResponseBodyValidator(response_schema, validator=self.validator)
            try:
                data = self.operation.json_loads(data)

                #==================================================================
                #Added code
                
                data = self.response_trim(response_schema, data)
                #==================================================================

                v.validate_schema(data, url)
            except ValidationError as e:
                raise NonConformingResponseBody(message=str(e))

        if response_definition and response_definition.get("headers"):
            # converting to set is needed to support python 2.7
            response_definition_header_keys = set(response_definition.get("headers").keys())
            header_keys = set(headers.keys())
            missing_keys = response_definition_header_keys - header_keys
            if missing_keys:
                pretty_list = ', '.join(missing_keys)
                msg = ("Keys in header don't match response specification. "
                       "Difference: {0}").format(pretty_list)
                raise NonConformingResponseHeaders(message=msg)
        return data


    def __call__(self, function):
        """
        :type function: types.FunctionType
        :rtype: types.FunctionType
        """

        def _wrapper(request, response):
            connexion_response = \
                self.operation.api.get_connexion_response(response, self.mimetype)
            
            #==================================================================
            #Added code
            
            trim_data = self.validate_response(
                connexion_response.body, connexion_response.status_code,
                connexion_response.headers, request.url)

            response_with_trim_data = (trim_data,response[1])
            
            return response_with_trim_data
            #==================================================================

        if has_coroutine(function):
            from .coroutine_wrappers import get_response_validator_wrapper
            wrapper = get_response_validator_wrapper(function, _wrapper)

        else:  # pragma: 3 no cover
            @functools.wraps(function)
            def wrapper(request):
                response = function(request)
                return _wrapper(request, response)

        return wrapper


