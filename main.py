# This is a sample Python script.

from apscheduler.schedulers.blocking import BlockingScheduler

import request_url

if __name__ == '__main__':
    scheduler = BlockingScheduler()

    request_url.rush_to_buy("1704487985300381698", scheduler)
    for job in scheduler.get_jobs():
        print(f"id:{job.id},{scheduler.get_job(job.id)}, 函数{scheduler.get_job(job.id).func}")
    scheduler.start()
