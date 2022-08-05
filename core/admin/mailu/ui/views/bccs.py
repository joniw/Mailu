from mailu import models
from mailu.ui import ui, forms, access

import flask


@ui.route('/bcc/list/<domain_name>', methods=['GET'])
@access.domain_admin(models.Domain, 'domain_name')
def bcc_list(domain_name):
    domain = models.Domain.query.get(domain_name) or flask.abort(404)
    return flask.render_template('bcc/list.html', domain=domain)


@ui.route('/bcc/create/<domain_name>', methods=['GET', 'POST'])
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


@ui.route('/bcc/edit/<bcc_id>', methods=['GET', 'POST'])
@access.domain_admin(models.Bcc, 'bcc_id')
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

    
@ui.route('/bcc/delete/<bcc_id>', methods=['GET', 'POST'])
@access.domain_admin(models.Bcc, 'bcc_id')
@access.confirmation_required("Delete a bcc address")
def bcc_delete(bcc_id):
    bcc = models.Bcc.query.get(bcc_id) or flask.abort(404)
    domain = bcc.domain
    models.db.session.delete(bcc)
    models.db.session.commit()
    flask.flash('Bcc %s deleted' % bcc)
    return flask.redirect(
        flask.url_for('.bcc_list', domain_name=domain.name))
