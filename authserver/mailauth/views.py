# -* encoding: utf-8 *-
import json
import logging
from typing import Any

from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from oauth2_provider.forms import AllowForm
from oauth2_provider.models import get_application_model
from oauth2_provider.views.base import AuthorizationView

from mailauth.models import MNApplication, MNApplicationPermission
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


class WellKnownConfigView(View):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    def get(self, request: HttpRequest) -> HttpResponse:
        return HttpResponse(json.dumps({
            "issuer": request.get_host(),
            "authorization_endpoint": reverse('authorize'),
            "token_endpoint": reverse('token'),
            "scopes_supported": [perm.scope_name for perm in MNApplicationPermission.objects.all()],
            "grant_types_supported": ["authorization_code", "implicit", "password", "client_credentials"],
            "subject_types_supported": ["public", "private"],
            "response_types_supported": ["token"],
            "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
            # I don't think django-oauth-toolkit supports passing claims to oauthlib
            "claims_parameter_supported": False,
            "request_parameter_supported": False,
            "request_uri_parameter_supported": False
        }).encode('utf-8'), content_type="application/json", status=200)
