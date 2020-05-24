from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, BooleanField, SubmitField, 
    TextAreaField, StringField, FloatField, SelectField, IntegerField)
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
from webapp.models import User
from webapp.api_calls import getTeamDetails
import string
import random

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    fpl_id = StringField('FPL ID', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_fpl_id(self, fpl_id):
        team_data = getTeamDetails(fpl_id.data)
        if team_data == "{'detail': 'Not found.'}":
            raise ValidationError('Team not found, please try a different FPL ID')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')

class CreateLeagueForm(FlaskForm):
    league_name = StringField('League Name', validators=[DataRequired()])
    entry_fee = FloatField('Entry Fee', validators=[DataRequired()])
    max_entrants = IntegerField('Maximum Entrants', validators=[DataRequired()])
    submit = SubmitField('Submit')

    def create_code(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(10))


class JoinLeagueForm(FlaskForm):
    code = StringField('Enter Your Code', validators=[DataRequired()])
    submit = SubmitField('Submit')


