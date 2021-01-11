from apscheduler.schedulers.background import BackgroundScheduler

class GlobalScheduler():
    def __init__(self,scheduler):
        self.scheduler=scheduler

scheduler = BackgroundScheduler()
instance_GlobalScheduler=GlobalScheduler(scheduler)
scheduler.start()


