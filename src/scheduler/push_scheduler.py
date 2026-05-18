"""定时推送调度器 —— 使用 APScheduler 定时触发 Agent。"""

import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger


class PushScheduler:
    """管理定时推送任务的启动、停止、配置更新。"""

    def __init__(self, callback):
        """
        Args:
            callback: 无参函数，触发推送时调用
        """
        self._callback = callback
        self._scheduler = BackgroundScheduler()
        self._job = None
        self._interval_minutes = 60

    def start(self, interval_minutes: int = 60):
        """启动调度器。"""
        self._interval_minutes = interval_minutes
        if self._job:
            self._job.remove()
        self._job = self._scheduler.add_job(
            self._callback,
            IntervalTrigger(minutes=interval_minutes),
            id="push_job",
            replace_existing=True,
        )
        if not self._scheduler.running:
            self._scheduler.start()

    def stop(self):
        """停止调度器。"""
        if self._job:
            self._job.remove()
            self._job = None
        if self._scheduler.running:
            self._scheduler.shutdown(wait=False)

    def update_interval(self, interval_minutes: int):
        """更新推送间隔。"""
        self._interval_minutes = interval_minutes
        if self._job:
            self._job.remove()
            self._job = self._scheduler.add_job(
                self._callback,
                IntervalTrigger(minutes=interval_minutes),
                id="push_job",
                replace_existing=True,
            )

    def is_within_time_window(self, start_hour: int, end_hour: int) -> bool:
        """判断当前时间是否在推送时间窗口内。"""
        now = datetime.datetime.now()
        if start_hour <= end_hour:
            return start_hour <= now.hour < end_hour
        else:
            return now.hour >= start_hour or now.hour < end_hour

    @property
    def is_running(self) -> bool:
        return self._scheduler.running and self._job is not None
