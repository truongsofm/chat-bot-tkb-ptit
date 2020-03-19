import datetime

from pytz import timezone

now = datetime.datetime.now(tz=timezone("Asia/Saigon"))
print(now.strftime("%A %d-%m-%Y"))