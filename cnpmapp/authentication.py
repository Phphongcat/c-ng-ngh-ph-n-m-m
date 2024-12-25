from functools import wraps
from flask_login import current_user
from flask import redirect


def login_required(f):
    @wraps(f)
    def authentication_function(*args, **kwargs):
        if current_user.is_authenticated is False:
            return redirect('/')
        return f(*args, **kwargs)

    return authentication_function


def anonymous_user(f):
    @wraps(f)
    def anonymous_function(*args, **kwargs):
        if current_user.is_authenticated:
            return redirect('/')
        return f(*args, **kwargs)

    return anonymous_function