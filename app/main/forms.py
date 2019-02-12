from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, TextAreaField
from wtforms.fields.html5 import DateField, TimeField
from wtforms.validators import DataRequired, ValidationError
from app.models import Area, Shift, User, Schedule


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


class CreateAreaForm(FlaskForm):
    name = StringField('Area Name', validators=[DataRequired()])
    shifts = TextAreaField('Shifts', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def __init__(self, original_name, *args, **kwargs):
        super(CreateAreaForm, self).__init__(*args, **kwargs)
        self.original_name = original_name

    def validate_name(self, name):
        if not self.original_name and name.data in [a.name for a in Area.query.all()]:
            raise ValidationError('This name already exists')


class AssignAreaForm(FlaskForm):
    items = TextAreaField(label='Assign Areas', description='separate each area with a comma')
    submit1 = SubmitField('Submit')


class AssignShiftForm(FlaskForm):
    items = TextAreaField(label='Assign Shifts', description='separate each area with a comma')
    submit2 = SubmitField('Submit')


class CreateKPIForm(FlaskForm):
    demand = IntegerField('Demand (good parts)', validators=[DataRequired()])
    pct = IntegerField('Planned Cycle Time (seconds)', validators=[DataRequired()])
    shift = SelectField('Shift', validators=[DataRequired()])
    date = DateField('Date (at end of shift)', validators=[DataRequired()])
    area = StringField('Area', validators=[DataRequired()])
    submit = SubmitField('Create')

    def __init__(self, user_name, *args, **kwargs):
        super(CreateKPIForm, self).__init__(*args, **kwargs)
        self.user = user_name

    def validate_area(self, area):
        a = Area.query.filter_by(name=area.data).first()
        if a not in self.user.areas:
            raise ValidationError('You are not assigned to this area')


class CreateShiftForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    start = TimeField('Start Time', validators=[DataRequired()])
    end = TimeField('End Time', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def validate_name(self, name):
        names = [s.name for s in Shift.query.all()]
        if name.data in names:
            raise ValidationError('This shift already exists')

    def validate_start(self, start):
        if start.data == self.end.data:
            raise ValidationError('These times are the same')

    def validate_end(self, end):
        if self.start.data == end.data:
            raise ValidationError('These times are the same')


class CreateScheduleForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    start1 = TimeField('First Block Start', validators=[DataRequired()])
    end1 = TimeField('First Block End', validators=[DataRequired()])
    start2 = TimeField('Second Block Start')
    end2 = TimeField('Second Block End')
    start3 = TimeField('Third Block Start')
    end3 = TimeField('Third Block End')
    start4 = TimeField('Fourth Block Start')
    end4 = TimeField('Fourth Block End')
    submit = SubmitField('Submit')

    def __init__(self, original_name, area, shift, *args, **kwargs):
        super(CreateScheduleForm, self).__init__(*args, **kwargs)
        self.original_name = original_name
        self.area = area
        self.shift = shift

    def validate_name(self, name):
        schedules = [s.name for s in Schedule.query.filter_by(id_area=self.area.id, id_shift=self.shift.id).all()]
        if name.data != self.original_name and name.data in schedules:
            raise ValidationError('This name exists for this team already')
        if len(name.data) > 24:
            raise ValidationError('Schedule name must be shorter than 24 characters')
