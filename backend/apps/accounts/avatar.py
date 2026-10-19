import uuid


def avatar_upload_path(instance, filename: str) -> str:
    ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else 'jpg'
    return f'avatars/user_{instance.pk}_{uuid.uuid4().hex[:8]}.{ext}'


def user_avatar_url(user, request=None) -> str:
    if getattr(user, 'avatar_image', None):
        url = user.avatar_image.url
        if request:
            return request.build_absolute_uri(url)
        return url
    return user.avatar or ''
