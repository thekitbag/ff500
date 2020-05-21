from flask import render_template, redirect, flash, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime, timedelta
from webapp import app, db
from webapp.forms import (LoginForm, RegistrationForm, EditProfileForm, CreateLeagueForm,
                 JoinLeagueForm)
from webapp.models import User, League, Membership, FPL_Gameweek
import webapp.api_calls as api_calls
import webapp.league_calcs as league_calcs
from webapp.leagues import FF500League

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/')
@app.route('/index')
def index():
    data = {}
    current_week = api_calls.getCurrentWeekDetails()
    week_id = current_week['id']
    next_deadline = current_week['deadline_time'][:-1]
    deadline = datetime.strptime(next_deadline, '%Y-%m-%dT%H:%M:%S')
    draft_deadline = deadline - timedelta(days=1)
    data['deadline'] = deadline
    data['draft deadline'] = draft_deadline
    if current_user.is_authenticated:
        team_history = api_calls.getTeamDetails(current_user.fpl_id)
        current_week_details = team_history['current'][week_id-2]
        team = api_calls.getPicks(current_user.fpl_id, week_id-2)
        score = team['points']
        data['team'] = team['team']
        data['score'] = score
    return render_template('index.html', title='Home', data=data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', form=form)
    else:
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user is None or not user.check_password(form.password.data):
                flash('Invalid username or password')
                return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))
        
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, fpl_id=form.fpl_id.data)
        user.set_password(form.password.data)
        user.getHistory()
        user.getPicksHistory()
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    #duplication of this code on index - turn in to separate function and reuse
    current_week = api_calls.getNextWeekDetails()
    week_id = current_week['id']
    data = {}
    user = User.query.filter_by(username=username).first_or_404()
    team_history = api_calls.getTeamDetails(user.fpl_id)
    current_week_details = team_history['current'][week_id-2]
    team = api_calls.getPicks(user.fpl_id, week_id-2)
    score = team['points']
    data['team'] = team['team']
    data['score'] = score
    return render_template('user.html', user=user, data=data)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)

@app.route('/history')
@login_required
def history():
    league_name = 'ff500'
    league = League.query.filter_by(league_name=league_name).first_or_404()
    a = FF500League(league)
    league_data = a.leagueDataJson()
    return render_template('history.html', league_data=league_data)

@app.route('/live')
@login_required
def live():
    return render_template('live.html')

@app.route('/create_league', methods=['GET', 'POST'])
@login_required
def create_league():
    form = CreateLeagueForm()
    code = form.create_code()
    if form.validate_on_submit():
        league = League(league_name=form.league_name.data, entry_fee=form.entry_fee.data, 
                        payout_rules='ff350', entrants=7, entry_code=code, status='registering')
        db.session.add(league)
        current_user.joinLeague(league)
        message = f"Congratulations, you have created league: {league.league_name}! Give code: {code} \
         to anyone who wants to join!"
        flash(message)
        return redirect(url_for('index'))
    return render_template('create_league.html', form=form)

@app.route('/join_league', methods=['GET', 'POST'])
@login_required
def join_league():
    form = JoinLeagueForm()
    if form.validate_on_submit():
        league = League.query.filter_by(entry_code=form.code.data).first()
        if league is None:
            message = "No league with this code exists"
            flash(message)
            return redirect(url_for('join_league'))
        else: current_user.joinLeague(league)
        if len(league.members) == league.entrants:
            league.status = 'starting'
        db.session.commit()
        message = f"Success! You have joined league {league.league_name}"
        flash(message)
        return redirect(url_for('index'))
    return render_template('join_league.html', form=form)


