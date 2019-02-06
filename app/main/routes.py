from flask import render_template, flash, redirect, url_for, request
from app import db
from app.main.forms import EditProfileForm
from flask_login import current_user, login_required
from app.models import User
from app.main import bp
tempdir = 'main/'


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    text = "This is the landing site for AndonResponse.com"
    areas = current_user.areas.all()
    return render_template(tempdir + 'index.html', title='Home', areas=areas, text=text)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template(tempdir + 'user.html', user=user, posts=posts)


@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template(tempdir + 'edit_profile.html', title='Edit Profile', form=form)
