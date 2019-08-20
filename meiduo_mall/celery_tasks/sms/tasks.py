from celery_tasks.main import celery_apps
from celery_tasks.yuntongxun.ccp_sms import CCP


@celery_apps.task(name='send_sms_code')
def send_sms_code(mobile,sms_code):
    """
    发送短信验证码
    :return:
    """
    result = CCP().send_template_sms(mobile,[sms_code,5],1)
    return result