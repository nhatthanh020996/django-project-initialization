from django.utils.translation import gettext_lazy as _

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions



class PartnerAuthentication(BaseAuthentication):
    def authenticate(self, request):
        """
        """
        pass