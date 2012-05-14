from itertools import imap
from django.conf import settings
from datetime import datetime, time, timedelta


INTERVALS = getattr(settings, 'EMPP_VALID_INTERVALS',
                    ((time.min, time.max), ))

def send_sms(receiver, content):
    from tasks import send_sms
    send_sms.delay(receiver, content)

def schedule_sms(receiver, content):
    from tasks import send_sms
    now = datetime.now()
    current_time = now.time()
    if any(imap(lambda x: x[0] <= current_time and current_time <= x[1],
                INTERVALS)):
        send_sms.delay(receiver, content)
        return
    availables = filter(lambda x: current_time <= x,
                        imap(lambda x:x[0], INTERVALS))
    if availables:
        # send it at the beginning of next interval
        eta = datetime.combine(now.date(), min(availables))
        send_sms.apply_async(args = [receiver, content], eta = eta)
    else:
        # send it tomorrow
        eta = datetime.combine((now + timedelta(days = 1)).date(),
                               min(imap(lambda x: x[0], INTERVALS)))
        send_sms.apply_async(args = [receiver, content], eta = eta)
