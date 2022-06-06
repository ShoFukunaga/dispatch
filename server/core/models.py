import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.shortcuts import reverse


class User(AbstractUser):
    pass


class Dispatch(models.Model):
    REQUESTED = 'REQUESTED'
    STARTED = 'STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'

    STATUSES = (
        (REQUESTED, REQUESTED),
        (STARTED, STARTED),
        (IN_PROGRESS, IN_PROGRESS),
        (COMPLETED, COMPLETED),
    )

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        auto_now=True,
    )
    request_location = models.CharField(
        max_length=256,
    )
    destination = models.CharField(
        max_length=256,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUSES,
        default=REQUESTED
    )
    contractor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name='contractors',
    )
    requestor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.DO_NOTHING,
        related_name='requestors',
    )

    def __str__(self):
        return f'{self.id}'

    def get_absolute_url(self):
        return reverse('core:dispatch_detail', kwargs={'dispatch_id': self.id})
