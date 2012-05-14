django-celery-empp
==================

A Django client of China Mobile Enterprise SMS, which uses [Celery](https://github.com/ask/django-celery) queue for sending and scheduling messages.


To enable ``django-celery-empp`` for your project, you need to add ``djcelery_empp`` and ``djcelery`` to ``INSTALL_APPS``:

	INSTALLED_APPS += ("djcelery_empp", "djcelery", )

then add the following lines to your ``settings.py``:

	SMS_HOST = '127.0.0.1'          # the ip of chinamobile empp server
	SMS_PORT = 9981                 # server port
	SMS_ACCOUNT = '10650123456789'  # your account
	SMS_PASSWORD = 'password'       # your password

To send messages is very simple:

	from djcelery_empp import send_sms
	receiver = '12345678901'
	content = u'hello world'
	send_sms(receiver, content)

If you need to send messages only in certain time intervals in a day, please also set the ``EMPP_VALID_INTERVALS`` in your ``settings.py``:

	from datetime import time
	EMPP_VALID_INTERVALS = (
		(time(hour = 8), time(hour = 12, minute = 30)),
		(time(hour = 14), time(hour = 21)),
    )

Then:

	from djcelery_empp import schedule_sms
	schedule_sms(receiver, content)

the scheduler will send the message in the beginning of next valid time interval (maybe in the next day), or immediately if current time is in any of the intervals.
