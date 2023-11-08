from django.db import models
from django.utils.translation import gettext_lazy as _



class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_('Created At'), help_text='')
    
    updated_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name=_('Updated At'), help_text='')

    is_active = models.BooleanField(default=True,
                                    verbose_name=_('Is Active'), help_text='')
    
    class Meta:
        abstract = True
