from datetime import datetime
from webapp import db, login
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from hashlib import md5
import webapp.api_calls as api_calls


class User(UserMixin, db.Model):
	__tablename__ = 'user'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	password_hash = db.Column(db.String(128))
	fpl_id = db.Column(db.Integer)
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime, default=datetime.utcnow)
	memberships = db.relationship("Membership", back_populates="entrant")
	picks = db.relationship("GameweekPick", back_populates="user")
	fpl_gameweeks = db.relationship("FPL_Gameweek", back_populates="user")
	league_gameweeks = db.relationship("LeagueGameweek", back_populates="user")
	
	def set_password(self, password):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password):
		return check_password_hash(self.password_hash, password)

	def avatar(self, size):
		digest = md5(self.email.lower().encode('utf-8')).hexdigest()
		return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
			digest, size)

	def joinLeague(self, league):
		membership = Membership(entrant=self, league=league)
		db.session.add(membership)
		db.session.commit()

	def getHistory(self):
		 #gets a users fpl history and writes it in gameweeks to the DB
		history = api_calls.getTeamDetails(self.fpl_id)
		season = history['current']
		chips = history['chips']
		for week in season:
			gameweek = FPL_Gameweek(user=self, fpl_event=week['event'], fpl_points=week['points'] - week['event_transfers_cost'])
			db.session.add(gameweek)
			for i in chips:
				if i['event'] == week['event']:
					gameweek.chip = i['name']
		db.session.commit()

	def getPicksHistory(self):
		gameweeks = FPL_Gameweek.query.filter_by(user=self)
		picks = api_calls.getPicksHistory(gameweeks, self.fpl_id)
		for i in picks:
			autosubs = []
			for sub in i['autosubs']:
				autosubs.append(sub['element_in'])
			for j in i['picks']:
				player=Player.query.filter_by(element_id=j['element']).first()
				gwpk = GameweekPick(user=self, player=player, fpl_event=i['gameweek'], element_id=j['element'],\
								 	pick_number=j['position'], is_captain=j['is_captain'], is_vice_captain=j['is_vice_captain'])
				if j['element'] in autosubs:
					gwpk.auto_sub = 1
				else: gwpk.auto_sub = 0
				db.session.add(gwpk)
		db.session.commit()

	def __repr__(self):
		return '<User {}>'.format(self.username)

class League(db.Model):
	__tablename__ = 'league'
	league_id = db.Column(db.Integer, primary_key=True)
	league_name = db.Column(db.String(128))
	entry_fee = db.Column(db.Float)
	payout_rules = db.Column(db.String(128))
	entry_code = db.Column(db.String(128))
	entrants = db.Column(db.Integer)
	status = db.Column(db.String(128))
	members = db.relationship("Membership", back_populates="league")
	league_gameweeks = db.relationship("LeagueGameweek", back_populates="league")

	def __repr__(self):
		return '<League {}>'.format(self.league_id)

class Membership(db.Model):
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	league_id = db.Column(db.Integer, db.ForeignKey('league.league_id'), primary_key=True)

	entrant = db.relationship('User', back_populates='memberships')
	league = db.relationship('League', back_populates='members')

	def __repr__(self):
		return f'<member: {self.id} is in league {self.league_id}>'

class FPL_Gameweek(db.Model):
	__tablename__ = 'fpl_gameweek'
	fpl_gameweek_id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
	fpl_event = db.Column(db.Integer)
	fpl_points = db.Column(db.Integer)
	chip = db.Column(db.String(60))

	user = db.relationship('User', back_populates='fpl_gameweeks')
	

	def __repr__(self):
		return '<FPL Gameweek {}>'.format(self.gameweek_id)

class LeagueGameweek(db.Model):
	__tablename__ = 'league_gameweek'
	gameweek_id = db.Column(db.Integer, primary_key=True)
	id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
	fpl_event = db.Column(db.Integer)
	fpl_points = db.Column(db.Integer)
	league_id = db.Column(db.Integer, db.ForeignKey('league.league_id'), primary_key=True)
	championship_points = db.Column(db.Integer)
	month = db.Column(db.String(32))
	fines = db.Column(db.Integer)
	notes = db.Column(db.String(120))

	user = db.relationship('User', back_populates='league_gameweeks')
	league = db.relationship('League', back_populates='league_gameweeks')


	def __repr__(self):
		return f'<League Gameweek {self.gameweek_id}, {self.user}>'

class GameweekPick(db.Model):
	"""association object of users picking players in gameweeks"""
	gameweeks_pick_id = db.Column(db.Integer, primary_key=True)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
	element_id = db.Column(db.Integer, db.ForeignKey('player.element_id'))
	fpl_event = db.Column(db.Integer)
	pick_number = db.Column(db.Integer)
	is_captain = db.Column(db.Integer)
	is_vice_captain = db.Column(db.Integer)
	auto_sub = db.Column(db.Integer)

	user = db.relationship('User', back_populates='picks')
	player = db.relationship('Player', back_populates='picks')

	def __repr__(self):
		return f'<member {self.user_id} picked {self.element_id} in gameweek {self.fpl_event}>'


class GameweekPerformance(db.Model):
	gwpf_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	element_id = db.Column(db.Integer, db.ForeignKey('player.element_id'))
	player_name = db.Column(db.String(128))
	fpl_event = db.Column(db.Integer)
	minutes = db.Column(db.Integer)
	points = db.Column(db.Integer)
	red_cards = db.Column(db.Integer)

	player = db.relationship('Player', back_populates='gameweek_performances')



	def buildGameweekPerformanceTable():
		db_check = GameweekPerformance.query.first()
		if db_check:
			print('performance db check over')
		else:
			players = db.session.query(Player).all()
			for i in players:
				fpl_id = i.element_id
				name = i.name
				history = api_calls.getGameweekHistory(i)
				for week in history['history']:
					gameweek_id = week['round']
					points = week['total_points']
					minutes = week['minutes']
					red_card = week['red_cards']
					gwp = GameweekPerformance(element_id=i.element_id, player_name=name, fpl_event=gameweek_id, \
											points=points, minutes=minutes, red_cards=red_card)
					db.session.add(gwp)
			db.session.commit()


class Player(db.Model):
	__tablename__ = 'player'
	player_id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(128))
	position = db.Column(db.String(128))
	team = db.Column(db.String(128))
	element_id = db.Column(db.Integer)
	
	picks = db.relationship("GameweekPick", back_populates="player")
	gameweek_performances = db.relationship("GameweekPerformance", back_populates="player")

	def buildPlayerTable():
		db_check = Player.query.first()
		if db_check:
			print('player db check over')
		else:
			players = api_calls.getPlayers()
			for i in players:
				player = Player(name=i['name'], position=i['position'], team=i['team'], element_id=i['id'])
				db.session.add(player)
			db.session.commit()


	def __repr__(self):
		return f'<Player {self.name}>'


@login.user_loader
def load_user(id):
	return User.query.get(int(id))




