from connexion.decorators.response import ResponseValidator
from connexion.decorators.validation import ResponseBodyValidator
from jsonschema import ValidationError
from connexion.exceptions import (NonConformingResponseBody,
                          NonConformingResponseHeaders)
from connexion.operations import abstract
from connexion.utils import all_json

class CustomResponseValidator(ResponseValidator):

    # code from https://github.com/zalando/connexion/blob/96bdcb010a4e5180c2bce18295e7b576c9c1ef0f/connexion/decorators/response.py#L16

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

        if self.is_json_schema_compatible(response_schema,content_type):
            v = ResponseBodyValidator(response_schema, validator=self.validator)
            try:
                data = self.operation.json_loads(data)
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
        return True
    
    def is_json_schema_compatible(self, response_schema, content_type):
        """
        Verify if the specified operation responses are JSON schema
        compatible.
        All operations that specify a JSON schema and have content
        type "application/json" or "text/plain" can be validated using
        json_schema package.
        :type response_schema: dict
        :rtype bool
        """
        if not response_schema:
            return False
        return all_json([content_type]) or content_type == 'text/plain'