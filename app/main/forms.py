from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, TimeField, SelectField, TextAreaField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, ValidationError
from app.models import Area, Shift, User


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
    submit = SubmitField('Submit')

    def validate_name(self, name):
        if name.data in [a.name for a in Area.query.all()]:
            raise ValidationError('This area already exists')


class AssignAreaForm(FlaskForm):
    areas = TextAreaField("Assign Areas",
                          description='separate each area with a comma')
    submit = SubmitField('Submit')


class CreateKPI(FlaskForm):
    demand = IntegerField('Demand (good parts)', validators=[DataRequired()])
    pct = IntegerField('Planned Cycle Time (seconds)', validators=[DataRequired()])
    shift = SelectField('Shift', validators=[DataRequired()])
    date = DateField('Date (at end of shift)', validators=[DataRequired()])
    area = StringField('Area', validators=[DataRequired()])
    submit = SubmitField('Create')

    def __init__(self, user_name, *args, **kwargs):
        super(CreateKPI, self).__init__(*args, **kwargs)
        self.user = user_name

    def validate_area(self, area):
        a = Area.query.filter_by(name=area.data).first()
        if a not in self.user.areas:
            raise ValidationError('You are not assigned to this area')


class CreateShift(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    start = TimeField('Start Time', validators=[DataRequired()], format="%I:%M %p")
    end = TimeField('End Time', validators=[DataRequired()], format="%I:%M %p")
    submit = SubmitField('Submit')

    def __init__(self, area, user, *args, **kwargs):
        super(CreateShift, self).__init__(*args, **kwargs)
        self.area = area
        self.user = user

    def validate_name(self, name):
        names = [s.name for s in Shift.query.all()]
        if name.data in names:
            raise ValidationError('This shift already exists')
        a = Area.query.filter_by(name=self.area).first()
        if a not in self.user.areas:
            raise ValidationError('You are not assigned to this area')

    def validate_start(self, start):
        a = Area.query.filter_by(name=self.area).first()
        starts = [s.start for s in a.shifts.all()]
        ends = [s.end for s in a.shifts.all()]
        for i in range(len(starts)):
            if starts[i] < start.data < ends[i] or\
                    start.data < ends[i] < starts[i]:
                raise ValidationError('This schedule conflicts with other shift times')
        if self.start.data == self.end.data:
            raise ValidationError('These times are the same')

    def validate_end(self, end):
        a = Area.query.filter_by(name=self.area).first()
        starts = [s.start for s in a.shifts.all()]
        ends = [s.end for s in a.shifts.all()]
        for i in range(len(starts)):
            if starts[i] < end.data < ends[i] or\
                    end.data < ends[i] < starts[i]:
                raise ValidationError('This schedule conflicts with other shift times')
        if self.start.data == self.end.data:
            raise ValidationError('These times are the same')
