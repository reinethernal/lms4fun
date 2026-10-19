from .models import AuditLog, Notification


def create_notification(user, notification_type, title, message='', data=None):
    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        data_json=data or {},
    )


def log_audit(user=None, action='', entity_type='', entity_id='', details=None, request=None):
    ip_address = None
    user_agent = ''
    if request is not None:
        forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded:
            ip_address = forwarded.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    return AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else '',
        details_json=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
