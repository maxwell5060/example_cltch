import os
from datetime import datetime, timedelta
from functools import wraps
from time import time

from luigi.contrib import postgres

from backend.grabbers.call_touch import CalltouchGrabber
from backend.settings.main import CONFIG


def d_range(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


def timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print(f'Elapsed time {f}: {int((end - start) * 1000)}')

        return result
    return wrapper


class BaseCalltouchGetter(postgres.CopyToTable):
    STAGE = os.getenv('STAGE')
    APP = os.getenv('APP')

    @property
    def host(self):
        return CONFIG[self.STAGE][self.APP]['host']

    @property
    def database(self):
        return CONFIG[self.STAGE][self.APP]['database']

    @property
    def user(self):
        return CONFIG[self.STAGE][self.APP]['used']

    @property
    def password(self):
        return CONFIG[self.STAGE][self.APP]['password']

    @property
    def port(self):
        return CONFIG[self.STAGE][self.APP]['port']

    @property
    def table(self):
        return CONFIG[self.STAGE][self.APP]['table']

    @property
    def update_id(self):
        date = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d_%H:%M')
        return f'CalltouchGetter_{self.table}_{date}'

    @property
    def call_touch_grabber(self):
        return CalltouchGrabber(CONFIG[self.STAGE]['calltouch_user_id'], CONFIG[self.STAGE]['calltouch_token'])

    column_separator = ";"
