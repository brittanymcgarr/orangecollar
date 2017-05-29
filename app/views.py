import bcrypt
import os
import datetime

from flask_login import login_user, logout_user, current_user, login_required
from flask import (render_template, flash, redirect, session, url_for, 
                   request, g, abort, Response)
from werkzeug.utils import secure_filename

from app import app, db, lm
from .forms import LoginForm, SignUpForm, ContactForm, NewPetForm, EditForm, ImageForm
from .models import User, Pet

from twilio.rest import Client

# Get the g session
@app.before_request
def before_request():
    g.user = current_user

# Home
@app.route('/')
@app.route('/index')
def index():
    user = g.user
    
    if user is None:
        user = {'name': None}
    
    return render_template('index.html', title='', user=user)
    
# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        user = User.query.filter_by(email=form.email.data).first() or None
        
        if user is None:
            flash("You are not in our database. Check your email and password or sign up!")
            return redirect(url_for('login'))
        
        if user.password_hash == bcrypt.hashpw(form.password.data.encode('utf-8'), 
                                               user.password_hash.encode('utf-8')):
            
            if "remember_me" in session:
                remember_me = session['remember_me']
                session.pop('remember_me', None)
                        
            login_user(user, remember = remember_me)
            flash("Successfully Logged In. Welcome back, %s!" % g.user.name)
            return redirect(url_for('dashboard'))
        else:
            flash("Password was not valid. Try again or contact an admin.")
            return redirect(url_for('login'))
    
    return render_template('login.html', title='Sign In', form=form)
    
# Logout
@app.route('/logout')
def logout():
    logout_user()
    
    flash("Logged out")
    return redirect(url_for('index'))
    
# Load the user from the databse
@lm.user_loader
def user_loader(email):
    return User.query.filter_by(email=email).first() or None
    
# Sign Up new users
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignUpForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first() or None
        
        if user is not None:
            flash("That email already exists. Please sign in or contact an admin.")
            return redirect(url_for('login'))
            
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(form.password.data.encode('utf-8'), salt)
        
        user = User(name = form.name.data, 
                    email = form.email.data, 
                    password_hash = password_hash, 
                    primary_phone = form.primary_phone.data,
                    primary_address = form.primary_address.data,
                    allow_mms = form.allow_mms.data,
                    allow_sms = form.allow_sms.data,
                    allow_voice = form.allow_voice.data,
                    last_mms = datetime.datetime.now(),
                    last_sms = datetime.datetime.now(),
                    last_call = datetime.datetime.now())
                    
        db.session.add(user)
        db.session.commit()
        flash("Successfully created account. Welcome!")
    
        user.authenticated = True
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('signup.html', title='Sign Up', form=form)
    
# View the User Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    if g.user.is_authenticated:
        user = User.query.filter_by(email=g.user.email).first()
        pets = user.pets
        return render_template('dashboard.html', title="Dashboard",
                                user=user, pets=pets)
    else:
        flash("You need to be logged in to view your dashboard.")
        return render_template('dashboard.html', title="Dashboard",
                                user={"name":None}, pets=[])

# Edit a User Profile
@app.route('/edit', methods=['GET', 'POST'])
def edit():
    form = EditForm()
    user = User.query.get(g.user.id)
    
    if g.user.is_authenticated and user is not None:
        if form.validate_on_submit():
            form.populate_obj(user)
            db.session.add(user)
            db.session.commit()
        
            return redirect(url_for('dashboard'))
        
        return render_template('edit_user.html', title="Edit User", user=g.user, form=form)
    else:
        flash("You must be logged in to edit your profile")
        return redirect(url_for('login'))

# Create a Pet Profile for a User's Pet
@app.route('/new_user_pet', methods=['GET', 'POST'])
def new_user_pet():
    form = NewPetForm()
    
    if g.user is not None and g.user.is_authenticated:
        if form.validate_on_submit():
            pet = Pet(name = form.name.data,
                      species = form.species.data,
                      color = form.color.data,
                      breed = form.breed.data,
                      gender = form.gender.data,
                      description = form.description.data,
                      status = form.status.data,
                      home_address = form.home_address.data,
                      user_id = g.user.get_id())
            
            db.session.add(pet)
            current_user.pets.append(pet)
            db.session.commit()
            
            flash("Successfully registered your pet. Good Work!")
            return redirect(request.args.get('next') or url_for('dashboard'))
        
        return render_template('new_user_pet.html', title='Register Your Pet', form=form)
        
    else:
        flash("You need to be logged in to set your own pets or try Report a Sighted Pet")
        return redirect(url_for('index'))

# Upload an image for the pet
@app.route('/image-upload/<petID>', methods=['GET', 'POST'])
def image_upload(petID):
    if request.method == 'POST':
        form = ImageForm(request.form)
        
        if form.validate_on_submit():
            pet = Pet.query.get(petID) or None
            
            if pet is not None:
                image_file = request.files['file']
                filename = os.path.join(app.config['IMAGES_DIR'], secure_filename(image_file.filename))
                image_file.save(filename)
                pet.picture = image_file.filename
                
                db.session.add(pet)
                db.session.commit()
                
                flash('Saved %s' % os.path.basename(filename), 'success')
                return redirect(url_for('pet_profile', petID=pet.id))
        else:
            flash("Unable to locate the requested pet to upload file.")
            return redirect(url_for('dashboard'))
    else:
        form = ImageForm()

    return render_template('image_upload.html', title="Upload a Picture", petID=petID, form=form)

# Create a Pet Profile for a found Pet

# Edit a Pet Profile

# Delete a Pet Profile

# View a Pet Profile
@app.route('/pet_profile/<petID>', methods=['GET', 'POST'])
def pet_profile(petID):
    form = ContactForm()
    
    pet = Pet.query.get(petID) or None
    user = User.query.get(pet.user_id) or None
        
    if request.method == 'POST':
        reportPet(pet.id)
        return render_template('pet.html', title=pet.name, form=form, 
                                pet=pet, user=user)

    if pet is not None:
        return render_template('pet.html', title=pet.name, form=form, 
                                pet=pet, user=user)
    else:
        flash("Pet not found")
        return redirect(url_for('dashboard'))

# Find Pets in the area based on current position

# Find a Pet by Data

# Report a Pet Found
# Reporting a Pet forwards the listing and picture to the owner's email, sms
# mms, or phone through Twilio API
def reportPet(petID):
    pet = Pet.query.get(petID)
    user = User.query.get(pet.user_id)
    
    if user is not None:
        if user.primary_phone is not "":
            message = "Your %s, %s, was sighted in the area. Log in to Orange Collar to change your pet's status." % (pet.species, pet.name)
            
            #if user.allow_mms and pet.picture is not "":
            #    sendMMS(message, user.primary_phone, pet.picture)
            if user.allow_sms:
                sendSMS(message, user.primary_phone)
                
            if user.allow_voice:
                sendCall(pet, user, message, user.primary_phone)
            
            time = datetime.datetime.now()
            user.last_mms = time
            user.last_sms = time
            user.last_call = time
            db.session.commit()
            
            flash("The owner is being contacted. Thank you for doing your part!")
        else:
            flash("Could not find the owner\'s contact information. Thank you for trying.")
    else:
        flash("Could not find the owner. Thank you for trying to help.")

# Send SMS
def sendSMS(message="Your pet has been reported.", phone=""):
    if phone != "":
        account_sid = str(os.getenv('TWILIO_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        local_phone = str(os.getenv('OC_PHONE'))
        
        client = Client(account_sid, auth_token)
    
        client.messages.create(to = "+1%s" % phone,
                               from_ = local_phone,
                               body = message)

# Send MMS
def sendMMS(message="Your pet has been reported.", phone="", picture=""):
    pass

# Send Call
def sendCall(pet, user, message="Your pet has been reported.", phone=""):
    if phone != "":
        account_sid = str(os.getenv('TWILIO_SID'))
        auth_token = str(os.getenv('TWILIO_AUTH_TOKEN'))
        local_phone = str(os.getenv('OC_PHONE'))
        
        url = url_for('calltemplate', petID=pet.id)
        url = "http://orange-collar.herokuapp.com" + url

        client = Client(account_sid, auth_token)
        call = client.calls.create(to = "+1%s" % phone,
                                   from_ = local_phone,
                                   url = url)

# Create XML
@app.route('/calltemplate.xml/<petID>', methods=['GET', 'POST'])
def calltemplate(petID):
    pet = Pet.query.get(petID)
    user = User.query.get(pet.user_id)
    
    if pet is not None and user is not None:
        response_page = render_template('/calltemplate.xml', pet=pet, user=user)
        return Response(response_page, mimetype='text/xml')
    
# Check permissible file types
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']
