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
from lxml.builder import E


class EmailVision(object):
    """
    EmailVision REST API wrapper.
    """
    class Error(Exception):
        """
        Exception raised when an EmailVision API call fails either due to a
        network related error or for an EmailVision specific reason.
        """
        def __init__(self, error, code=None):
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

    def __init__(self, api, server, login, password, api_key, secure=True):
        """
        Create the API wrapper object.
        """
        if not (api and server):
            raise self.Error(
                u"API and API server URL must be specified.",
            )

        self.base_url = u"{protocol}://{server}/{api}/services/rest/".format(
            protocol=u"https" if secure else u"http",
            api=api,
            server=server,
        )
        self.token = None
        self.open(login, password, api_key)

    def __unicode__(self):
        return self.base_url

    def __str__(self):
        return unicode(self).encode("utf8")

    ##########################################
    # Methods to enable with statement usage #
    ##########################################

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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

    #################################################
    # Helper methods that are implementation detail #
    #################################################

    def _call_get_method(self, url, params):
        if self.token is not None:
            params["token"] = self.token
        url = "".join((self.base_url, url))
        try:
            return requests.get(url, params=params)
        except Exception as e:
            raise self.Error(
                u"Error connecting to EmailVision by HTTP GET: {0!r}".format(
                    e,
                ),
            )

    def _call_post_method(self, url, params):
        if self.token is not None:
            url = "".join((self.base_url, url, self.token))
        data = self._format_xml_params(params)
        try:
            return requests.post(url, data=data)
        except Exception as e:
            raise self.Error(
                u"Error connecting to EmailVision by HTTP POST: {0!r}".format(
                    e,
                ),
            )

    def _format_xml_params(self, params):
        # TODO
        return etree.tostring(E("root"), encoding="utf-8")

    def _parse_xml(self, text):
        try:
            return etree.fromstring(text)
        except Exception as e:
            raise self.Error(
                u"Error parsing response from EmailVision: {0!r}".format(e),
            )

    ######################
    # Public API methods #
    ######################

    def call(self, url, http_method="get", **params):
        """
        Call the REST API method at the given URL, using the given HTTP method
        with the parameters supplied.
        Returns the text of the response, or raises an EmailVision.Error if
        there is an error.
        """
        if http_method == "get":
            result = self._call_get_method(url, params)
        elif http_method == "post":
            result = self._call_post_method(url, params)
        else:
            raise self.Error(
                u"Internal API error: invalid HTTP method '{0}'".format(
                    http_method,
                ),
            )

        try:
            result.raise_for_status()
        except Exception as e:
            raise self.Error(u"{0!r}".format(e))

        return result.text

    def open(self, login, password, api_key):
        """
        Open the session connection with the API server.
        """
        if self.token is not None:
            raise self.Error(u"API server connection already open.")

        xml_tree = self._parse_xml(self.call("connect/open/",
                                             "get",
                                             login=login,
                                             pwd=password,
                                             key=api_key))
        try:
            self.token = xml_tree.xpath("/response/result[1]")[0].text
        except IndexError:
            raise self.Error(u"Unexpected response from EmailVision")

    def close(self):
        """
        Close the session connection with the API server.
        """
        xml_tree = self._parse_xml(self.call("connect/close/", "get"))
        try:
            result_text = xml_tree.xpath("/response/result[1]")[0].text
        except IndexError:
            raise self.Error(u"Unexpected response from EmailVision")

        if result_text == "connection closed":
            self.token = None
        else:
            raise self.Error(
                u"Failure to close API server connection: {0}".format(
                    result_text,
                ),
            )
