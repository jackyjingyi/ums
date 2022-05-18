import logging
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from guardian.shortcuts import assign_perm, get_users_with_perms, get_user_perms, remove_perm, get_perms
from .models import Process, Task, Achievement
from .serializers import ProcessSerializer
from .activation import STATUS, STATUS_CHOICES
from .utils import AchievementStateChoices

User = get_user_model()


class ProcessHandler:
    model = None
    status_field = ''

    def submit(self):
        pass

    def done(self):
        pass

    def withdraw(self):
        pass

    def get_status(self):
        pass

    @classmethod
    def create_process(cls, instance, *args, **kwargs):
        pass

    @classmethod
    def create_tasks(cls, process, init_task):
        pass


class AchievementProcessHandler(ProcessHandler):
    model = Achievement


class AchievementProcessHandlerFirstStage(AchievementProcessHandler):
    status_field = 'status1'

    @classmethod
    def create_process(cls, instance, *args, **kwargs):
        """
        kwargs :{
        flow_type: SINGLE, JOIN, OR,
        comments: '',
        }
        """
        flow_type = kwargs.get('flow_type', 'SINGLE')
        approver = kwargs.get('required_approver', None)
        perm = 'approve_achievement_lv1'
        print(type(approver), approver)
        if not approver:
            approver = [
                {'id': u.id, 'name': u.name} for u in
                instance.project.project_sponsor.all()
            ]
        else:
            print(type(approver), type(approver[0]))
        level = kwargs.get('level', 1)
        if level == 2:
            perm = 'approve_achievement_lv2'
        if not flow_type:
            logging.error(f'No flow type provided for instance {instance._meta.model.__name__} {instance.pk}')
        content_type_object = ContentType.objects.get(app_label=instance._meta.app_label,
                                                      model=instance._meta.model.__name__)

        process = Process(
            artifact_content_type=content_type_object, artifact_object_id=instance.pk,
            data={
                # store flow attributes
                'flow_type': flow_type,  # 会签JOIN，或签OR，单签SINGLE
                # 'due_range': 30
                'approve': approver,
                'owner': {'id': instance.creator.id, 'name': instance.creator.name},
                'allow_withdraw': True,
                'show_other_output': True,  # 向其他用户展示成果（仅展示）
                'activation': 'approval',
                'permission': perm,
                'stage': level,
                'is_resubmit': 0
            }
        )
        logging.info(process.data)
        #
        process.save()
        # create first task
        comments = kwargs.get('comments', '')
        task = Task(
            process=process,
            flow_task_type=flow_type,
            artifact_content_type=content_type_object,
            artifact_object_id=instance.pk,
            owner=instance.creator,
            # external_task_id
            owner_permission='submit_achievement',
            comments=comments,
            status=STATUS.DONE,  # 提交已完成
            data={
                'is_withdraw': 0,
                'is_first': 1  # 是首个task
            }
        )
        task.assigned = timezone.now()
        task.started = timezone.now()
        task.finished = timezone.now()
        task.save()
        cls.create_tasks(process, task)
        return process

    @classmethod
    def create_tasks(cls, process, init_task):
        data = process.data
        flow_type = data.get('flow_type')

        task_list = []
        # 为每个用户创建task
        for item in data.get('approve'):
            task = Task(
                process=process,
                flow_task_type=flow_type,
                artifact_content_type=init_task.artifact_content_type,
                artifact_object_id=init_task.artifact_object_id,
                owner=User.objects.get(id=item.get('id')),
                # external_task_id
                owner_permission=data.get("permission"),
                status=STATUS.ASSIGNED,  # 提交已完成，分配给sponsor
                data={
                    'is_first': 0
                }
            )
            task.assigned = timezone.now()
            task.started = timezone.now()
            task.save()
            task.previous.add(init_task)
            task_list.append(task)
        return task_list


class ActionHandler:

    def __init__(self, instance):
        self.instance = instance
        self.content_type_object = ContentType.objects.get(app_label=instance._meta.app_label,
                                                           model=instance._meta.model.__name__)
        self.object_id = instance.pk

    def get_process(self):

        processes = Process.objects.filter(
            artifact_content_type=self.content_type_object, artifact_object_id=self.object_id,
        ).order_by('-created')
        return processes[0]

    def withdraw(self, comments):
        process = self.get_process()
        tasks = Task.objects.filter(
            process=process
        ).order_by('-created')
        task = Task(
            process=process,
            flow_task_type=process.data.get('flow_type', 'SINGLE'),
            artifact_content_type=self.content_type_object,
            artifact_object_id=self.object_id,
            owner=self.instance.creator,
            owner_permission='withdraw_achievement',
            comments=comments,
            status=STATUS.CANCELED,  # 提交已完成
            data={
                'is_withdraw': 1,
                'is_first': 0  # 是首个task
            },
        )
        task.assigned = timezone.now()
        task.started = timezone.now()
        task.finished = timezone.now()
        task.save()
        task.previous.add(
            tasks[0]
        )
        for t in tasks:
            if t.status != STATUS.DONE and t.status != STATUS.ERROR and t.status != STATUS.CANCELED:
                t.status = STATUS.CANCELED
                t.comments = '提交人撤销，自动处理。'
                t.save()
        process.status = STATUS.CANCELED
        process.comments = '提交人撤销，自动处理。'
        process.finished = timezone.now()
        process.save()
        return process

    def approve(self, comments, user):
        # 判断几级审批
        process = self.get_process()
        stage = process.data.get('stage', 1)
        if stage == 1:
            self._approve(process, comments, user, 1)
        else:
            self._approve(process, comments, user, 2)
        # 找到第一个task
        first_task = Task.objects.get(
            process=process,
            data__is_first=1,
            owner_permission__contains='submit'
        )
        if process.data.get('flow_type', 'SINGLE') == 'JOIN':
            # 如果是join，需要等待所有审批人通过
            if self.perform_join(first_task):
                # all done
                # 更改process
                process.status = STATUS.DONE
                process.finished = timezone.now()
                process.save()
        else:
            if process.data.get('flow_type', 'SINGLE') == 'OR':
                # 将所有task状态改为通过
                self.perform_or(first_task, STATUS.DONE)
            process.status = STATUS.DONE
            process.finished = timezone.now()
            process.save()
        self._approval_after(process, user, stage)
        return process

    def _approval_after(self, process, user, stage):
        # todo  分配权限
        perm = 'approve_achievement_lv1'
        if stage == 2:
            perm = 'approve_achievement_lv2'
        # all conditions user need remove permission
        remove_perm(perm, user, self.instance)

        # 如果是第一级审批，需要分配给当前用户提交权限（要求process status == DONE)
        if stage == 1 and process.status == STATUS.DONE:  # 谁审批，谁提交
            # 成果的一级审批标签变为完成
            self.instance.status1 = STATUS.DONE
            self._flush_perms(stage)
            # 重新为当前审批负责人分配权限
            assign_perm('change_achievement', user, self.instance)
            assign_perm('submit_achievement', user, self.instance)
            assign_perm('delete_achievement', user, self.instance)
            # 去掉 approve_achievement_lv1的所有权限
            # 如果通过，去掉一级提交人（一般是作者）的withdraw权限
        if stage == 2 and process.status == STATUS.DONE:
            # 如果结束，去掉所有leader的 approval权限
            # 收回所有用户的withdraw，change， submit， delete权限
            self._flush_perms(stage)
            self.instance.state = AchievementStateChoices.APP.value
            self.instance.status2 = STATUS.DONE
        self.instance.state = AchievementStateChoices.APP.value
        self.instance.save()

    def _flush_perms(self, stage):
        # 1. achievement creator
        creator = self.instance.creator
        sponsors = self.instance.project.project_sponsor.all()
        leaders = self.instance.project.project_approver.all()

        # when lv1 pass
        # remove creator's withdraw permission, and change/submit/delete(if have)
        remove_perm('withdraw_achievement', creator, self.instance)
        remove_perm('change_achievement', creator, self.instance)
        remove_perm('delete_achievement', creator, self.instance)
        remove_perm('submit_achievement', creator, self.instance)

        # sponsor 已经审批完毕，释放app权限，
        for sponsor in sponsors:
            remove_perm('withdraw_achievement', sponsor, self.instance)
            remove_perm('submit_achievement', sponsor, self.instance)
            remove_perm('delete_achievement', sponsor, self.instance)
            remove_perm('approval_achievement_lv1', sponsor, self.instance)
        if stage == 1:
            return True
        for leader in leaders:
            # 回收所有用户权限，主要为leader的approval 权限
            remove_perm('withdraw_achievement', leader, self.instance)
            remove_perm('submit_achievement', leader, self.instance)
            remove_perm('delete_achievement', leader, self.instance)
            remove_perm('approval_achievement_lv2', leader, self.instance)
        return True

    def perform_join(self, task):
        task_list = task.leading.all()
        all_done = True
        for task in task_list:
            if task.status != STATUS.DONE:
                all_done = False
        return all_done

    def perform_or(self, task, status):
        task_list = task.leading.all()
        for task in task_list:
            if task.status != STATUS.DONE and task.status != STATUS.CANCELED:
                task.status = status
                task.finished = timezone.now()
                task.save()

    def _approve(self, process, comments, user, stage):
        perm = 'approve_achievement_lv1'
        if stage == 2:
            perm = 'approve_achievement_lv2'
        try:
            users_task = Task.objects.get(
                status=STATUS.ASSIGNED,
                owner=user,
                artifact_content_type=self.content_type_object,
                artifact_object_id=self.object_id,
                owner_permission=perm,
                process=process
            )
            users_task.status = STATUS.DONE
            users_task.finished = timezone.now()
            users_task.comments = comments
            print(users_task)
            users_task.save()
        except Exception as e:
            # todo: raise 500
            print(e)
            raise Exception
