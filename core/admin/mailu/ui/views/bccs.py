from mailu import models
from mailu.ui import ui, forms, access

import flask
import flask_login


@ui.route('/bcc/list/user', methods=['GET', 'POST'], defaults={'user_email': None})
@ui.route('/bcc/list/user/<path:user_email>', methods=['GET'])
@access.owner(models.User, 'user_email')
def bcc_list_user(user_email):
    user_email = user_email or flask_login.current_user.email
    user = models.User.query.get(user_email) or flask.abort(404)
    return flask.render_template('bcc/list_user.html', user=user)


@ui.route('/bcc/create/user', methods=['GET', 'POST'], defaults={'user_email': None})
@ui.route('/bcc/create/user/<path:user_email>', methods=['GET', 'POST'])
@access.owner(models.User, 'user_email')
def bcc_create_user(user_email):
    user_email = user_email or flask_login.current_user.email
    user = models.User.query.get(user_email) or flask.abort(404)
    form = forms.BccForm(user_permissions='edit')
    aliases = [(alias, alias) for alias in user.get_aliases()]
    form.localpart.choices = aliases
    if form.validate_on_submit():
        email = form.localpart.data
        localpart = email.split("@")[0]
        if email in user.get_aliases():
            domain = models.Domain.query.get(email.split("@")[1]) or flask.abort(404)
            if not domain.has_email(localpart):
                flask.flash('Email adress to bcc for does not exist', 'error')
            else:
                bcc = models.Bcc(domain=domain)
                form.populate_obj(bcc)
                bcc.localpart = localpart
                bcc.domain = domain
                models.db.session.add(bcc)
                models.db.session.commit()
                flask.flash('Bcc %s created' % bcc)
                return flask.redirect(
                    flask.url_for('.bcc_list_user', user=user))
    return flask.render_template('bcc/create_user.html',
        form=form, user=user)


@ui.route('/bcc/edit/user/<bcc_id>', methods=['GET', 'POST'], defaults={'user_email': None})
@ui.route('/bcc/edit/user/<path:user_email>/<bcc_id>', methods=['GET', 'POST'])
@access.bcc_owner
def bcc_edit_user(user_email, bcc_id):
    user_email = user_email or flask_login.current_user.email
    user = models.User.query.get(user_email) or flask.abort(404)
    bcc = models.Bcc.query.get(bcc_id) or flask.abort(404)
    form = forms.BccForm(obj=bcc, user_permissions='edit')
    aliases = [(alias, alias) for alias in user.get_aliases()]
    form.localpart.choices = aliases
    if form.validate_on_submit():
        email = form.localpart.data
        localpart = email.split("@")[0]
        domain = models.Domain.query.get(email.split("@")[1]) or flask.abort(404)
        form.populate_obj(bcc)
        bcc.localpart = localpart
        bcc.domain = domain
        models.db.session.commit()
        flask.flash('Bcc address configuration updated')
        return flask.redirect(
            flask.url_for('.bcc_list_user', user=user))
    form.localpart.data = f'{bcc.localpart}@{bcc.domain_name}'
    return flask.render_template('bcc/edit_user.html',
        form=form, user=user)


@ui.route('/bcc/delete/user/<bcc_id>', methods=['GET', 'POST'], defaults={'user_email': None})
@ui.route('/bcc/delete/user/<path:user_email>/<bcc_id>', methods=['GET', 'POST'])
@access.bcc_owner
def bcc_delete_user(user_email, bcc_id):
    user_email = user_email or flask_login.current_user.email
    user = models.User.query.get(user_email) or flask.abort(404)
    bcc = models.Bcc.query.get(bcc_id) or flask.abort(404)
    domain = bcc.domain
    models.db.session.delete(bcc)
    models.db.session.commit()
    flask.flash('Bcc %s deleted' % bcc)
    return flask.redirect(
        flask.url_for('.bcc_list_user', user=user))


@ui.route('/bcc/list/domain/<domain_name>', methods=['GET'])
@access.domain_admin(models.Domain, 'domain_name')
def bcc_list(domain_name):
    domain = models.Domain.query.get(domain_name) or flask.abort(404)
    return flask.render_template('bcc/list.html', domain=domain)


@ui.route('/bcc/create/domain/<domain_name>', methods=['GET', 'POST'])
@access.domain_admin(models.Domain, 'domain_name')
def bcc_create(domain_name):
    domain = models.Domain.query.get(domain_name) or flask.abort(404)
    form = forms.BccForm()
    users = [(user.localpart, user.email) for user in domain.users]
    aliases = [(alias.localpart, alias.email) for alias in domain.aliases]
    form.localpart.choices = users + aliases
    if form.validate_on_submit():
        if not domain.has_email(form.localpart.data):
            flask.flash('Email adress to bcc for does not exist', 'error')
        else:
            bcc = models.Bcc(domain=domain)
            form.populate_obj(bcc)
            models.db.session.add(bcc)
            models.db.session.commit()
            flask.flash('Bcc %s created' % bcc)
            return flask.redirect(
                flask.url_for('.bcc_list', domain_name=domain.name))
    return flask.render_template('bcc/create.html',
        domain=domain, form=form)


@ui.route('/bcc/edit/domain/<bcc_id>', methods=['GET', 'POST'])
@access.bcc_owner
def bcc_edit(bcc_id):
    bcc = models.Bcc.query.get(bcc_id) or flask.abort(404)
    domain = bcc.domain
    form = forms.BccForm(obj=bcc)
    users = [(user.localpart, user.email) for user in domain.users]
    aliases = [(alias.localpart, alias.email) for alias in domain.aliases]
    form.localpart.choices = users + aliases
    if form.validate_on_submit():
        form.populate_obj(bcc)
        models.db.session.commit()
        flask.flash('Bcc address configuration updated')
        return flask.redirect(
            flask.url_for('.bcc_list', domain_name=domain.name))
    return flask.render_template('bcc/edit.html',
        form=form, bcc=bcc)

    
@ui.route('/bcc/delete/domain/<bcc_id>', methods=['GET', 'POST'])
@access.bcc_owner
@access.confirmation_required("Delete a bcc address")
def bcc_delete(bcc_id):
    bcc = models.Bcc.query.get(bcc_id) or flask.abort(404)
    domain = bcc.domain
    models.db.session.delete(bcc)
    models.db.session.commit()
    flask.flash('Bcc %s deleted' % bcc)
    return flask.redirect(
        flask.url_for('.bcc_list', domain_name=domain.name))
