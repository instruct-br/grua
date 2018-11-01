import time
import schedule

from jobs.master import enqueue_update

schedule.every(30).minutes.do(enqueue_update)

while True:
    schedule.run_pending()
    time.sleep(1)
