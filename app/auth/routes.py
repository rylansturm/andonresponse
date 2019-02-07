from flask import render_template, flash, redirect, url_for, request
from app import db
from app.auth.forms import LoginForm, RegistrationForm,\
    ResetPasswordForm, ResetPasswordRequestForm, RequestLoginForm
from flask_login import current_user, login_user, logout_user
from app.models import User
from werkzeug.urls import url_parse
from app.auth.email import send_password_reset_email, send_login_info_request
from app.auth import bp
tempdir = 'auth/'


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template(tempdir + 'login.html', title='Sign In', form=form)


@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('auth.login'))
    return render_template(tempdir + 'register.html', title='Register', form=form)


@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('auth.login'))
    return render_template(tempdir + 'reset_password_request.html',
                           title='Reset Password', form=form)


@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        flash("You attempted to reset your password, but you are already logged in. If you have forgotten your"
              "password, please log out and click 'Click to Reset It'")
        return redirect(url_for('main.index'))
    user = User.verify_reset_password_token(token)
    if not user:
        flash("The token provided either does not match or has expired")
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template(tempdir + 'reset_password.html', form=form)


@bp.route('/request_login', methods=['GET', 'POST'])
def request_login():
    if current_user.is_authenticated:
        flash("You attempted to visit the 'Request Login' page, but you are already a registered user")
        return redirect(url_for('main.index'))
    form = RequestLoginForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        send_login_info_request(name, email)
        flash('Once approved by an admin, an email will be sent to you with your login info')
        return redirect(url_for('auth.login'))
    return render_template(tempdir + 'login_credential_request.html', title='Login Request', form=form)
