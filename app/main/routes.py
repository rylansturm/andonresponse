from flask import render_template, flash, redirect, url_for, request
from app import db
from app.main.forms import EditProfileForm, CreateKPI
from flask_login import current_user, login_required
from app.models import User, Area, KPI
from app.main import bp, dates

tempdir = 'main/'


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    text = "Here is a snapshot of the areas you have been assigned:"
    areas = current_user.areas.order_by(Area.name.asc()).all()
    return render_template(tempdir + 'index.html', title='Home', areas=areas, text=text)


@bp.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template(tempdir + 'user.html', user=user)


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


@bp.route('/area/<area_name>')
@login_required
def area(area_name):
    week = dates.this_week()
    if area_name != 'all':
        area = Area.query.filter_by(name=area_name).first_or_404()
        return render_template(tempdir + 'area.html', area=area)
    else:
        areas = Area.query.order_by(Area.name.asc()).all()
        return render_template(tempdir + 'area_browse.html', areas=areas)


@bp.route('/area/<area_name>/kpi/<id>', methods=['GET', 'POST'])
@login_required
def kpi(area_name, id):
    area = Area.query.filter_by(name=area_name).first_or_404()
    if id == 'add':
        form = CreateKPI(current_user)
        if form.validate_on_submit():
            d = form.date.data
            demand = form.demand.data
            pct = form.pct.data
            area = form.area.data
            user = current_user
            k = KPI(d=d, demand=demand, plan_cycle_time=pct)
            k.add_area(area)
            k.add_user(user)
            db.session.add(k)
            db.session.commit()
            flash('Your changes have been saved')
            return redirect(url_for('main.area', area_name=form.area.data))
        elif request.method == 'GET':
            form.area.data = area_name
        return render_template(tempdir + 'create_kpi.html', form=form)
