from flask import render_template, redirect, url_for, flash, session, abort, request, current_app
from flask_login import login_required, current_user

from . import main
from .. import db
from ..models import User, Role, Event, Permission
from .forms import EventForm, EditProfileForm, EditProfileAdminForm
from ..decorators import admin_required


@main.route('/', methods=['GET', 'POST'])
def index():
    form = EventForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        event = Event(
            body=form.body.data,
            author=current_user._get_current_object())
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('.index'))
    events = Event.query.order_by(Event.timestamp.desc()).all()
    page = request.args.get('page', 1, type=int)
    pagination = Event.query.order_by(Event.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_EVENTS_PER_PAGE'], error_out=False)
    events = pagination.items
    return render_template('index.html', form=form, events=events, pagination=pagination)


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    events = user.events.order_by(Event.timestamp.desc()).all()
    return render_template('user.html', user=user, events=events)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)


@main.route('/event/<int:id>')
def event(id):
    event = Event.query.get_or_404(id)
    return render_template('event.html', events=[event])


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    event = Event.query.get_or_404(id)
    if current_user != event.author and \
            not current_user.can(Permission.ADMIN):
        abort(403)
    form = EventForm()
    if form.validate_on_submit():
        event.body = form.body.data
        db.session.add(event)
        db.session.commit()
        flash('The event has been updated.')
        return redirect(url_for('.event', id=event.id))
    form.body.data = event.body
    return render_template('edit_event.html', form=form)
