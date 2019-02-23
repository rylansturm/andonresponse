from flask import render_template, flash, redirect, url_for, request
from app import db
from app.main.forms import EditProfileForm, CreateKPIForm, CreateAreaForm, \
    CreateShiftForm, AssignAreaForm, AssignShiftForm, CreateScheduleForm
from flask_login import current_user, login_required
from app.models import User, Area, KPI, Shift, Schedule, Cycle, Andon
from app.main import bp
from functions.dates import Week, date_from_string, string_from_time as sft
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
    all_areas = Area.query.order_by(Area.name.asc()).all()
    all_shifts = Shift.query.all()
    area_string = ', '.join([a.name for a in all_areas])
    shift_string = ', '.join([s.name for s in all_shifts])
    user_areas = user.areas.order_by(Area.name.asc()).all()
    user_shifts = user.shifts.all()
    area_form = AssignAreaForm()
    shift_form = AssignShiftForm()
    if area_form.validate_on_submit() and area_form.submit1.data:
        areas = conv(area_form.items.data)
        for area in all_areas:
            user.rm_area(area)
        db.session.commit()
        for area in areas:
            a = Area.query.filter_by(name=area.capitalize()).first()
            if a in all_areas:
                user.add_area(a)
        db.session.commit()
        return redirect(url_for('main.user', username=username))
    elif shift_form.validate_on_submit() and shift_form.submit2.data:
        shifts = conv(shift_form.items.data)
        for shift in all_shifts:
            user.rm_shift(shift)
        db.session.commit()
        for shift in shifts:
            s = Shift.query.filter_by(name=shift.capitalize()).first()
            if s in all_shifts:
                user.add_shift(s)
        db.session.commit()
        return redirect(url_for('main.user', username=username))
    elif request.method == 'GET':
        area_form.items.data = ', '.join([a.name for a in user_areas])
        shift_form.items.data = ', '.join([s.name for s in user_shifts])
    return render_template(tempdir + 'user.html', title='User: ' + user.username, user=user, user_areas=user_areas,
                           area_string=area_string, all_areas=all_areas, area_form=area_form,
                           shift_form=shift_form, shift_string=shift_string)


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
    form = CreateAreaForm(original_name=None)
    all_shifts = Shift.query.all()
    if form.validate_on_submit():
        area = Area(name=form.name.data.capitalize())
        shifts = conv(form.shifts.data)
        db.session.add(area)
        for shift in shifts:
            if shift.capitalize() in [s.name for s in all_shifts]:
                area.add_shift(Shift.query.filter_by(name=shift.capitalize()).first())
        db.session.commit()
        flash('Area {} added'.format(area.name))
        return redirect(url_for('main.create_area'))
    elif request.method == 'GET':
        form.shifts.data = ', '.join([s.name for s in all_shifts])
    return render_template(tempdir + 'create_area.html', title='Create New Area', form=form)


@bp.route('/area/<area_name>/config', methods=['GET', 'POST'])
@login_required
def config_area(area_name):
    form = CreateAreaForm(original_name=area_name)
    area = Area.query.filter_by(name=area_name).first()
    all_shifts = Shift.query.all()
    if form.validate_on_submit():
        area.name = form.name.data
        shifts = conv(form.shifts.data)
        for shift in all_shifts:
            area.rm_shift(shift)
        db.session.commit()
        for shift in shifts:
            if shift.capitalize() in [s.name for s in all_shifts]:
                area.add_shift(Shift.query.filter_by(name=shift.capitalize()).first())
        db.session.commit()
        flash('Area {} configured'.format(area.name))
        return redirect(url_for('main.area', area_name=area.name))
    elif request.method == 'GET':
        form.name.data = area.name
        form.shifts.data = ', '.join(a.name for a in area.shifts.all())
    return render_template(tempdir + 'create_area.html', title='Configure Area:', form=form, area=area.name)


@bp.route('/area/<area_name>/<date>')
@login_required
def area_date(area_name, date):
    week = Week(date=date_from_string(date))
    if area_name != 'all':
        area = Area.query.filter_by(name=area_name).first_or_404()
        return render_template(tempdir + 'area.html', title=area_name + ' Overview', date=date, dfs=date_from_string,
                               area=area, week=week, KPI=KPI, user=current_user, datetime=datetime)
    else:
        areas = Area.query.order_by(Area.name.asc()).all()
        return render_template(tempdir + 'area_browse.html', title='All Areas',
                               areas=areas, week=week, user=current_user)


@bp.route('/area/<area_name>/schedules/<shift_name>/<schedule_name>', methods=['GET', 'POST'])
@login_required
def config_schedule(area_name, shift_name, schedule_name):
    area = Area.query.filter_by(name=area_name).first()
    shift = Shift.query.filter_by(name=shift_name).first()
    form = CreateScheduleForm(original_name=schedule_name, area=area, shift=shift)
    if form.validate_on_submit():
        s = Schedule.query.filter_by(name=schedule_name).first()
        if not s:
            s = Schedule(name=form.name.data)
            db.session.add(s)
            s.add_area(area)
            s.add_shift(shift)
        s.name = form.name.data
        s.make_times_list(start1=form.start1.data, start2=form.start2.data, start3=form.start3.data,
                          start4=form.start4.data, end1=form.end1.data, end2=form.end2.data,
                          end3=form.end3.data, end4=form.end4.data)
        db.session.commit()
        flash('Successfully added {} shift for {} {}'.format(form.name.data, area.name, shift.name))
        return redirect(url_for('main.area_schedules', area_name=area_name, shift_name=shift_name))
    elif request.method == 'GET':
        if schedule_name != 'new':
            s = Schedule.query.filter_by(name=schedule_name, id_area=area.id, id_shift=shift.id).first()
            if s:
                form.name.data = s.name
                form.start1.data = s.start1
                form.start2.data = s.start2
                form.start3.data = s.start3
                form.start4.data = s.start4
                form.end1.data = s.end1
                form.end2.data = s.end2
                form.end3.data = s.end3
                form.end4.data = s.end4
    return render_template(tempdir + 'config_schedule.html', title='Edit Schedule',
                           area=area, shift=shift, form=form)


@bp.route('/area/<area_name>/schedules/<shift_name>', methods=['GET', 'POST'])
@login_required
def area_schedules(area_name, shift_name):
    area = Area.query.filter_by(name=area_name).first()
    shift = Shift.query.filter_by(name=shift_name).first()
    schedules = Schedule.query.filter_by(schedule_area=area, schedule_shift=shift).all()
    return render_template(tempdir + 'area_schedules.html', title=area_name + ' ' + shift_name + ' Schedules',
                           area=area, shift=shift, schedules=schedules)


@bp.route('/kpi/<kpi_id>/popup', methods=['GET'])
@login_required
def kpi_popup(kpi_id):
    kpi = KPI.query.get(kpi_id)
    return render_template(tempdir + 'kpi_popup.html', kpi=kpi)


@bp.route('/kpi/<kpi_id>/overview', methods=['GET'])
@login_required
def kpi_overview(kpi_id):
    kpi = KPI.query.get(kpi_id)
    if not kpi.schedule:
        kpi.add_schedule('Regular')
        db.session.commit()
    t = kpi.get_time_elapsed(d=datetime.datetime.now())
    sequences = kpi.get_sequences()
    schedule = kpi.schedule.return_schedule(kpi_d=kpi.d) if kpi.schedule else []
    blocks = list(range(1, len(schedule)//2+1))
    return render_template(tempdir + 'kpi_overview.html', title='Shift Overview',
                           kpi=kpi, sequences=sequences, schedule=schedule, blocks=blocks, t=t,
                           datetime=datetime, Cycle=Cycle, Andon=Andon)


@bp.route('/kpi/<area_name>/<shift>/<date>/edit', methods=['GET', 'POST'])
@login_required
def create_kpi(area_name, shift, date):
    form = CreateKPIForm(current_user)
    a = Area.query.filter_by(name=area_name).first()
    s = Shift.query.filter_by(name=shift).first()
    form.shift.choices = [(s.name, s.name) for s in Shift.query.all()]
    form.schedule.choices = [(s.name, s.name) for s in Schedule.query.filter_by(id_area=a.id,
                                                                                id_shift=s.id).all()]
    if form.validate_on_submit():
        d = form.date.data
        demand = form.demand.data
        pct = form.pct.data
        area = form.area.data
        schedule = form.schedule.data
        shift = form.shift.data
        user = current_user
        k = KPI(d=d, demand=demand, plan_cycle_time=pct)
        k.add_area(area)
        k.add_user(user)
        k.add_shift(shift)
        k.add_schedule(schedule)
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
    return render_template(tempdir + 'create_kpi.html', title='Plan Shift',
                           form=form)


@bp.route('/create_shift', methods=['GET', 'POST'])
@login_required
def create_shift():
    form = CreateShiftForm()
    if form.validate_on_submit():
        name = form.name.data
        start = form.start.data
        end = form.end.data
        s = Shift(name=name, start=start, end=end)
        db.session.add(s)
        db.session.commit()
        flash('You shift has been added')
        return redirect(url_for('main.area', area_name='all'))
    return render_template(tempdir + 'create_shift.html', title='Create Shift',
                           form=form)
