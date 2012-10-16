"""
Copyright 2012 42 Ventures Pte Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import requests
from lxml import etree


class EmailVision(object):
    """
    EmailVision REST API wrapper.
    """

    #####################
    # Exception classes #
    #####################

    class Error(Exception):
        """
        Exception raised when an EmailVision API call fails either due to a
        network related error or for an EmailVision specific reason.
        """
        def __init__(self, error, code=None):
            """
            Create the Error exception object.

            error: error message
            code: EmailVision error code
            """
            self.error = error
            self.code = code
            if self.code is not None:
                try:
                    self.code = int(self.code)
                except ValueError:
                    pass

        def __unicode__(self):
            if self.code is None:
                message = self.error
            else:
                message = u"{error} ({code})".format(error=self.error,
                                                     code=self.code)
            return u"EmailVision.Error({message})".format(message=message)

        def __str__(self):
            return unicode(self).encode("utf8")

        def __repr__(self):
            return str(self)

    ####################
    # Standard methods #
    ####################

    def __init__(self, server, api, login, password, api_key, secure=True):
        """
        Create the API wrapper object.

        server: URI identifying the EmailVision server to access, e.g.,
                "example.com"
        api: name of the EmailVision API to use, e.g., "apimember"
        login: API user account login username
        password: API user account password
        api_key: API key
        secure: HTTPS is used if True, otherwise HTTP is used
        """
        if not (server and api):
            raise self.Error(
                u"API server and API name must be specified.",
            )

        self._base_url = u"{protocol}://{server}/{api}/services/rest/".format(
            protocol=u"https" if secure else u"http",
            server=server,
            api=api,
        )
        self._token = None
        self.open(login, password, api_key)

    def __unicode__(self):
        """
        Returns Unicode string containing the base URL used for API calls.
        """
        return self._base_url

    def __str__(self):
        """
        Returns string version of Unicode string representation.
        """
        return unicode(self).encode("utf8")

    def __enter__(self):
        """
        Enables with statement usage.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Close connection prior to exiting the with statement.
        """
        try:
            self.close()
        except Exception as e:
            if exc_val is None:
                raise
            else:
                # Combine the exception passed in with this exception:
                raise self.Error(
                    u"Connection close failure: {0}; "
                    u"Exception raised prior to connection close: {1}".format(
                        e,
                        exc_val,
                    ),
                )
        return False

    ######################
    # Public API methods #
    ######################

    @property
    def token(self):
        """
        Returns the API token from EmailVision.
        """
        return self._token

    def get(self, path, query_string_params=None, parse_xml=True):
        """
        Call the EmailVision REST API method at the given path using HTTP GET.
        Returns the element tree obtained from parsing the response text as an
            XML document if parse_xml is True, otherwise returns the text of
            the response as a unicode string.
        Raises an EmailVision.Error if there is an error.

        Specifying the path:
        For the "path info" API, the path is a string with the API parameters
            fill in. For example, if the docs state:
            http://{server}/apiccmd/services/rest/campaign/last/{token}/{limit}
            Then the path might be: "campaign/last/foo/123", where the token is
            obtained through the token property of the EmailVision object.
        For the "query string" API, the query_string_params argument should
            be supplied. For example:
            path="campaign/last"
            query_string_params={"token": foo, "limit": 123}
        """
        if query_string_params is None:
            query_string_params = {}
        query_string_params["type"] = "xml"

        url = u"".join((self._base_url, path))
        try:
            response = requests.get(url, params=query_string_params)
        except Exception as e:
            raise self.Error(
                u"HTTP GET request for API call failed: {0!r}".format(e),
            )

        self._check_response_status(response)
        return (self._parse_xml(response.content) if parse_xml else
                response.text)

    def post(self, path, payload=None, parse_xml=True):
        """
        Call the EmailVision REST API method at the given path using HTTP POST.
        Returns the element tree obtained from parsing the response text as an
            XML document if parse_xml is True, otherwise returns the text of
            the response as a unicode string.
        Raises an EmailVision.Error if there is an error.

        Specifying the path:
        The path is a string with the API parameters filled in. For example, if
            the docs state:
            http://{server}/apiccmd/services/rest/message/create/{token}
            Then the path might be: "message/create/foo" where the token is
            obtained through the token property of the EmailVision object.

        Specifying the payload:
        If provided, the payload is a string (most likely an XML document) that
            is sent as the HTTP POST payload. A dictionary of name/value pairs
            may also be supplied as the payload.
        """
        url = u"".join((self._base_url, path))
        try:
            response = requests.post(url, data=payload, params={"type": "xml"})
        except Exception as e:
            raise self.Error(
                u"HTTP POST request for API call failed: {0!r}".format(e),
            )

        self._check_response_status(response)
        return (self._parse_xml(response.content) if parse_xml else
                response.text)

    def open(self, login, password, api_key):
        """
        Open the session connection with the API server, setting the token.

        This will be called automatically when the object is created, so it
        should only be used to reinitialise the connection after calling close.
        """
        if self._token is not None:
            raise self.Error(u"API server connection already open.")

        path = "connect/open/{login}/{password}/{api_key}".format(
            login=login,
            password=password,
            api_key=api_key,
        )
        response_xml = self.get(path)
        try:
            self._token = response_xml.xpath("/response/result[1]")[0].text
        except IndexError:
            raise self.Error(u"Unexpected response from EmailVision.")

    def close(self):
        """
        Close the session connection with the API server.
        """
        path = "connect/close/{token}".format(token=self._token)
        response_xml = self.get(path)
        try:
            result_text = response_xml.xpath("/response/result[1]")[0].text
        except IndexError:
            raise self.Error(u"Unexpected response from EmailVision")

        if result_text == "connection closed":
            self._token = None
        else:
            raise self.Error(
                u"Failure to close API server connection: {0}".format(
                    result_text,
                ),
            )

    ##########################################
    # Helper methods (implementation detail) #
    ##########################################

    def _check_response_status(self, response):
        try:
            response.raise_for_status()
        except Exception as e:
            raise self.Error(u"{0!r}".format(e))

    def _parse_xml(self, text):
        try:
            return etree.fromstring(text)
        except Exception as e:
            raise self.Error(
                u"Could not parse response from EmailVision: {0!r}".format(e),
            )
