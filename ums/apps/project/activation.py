from django.db import transaction
from django.utils.timezone import now
from django.utils.translation import pgettext_lazy


class STATUS:
    """Activation status constants used in the viewflow.
    3d party code can use any other strings in addition to build in
    status codes.
    """

    ASSIGNED = 'ASSIGNED'
    CANCELED = 'CANCELED'
    DONE = 'DONE'
    ERROR = 'ERROR'
    NEW = 'NEW'
    PREPARED = 'PREPARED'
    SCHEDULED = 'SCHEDULED'
    STARTED = 'STARTED'
    UNRIPE = 'UNRIPE'


STATUS_CHOICES = [
    (STATUS.ASSIGNED, pgettext_lazy('STATUS', 'Assigned')),
    (STATUS.CANCELED, pgettext_lazy('STATUS', 'Canceled')),
    (STATUS.DONE, pgettext_lazy('STATUS', 'Done')),
    (STATUS.ERROR, pgettext_lazy('STATUS', 'Error')),
    (STATUS.NEW, pgettext_lazy('STATUS', 'New')),
    (STATUS.PREPARED, pgettext_lazy('STATUS', 'Prepared')),
    (STATUS.SCHEDULED, pgettext_lazy('STATUS', 'Scheduled')),
    (STATUS.STARTED, pgettext_lazy('STATUS', 'Started')),
    (STATUS.UNRIPE, pgettext_lazy('STATUS', 'Unripe')),
]
