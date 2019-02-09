from flask import render_template, flash, redirect, url_for, request
from app import db
from app.main.forms import EditProfileForm, CreateKPI, CreateAreaForm, \
    CreateShift, AssignAreaForm
from flask_login import current_user, login_required
from app.models import User, Area, KPI, Shift
from app.main import bp
from functions.dates import Week, date_from_string
from functions.text import convert_text_area_to_list as conv
import datetime

tempdir = 'main/'


@bp.route('/')
@bp.route('/index')
@login_required
def index():
    text = "Here is a snapshot of the areas you have been assigned:"
    areas = current_user.areas.order_by(Area.name.asc()).all()
    return render_template(tempdir + 'index.html', title='Home', areas=areas, text=text)


@bp.route('/user/<username>', methods=['GET', 'POST'])
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    all_areas = Area.query.all()
    area_string = ', '.join([a.name for a in all_areas])
    user_areas = user.areas.all()
    area_form = AssignAreaForm()
    if area_form.validate_on_submit():
        areas = conv(area_form.areas.data)
        for area in all_areas:
            user.rm_area(area)
        db.session.commit()
        for area in areas:
            a = Area.query.filter_by(name=area.capitalize()).first()
            if a in all_areas:
                user.add_area(a)
        db.session.commit()
        return redirect(url_for('main.user', username=username))
    elif request.method == 'GET':
        area_form.areas.data = ', '.join([a.name for a in user_areas])
    return render_template(tempdir + 'user.html', user=user, user_areas=user_areas, area_string=area_string,
                           all_areas=all_areas, area_form=area_form)


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
    return redirect(url_for('main.area_date',
                            area_name=area_name, date=datetime.date.today()))


@bp.route('/create_area', methods=['GET', 'POST'])
@login_required
def create_area():
    form = CreateAreaForm()
    if form.validate_on_submit():
        area = Area(name=form.name.data.capitalize())
        db.session.add(area)
        db.session.commit()
        flash('Area {} added'.format(area.name))
        return redirect(url_for('main.create_area'))
    return render_template(tempdir + 'create_area.html', title='Create New Area', form=form)


@bp.route('/area/<area_name>/<date>')
@login_required
def area_date(area_name, date):
    week = Week(date=date_from_string(date))
    if area_name != 'all':
        area = Area.query.filter_by(name=area_name).first_or_404()
        return render_template(tempdir + 'area.html', area=area, week=week, KPI=KPI, user=current_user)
    else:
        areas = Area.query.order_by(Area.name.asc()).all()
        return render_template(tempdir + 'area_browse.html', areas=areas, week=week, user=current_user)


@bp.route('/area/<area_name>/edit/kpi/<shift>/<date>', methods=['GET', 'POST'])
@login_required
def create_kpi(area_name, shift, date):
    form = CreateKPI(current_user)
    form.shift.choices = [(s.name, s.name) for s in Shift.query.all()]
    if form.validate_on_submit():
        d = form.date.data
        demand = form.demand.data
        pct = form.pct.data
        area = form.area.data
        shift = form.shift.data
        user = current_user
        k = KPI(d=d, demand=demand, plan_cycle_time=pct)
        k.add_area(area)
        k.add_user(user)
        k.add_shift(shift)
        db.session.add(k)
        db.session.commit()
        flash('Your changes have been saved')
        return redirect(url_for('main.area', area_name=form.area.data))
    elif request.method == 'GET':
        id_area = Area.query.filter_by(name=area_name).first().id
        id_shift = Shift.query.filter_by(name=shift).first().id
        d = date_from_string(date)
        kpi = KPI.query.filter_by(id_area=id_area, id_shift=id_shift, d=d).first()
        if kpi:
            form.demand.data = kpi.demand
            form.pct.data = kpi.plan_cycle_time
        form.area.data = area_name
        form.shift.data = shift
        form.date.data = d
    return render_template(tempdir + 'create_kpi.html', form=form)


@bp.route('/area/<area_name>/create/shift', methods=['GET', 'POST'])
@login_required
def create_shift(area_name):
    a = Area.query.filter_by(name=area_name).first_or_404()
    form = CreateShift(area_name, current_user)
    if form.validate_on_submit():
        name = form.name.data
        start = form.start.data
        end = form.end.data
        s = Shift(name=name, start=start, end=end)
        db.session.add(s)
        s.add_area(a)
        db.session.commit()
        flash('You shift has been added')
        return redirect(url_for('main.area', area_name=area_name))
    return render_template(tempdir + 'create_shift.html', form=form)
