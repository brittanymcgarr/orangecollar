from flask_wtf import Form
from wtforms import StringField, TextField, BooleanField, PasswordField, IntegerField, FileField
from wtforms.validators import DataRequired


class LoginForm(Form):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


class SignUpForm(Form):
    name = StringField('name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired()])
    primary_phone = StringField('primary_phone', validators=[DataRequired()])
    primary_address = StringField('primary_address')
    secondary_phone = StringField('secondary_phone')
    allow_sms = BooleanField('allow_sms', default=True)
    allow_mms = BooleanField('allow_mms', default=True)
    allow_voice = BooleanField('allow_voice', default=False)
    pet_watch = BooleanField('pet_watch', default=False)
    

class EditForm(Form):
    name = StringField('name')
    password = PasswordField('password', validators=[DataRequired()])
    confirm_password = PasswordField('confirm_password', validators=[DataRequired()])
    primary_phone = StringField('primary_phone')
    secondary_phone = StringField('secondary_phone')
    primary_address = StringField('primary_address')
    secondary_address = StringField('secondary_address')
    allow_mms = BooleanField('allow_mms', default=True)
    allow_sms = BooleanField('allow_sms', default=True)
    allow_voice = BooleanField('allow_voice', default=True)
    pet_watch = BooleanField('pet_watch', default=False)
    

class ContactForm(Form):
    pet_id = StringField('pet_id')
    
    
class LocationForm(Form):
    address = StringField('address')
    

class NewPetForm(Form):
    name = StringField('name')
    species = StringField('species', validators=[DataRequired()])
    color = StringField('color')
    breed = StringField('breed')
    gender = StringField('gender')
    description = TextField('description')
    indoor_pet = BooleanField('indoor_pet', default=True)
    status = StringField('status', validators=[DataRequired()])
    home_address = StringField('home_address')


class ImageForm(Form):
    file = FileField('file')
