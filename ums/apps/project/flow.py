from .models import Achievement


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

    def create_formula(self, *args, **kwargs):
        pass


class AchievementProcessHandler(ProcessHandler):
    model = Achievement


class AchievementProcessHandlerFirstStage(AchievementProcessHandler):
    status_field = 'status1'

    def create_formula(self, *args, **kwargs):
        pass