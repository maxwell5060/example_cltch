@huey.periodic_task(crontab(minute='0', hour='3'))
def calltouch():
    CalltouchGetter.run()


if __name__ == "__main__":
    pass
