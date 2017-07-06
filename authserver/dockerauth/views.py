# -* encoding: utf-8 *-

# Support for the Docker OAuth2 token authentication
# The Docker client submits username and password through basic authentication,
# but using a GET request. Using the actual OAuth2 spec would be *just* *too* *hard*.
import base64
import re
import logging
from typing import NamedTuple, Dict, Any

from django.conf import settings
from django.contrib.auth import authenticate
from django.http.request import HttpRequest
from django.http.response import HttpResponse, HttpResponseNotFound, HttpResponseForbidden
from django.views.generic.base import View
from oauth2_provider.views.mixins import OAuthLibMixin
from oauth2_provider.settings import oauth2_settings

from dockerauth.models import DockerRepo
from mailauth.models import MNApplication

_TokenRequest = NamedTuple('_TokenRequest', [
    ('service', str),
    ('offline_token', bool),
    ('client_id', str),
    ('scope', str),
])


_TokenPermissions = NamedTuple('_TokenPermissions', [
    ("type", str),
    ("path", str),
    ("pull", bool),
    ("push", bool),
])


_log = logging.getLogger(__name__)


def _tkr_parse(params: Dict[str, str]) -> _TokenRequest:
    return _TokenRequest(
        service=params.get("service", None),
        offline_token=params.get("offline_token", "false") == "true",
        client_id=params.get("client_id", None),
        scope=params.get("scope", None)
    )


def _parse_scope(scope: str) -> _TokenPermissions:
    """
    :raises: ValueError when scope has the wrong type
    :param scope:
    :return: a repository permission object
    """
    typ, path, perms = scope.split(":", 2)

    if typ != "repository":
        raise ValueError("The requested permission scope is not of type repository - %s" % scope)

    for p in perms.split(","):
        if p not in ["pull", "push"]:
            raise ValueError("Client requested unknown permissions (not push or pull) - %s" % scope)

    return _TokenPermissions(
        type=typ,
        path=path,
        pull="pull" in perms,
        push="push" in perms,
    )


class DockerAuthView(OAuthLibMixin, View):
    server_class = oauth2_settings.OAUTH2_SERVER_CLASS
    validator_class = oauth2_settings.OAUTH2_VALIDATOR_CLASS
    oauthlib_backend_class = oauth2_settings.OAUTH2_BACKEND_CLASS

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        tr = _tkr_parse(request.GET)

        keys = sorted(filter(lambda k: re.match(r'(HTTP_|CONTENT_)', k), request.META))
        keys = ['REMOTE_ADDR'] + keys
        meta = ''.join("%s=%s\n" % (k, request.META[k]) for k in keys)

        _log.info('"%s %s\n%s' % (request.method, request.build_absolute_uri(), meta))

        try:
            client = MNApplication.objects.get(client_id=tr.client_id)
        except MNApplication.DoesNotExist:
            return HttpResponseNotFound("No such client")

        if client.authorization_grant_type != MNApplication.GRANT_PASSWORD:
            return HttpResponseForbidden("Client must be authorized for resource-owner password mode of operation")

        if tr.scope:
            tp = _parse_scope(tr.scope)
        else:
            tp = _TokenPermissions(
                type="login",
                path="",
                pull=False,
                push=False
            )

        try:
            drepo = DockerRepo.objects.get(name=tp.path)
        except DockerRepo.DoesNotExist:
            if settings.DOCKERAUTH_ALLOW_UNCONFIGURED_REPOS:
                drepo = DockerRepo()
                drepo.name = tp.path
                drepo.unauthenticated_read = True
                drepo.unauthenticated_write = True
            elif tp.type == "login":
                drepo = DockerRepo()
                drepo.name = tp.path
                drepo.unauthenticated_read = False
                drepo.unauthenticated_write = False
            else:
                return HttpResponseNotFound("No such repo '%s'" % tp.path)

        if not tr.offline_token:
            return HttpResponseForbidden("authserver only supports authentication for docker 1.11 or higher")

        if "HTTP_AUTHORIZATION" in request.META:
            basic, b64str = request.META["HTTP_AUTHORIZATION"].split(" ", 1)

            if basic != "Basic":
                return HttpResponseForbidden("Unsupported auth type (must be Basic)")

            basic_auth = base64.b64decode(b64str).decode('utf-8')
            try:
                username, password = basic_auth.split(":", 1)
            except ValueError:
                return HttpResponseForbidden("Invalid basic auth string")

            if authenticate(request, username=username, password=password) or \
                    (drepo.unauthenticated_pull and tp.pull) or \
                    (drepo.unauthenticated_push and tp.push):
                url, headers, body, status = self.create_token_response(request)
                response = HttpResponse(content=body, status=status)

                for k, v in headers.items():
                    response[k] = v
                return response
            else:
                return HttpResponseForbidden("Authentication failed")
        else:
            return HttpResponseForbidden("No authentication credentials provided")
