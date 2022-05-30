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
    DENY = 'DENY'
    UNRIPE = 'UNRIPE'  # 成熟


STATUS_CHOICES = [
    (STATUS.ASSIGNED, pgettext_lazy('STATUS', 'Assigned')),
    (STATUS.CANCELED, pgettext_lazy('STATUS', 'Canceled')),
    (STATUS.DONE, pgettext_lazy('STATUS', 'Done')),
    (STATUS.ERROR, pgettext_lazy('STATUS', 'Error')),
    (STATUS.NEW, pgettext_lazy('STATUS', 'New')),
    (STATUS.PREPARED, pgettext_lazy('STATUS', 'Prepared')),
    (STATUS.SCHEDULED, pgettext_lazy('STATUS', 'Scheduled')),
    (STATUS.STARTED, pgettext_lazy('STATUS', 'Started')),
    (STATUS.DENY, pgettext_lazy('STATUS', 'Denied')),
    (STATUS.UNRIPE, pgettext_lazy('STATUS', 'Unripe')),
]

STATUS_DISPLAY = {
    'ASSIGNED': '待处理',
    'CANCELED': '取消、撤回',
    'DONE': '已完成',
    'ERROR': '错误',
    'NEW': '新创建',
    'PREPARED': '准备中',
    'SCHEDULED': '排期中',
    'STARTED': '已开始',
    'DENY': '驳回',
    'UNRIPE': '未知',
}

FIRST_TASK_STATUS_DISPLAY = {
    'ASSIGNED': '待处理',
    'CANCELED': '取消、撤回',
    'DONE': '已提交,待审核',
    'ERROR': '错误',
    'NEW': '新创建',
    'PREPARED': '准备中',
    'SCHEDULED': '排期中',
    'STARTED': '已开始',
    'DENY': '驳回',
    'UNRIPE': '未知',
}
