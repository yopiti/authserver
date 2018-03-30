# -* encoding: utf-8 *-
import json
import logging
from typing import Any, Optional, Union, List, NamedTuple

from django.contrib.auth import authenticate
from django.http import HttpResponseBadRequest
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from oauth2_provider.forms import AllowForm
from oauth2_provider.models import get_application_model
from oauth2_provider.views.base import AuthorizationView
from ratelimit.mixins import RatelimitMixin

from dockerauth.jwtutils import JWTViewHelperMixin
from mailauth.models import MNApplication, Domain
from mailauth.models import MNUser
from mailauth.permissions import find_missing_permissions


_log = logging.getLogger(__name__)


class ScopeValidationAuthView(AuthorizationView):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def form_valid(self, form: AllowForm) -> HttpResponse:
        """
        use the base class' form logic, but always behave like users didn't authorize the app
        if they doesn't have the permissions to do so.
        """
        app = get_application_model().get(client_id=form.cleaned_data.get('client_id'))
        missing_permissions = find_missing_permissions(app, self.request.user)
        if missing_permissions:
            form.cleaned_data['allow'] = False

        return super().form_valid(form)

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        _log.debug("ScopeValidationAuthView.get()")
        # super.get will initialize self.oauth2_data and now we can do additional validation
        resp = super().get(request, *args, **kwargs)

        app = self.oauth2_data['application']  # type: MNApplication

        missing_permissions = find_missing_permissions(app, request.user)

        _log.debug("missing_permissions: %s (%s)" %
                   (",".join([m.scope_name for m in missing_permissions]), bool(missing_permissions)))

        if missing_permissions:
            return render(
                request,
                "oauth2_provider/unauthorized.html",
                context={
                    "required_permissions": list(app.required_permissions.all()),
                    "missing_permissions": missing_permissions,
                    "username": (
                        str(request.user.delivery_mailbox) if request.user.delivery_mailbox
                        else request.user.identifier
                    ),
                }
            )

        # we have all necessary permissions, so we return the original response
        return resp


_AuthRequest = NamedTuple(
    "_AuthRequest", [
        ("username", str),
        ("password", str),
        ("scopes", List[str]),
    ]
)


class InvalidAuthRequest(Exception):
    pass


class UserLoginAPIView(JWTViewHelperMixin, RatelimitMixin, View):
    ratelimit_key = 'ip'
    ratelimit_rate = '20/m'
    ratelimit_block = True

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    @method_decorator(csrf_exempt)
    def dispatch(self, *args: Any, **kwargs: Any) -> HttpResponse:
        return super().dispatch(*args, **kwargs)

    def _find_domain(self, fqdn: str) -> Union[Domain, None]:
        # results in ['sub.example.com', 'example.com', 'com']
        req_domain = None  # type: Domain
        parts = request.get_host().split(".")
        for domainstr in [".".join(parts[r:]) for r in range(0, len(parts))]:
            try:
                req_domain = Domain.objects.get(name=domainstr)
            except Domain.DoesNotExist:
                continue
            else:
                if req_domain.jwtkey is not None and req_domain.jwtkey != "":
                    if domainstr == request.get_host() or req_domain.jwt_subdomains:
                        break
                    elif not req_domain.jwt_subdomains:
                        # prevent the case where domainstr is the last str in parts, it matches, has a jwtkey but
                        # is not valid for subdomains. req_domain would be != None in that case and the loop would exit
                        req_domain = None
                        continue

        return req_domain

    def _parse_request(self, request: HttpRequest) -> Dict[str, Union[str, List[str]]]:
        scopes = None  # type: List[str]
        if request.content_type == "application/json":
            data = json.loads(request.body.decode('utf-8'))
            if "username" not in data or "password" not in data:
                return HttpResponseBadRequest("Missing parameters")
            username = data['username']
            password = data['password']
            if "scopes" in data and isinstance(data["scopes"], list):
                scopes = data["scopes"]
        else:
            if "username" not in request.POST or "password" not in request.POST:
                raise InvalidAuthRequest()
            username = request.POST["username"]
            password = request.POST["password"]
            scopes = request.POST["scopes"].split(",")

        return _AuthRequest(
            username=username,
            password=password,
            scopes=scopes,
        )

    def post(self, request: HttpRequest) -> HttpResponse:
        if not request.is_secure():
            return HttpResponseBadRequest("This endpoint must be called securely")

        req_domain = self._find_domain(request.get_host())

        if req_domain is None:
            return HttpResponseBadRequest("Not a valid authorization domain")

        try:
            userdesc = self._parse_request(request)
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON")
        except InvalidAuthRequest:
            return HttpResponseBadRequest("Missing parameters")

        user = authenticate(username=userdesc.username, password=userdesc.password)  # type: MNUser
        if user is None:
            return HttpResponse(
                '{"authenticated": false}', content_type='application/json', status=401,
            )
        else:
            if user.delivery_mailbox is None:
                return HttpResponse(
                    '{"authenticated": false}', content_type='application/json', status=401,
                )

            return HttpResponse(
                '{"username": "%s", "canonical_username": "%s@%s", "authenticated": true }' %
                (userdesc.username, user.delivery_mailbox.mailprefix, user.delivery_mailbox.domain.name),
                content_type='application/json', status=200
            )
