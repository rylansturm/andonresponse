from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, IntegerField
from wtforms.validators import DataRequired, ValidationError
from app.models import User, Area
import datetime


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


class CreateKPI(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    demand = IntegerField('Demand', validators=[DataRequired()])
    pct = IntegerField('Planned Cycle Time', validators=[DataRequired()])
    area = StringField('Area', validators=[DataRequired()])
    submit = SubmitField('Create')

    def __init__(self, user_name, *args, **kwargs):
        super(CreateKPI, self).__init__(*args, **kwargs)
        self.user = user_name

    def validate_area(self, user):
        a = Area.query.filter_by(name=self.area.data).first()
        if a not in self.user.areas:
            raise ValidationError('You are not assigned to this area')
