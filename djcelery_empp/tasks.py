from celery.task import task
from django.conf import settings

from .connection import get_connection


CONFIG = getattr(settings, 'CELERY_EMPP_TASK_CONFIG', {})

TASK_CONFIG = {
    'name': 'djcelery_empp_send',
    'ignore_result': True,
    }
TASK_CONFIG.update(CONFIG)

@task(**TASK_CONFIG)
def send_sms(receiver, content):
    logger = send_sms.get_logger()
    try:
        _send_sms_with_cached_connection(receiver, content)
        logger.debug('successfully sent sms to %s.' % receiver)
    except Exception as e:
        logger.warning('failed to send sms to %s, retrying.' % receiver)
        send_sms.retry(exc = e)

def _send_sms_with_cached_connection(receiver, content, _cache = {}):
    '''
    try to use in-process connection cache
    '''
    conn = _cache.get('conn', None)
    if not conn or not conn.is_alive():
        conn = get_connection()
    conn.send_sms(receiver, content)
    _cache['conn'] = conn
