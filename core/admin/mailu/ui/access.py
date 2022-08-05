from mailu import models
from mailu.ui import forms

import flask
import flask_login
import functools


def permissions_wrapper(handler):
    """ Decorator that produces a decorator for checking permissions.
    """
    def callback(function, args, kwargs, dargs, dkwargs):
        authorized = handler(args, kwargs, *dargs, **dkwargs)
        if not authorized:
            flask.abort(403)
        elif type(authorized) is int:
            flask.abort(authorized)
        else:
            return function(*args, **kwargs)
    # If the handler has no argument, declare a
    # simple decorator, otherwise declare a nested decorator
    # There are at least two mandatory arguments
    if handler.__code__.co_argcount > 2:
        def decorator(*dargs, **dkwargs):
            def inner(function):
                @functools.wraps(function)
                def wrapper(*args, **kwargs):
                    return callback(function, args, kwargs, dargs, dkwargs)
                wrapper._audit_permissions = handler, dargs
                return flask_login.login_required(wrapper)
            return inner
    else:
        def decorator(function):
            @functools.wraps(function)
            def wrapper(*args, **kwargs):
                return callback(function, args, kwargs, (), {})
            wrapper._audit_permissions = handler, []
            return flask_login.login_required(wrapper)
    return decorator


@permissions_wrapper
def global_admin(args, kwargs):
    """ The view is only available to global administrators.
    """
    return flask_login.current_user.global_admin


@permissions_wrapper
def domain_admin(args, kwargs, model, key):
    """ The view is only available to specific domain admins.
    Global admins will still be able to access the resource.

    A model and key must be provided. The model will be queries
    based on the query parameter named after the key. The model may
    either be Domain or an Email subclass (or any class with a
    ``domain`` attribute which stores a related Domain instance).
    """
    obj = model.query.get(kwargs[key])
    if obj:
        domain = obj if type(obj) is models.Domain else obj.domain
        return domain in flask_login.current_user.get_managed_domains()


@permissions_wrapper
def owner(args, kwargs, model, key):
    """ The view is only available to the resource owner or manager.

    A model and key must be provided. The model will be queries
    based on the query parameter named after the key. The model may
    either be User or any model with a ``user`` attribute storing
    a user instance (like Fetch).

    If the query parameter is empty and the model is User, then
    the resource being accessed is supposed to be the current
    logged in user and access is obviously authorized.
    """
    if kwargs[key] is None and model == models.User:
        return True
    obj = model.query.get(kwargs[key])
    if obj:
        user = obj if type(obj) is models.User else obj.user
        return (
            user.email == flask_login.current_user.email
            or user.domain in flask_login.current_user.get_managed_domains()
        )

@permissions_wrapper
def bcc_owner(args, kwargs):
    """ The view is only available to the bcc owner or manager of a domain.

    A bcc_id must be provided. The access to the id is check against
    the current user. Access is also granted if the user is the admin
    of the domain of the bcc_id.
    """
    if 'bcc_id' in kwargs:
        bcc = models.Bcc.query.get(kwargs['bcc_id'])
        email = f'{bcc.localpart}@{bcc.domain}'
        return (
            email in flask_login.current_user.get_aliases()
            or bcc.domain in flask_login.current_user.get_managed_domains()
        )


@permissions_wrapper
def authenticated(args, kwargs):
    """ The view is only available to logged in users.
    """
    return True



def confirmation_required(action):
    """ View decorator that asks for a confirmation first.
    """
    def inner(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            form = forms.ConfirmationForm()
            if form.validate_on_submit():
                return function(*args, **kwargs)
            return flask.render_template(
                "confirm.html", action=action.format(*args, **kwargs),
                form=form
            )
        return wrapper
    return inner
