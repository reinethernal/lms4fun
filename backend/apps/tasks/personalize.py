def student_display_name(user) -> str:
    if user is None:
        return 'ученик'
    return (getattr(user, 'display_name', None) or getattr(user, 'username', None) or 'ученик').strip()


def personalize_text(text: str, user) -> str:
    if not text:
        return text
    name = student_display_name(user)
    for token in ('{{ student_name }}', '{ student_name }', '{student_name}'):
        text = text.replace(token, name)
    return text
