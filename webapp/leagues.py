import webapp.league_calcs as league_calcs
from random import randint
from webapp import db
from webapp.models import LeagueGameweek


class FF500League(object):
	def __init__(self, league):
		self.league = league
		self.status = league.status
		self.members = []
		self.leaderboard = []
		self.gameweeks = {}
		self.graph = []
		self.monthly_standings = {}
		self.trivia = {}
		
		self.addMembers()
	
		if self.league.status == 'starting':
			self.addLeagueGameweeks()
			self.buildMonthlyStandings()
			self.addMonthlyFines()
		else:
			self.buildMonthlyStandings()
		self.buildLeaderboard() 
		self.createGraph()
		self.createTrivia()
		

	def leagueDataJson(self):
		"""returns league data to the view in nice easy to parse json"""
		data = {
		'league_name': self.league.league_name,
		'status': self.status,
		'members': [],
		'leaderboard': self.leaderboard,
		'gameweeks': self.gameweeks,
		'graph' : self.graph,
		'monthly_standings': {},
		'trivia': {}
		}
		for i in self.members:
			data['members'].append(i.username)
		for i in data['gameweeks']:
			for j in data['gameweeks'][i]:
				j['player'] = j['player'].username
		for i in self.monthly_standings:
			data['monthly_standings'][i] = []
			for j in self.monthly_standings[i]['leaderboard']:
				data['monthly_standings'][i].append({j[0].username: j[1]})
		for i in self.trivia:
			data['trivia'][i.username] = self.trivia[i]
		return data

	def createTrivia(self):
		data = {}
		for member in self.members:
			data[member] = {
			'wins': 0,
			'points': 0,
			'negatives': 0,
			'losses': 0,
			'motms': 0,
			'bottom_two': 0
			}
		for gameweek in self.gameweeks:
			for i in self.gameweeks[gameweek]:
				player = i['player']
				if i['league_points'] == 3:
					data[player]['wins'] += 1 
				if i['league_points'] > 0:
					data[player]['points'] += 1
				if i['league_points'] < 0:
					data[player]['negatives'] += 1
				if i['league_points'] == -2:
					data[player]['losses'] += 1
		for i in self.members:
			for j in self.monthly_standings:
				if i == self.monthly_standings[j]['winner']:
					data[i]['motms'] += 1
				if i in self.monthly_standings[j]['losers']:
					data[i]['bottom_two'] += 1
		for i in data:
			data[i]['win_percentage'] = round(data[i]['wins'] / len(self.gameweeks) * 100)
			data[i]['loss_percentage'] = round(data[i]['losses'] / len(self.gameweeks) * 100)
		self.trivia = data


			


	def createGraph(self):
		data = []
		for i in self.members:
			x = "rgba(220,220,220,1)"
			v1 = str(randint(1,220))
			v2 = str(randint(1,220))
			v3 = str(randint(1,220))
			colour = f"rgba({v1},{v2},{v3},0.4)"
			data.append({'player': i.username, 'running_scores': [], 'gameweeks': [], 'colour': colour})
		for i in self.gameweeks:
			data[0]['gameweeks'].append(i)
			for j in data:
				for k in self.gameweeks[i]:
					if j['player'] == k['player'].username:
						j['running_scores'].append(k['running_league_points'])
		self.graph = data

	def buildMonthlyStandings(self):
		self.monthly_standings = league_calcs.monthlyStandings(self.league)
		for i in self.monthly_standings:
			self.monthly_standings[i]['winner'] = self.monthly_standings[i]['leaderboard'][0][0]
			for j in self.monthly_standings[i]['leaderboard'][-2:]:
				self.monthly_standings[i]['losers'].append(j[0])


	def addMonthlyFines(self):
		for i in self.monthly_standings:
			print(i)
			if i not in ['March', 'April','May']:
				losers = self.monthly_standings[i]['losers']
				for j in league_calcs.fpl_phases:
					if i == j['name']:
						for loser in losers:
							lgw = LeagueGameweek.query.filter_by(user=loser, fpl_event=j['stop_event']).first()
							lgw.fines += 25
							lgw.notes += ' finished in bottom 2'
			db.session.commit()


	def addMembers(self):
		memberships = self.league.members
		for i in memberships:
			self.members.append(i.entrant)

	def addLeagueGameweeks(self):
		league_calcs.ff350_calc(self.league)		

	def buildLeaderboard(self):
		overall_standings = []
		overall_fpl_points = {}
		overall_league_points = {}
		overall_fines = {}
		gameweeks = {}
		for i in self.league.league_gameweeks:
			gameweeks[i.fpl_event] = []
		for i in self.members:
			overall_fpl_points[i] = 0
			overall_league_points[i] = 0
			overall_fines[i] = 0
			running_league_points = 0
			for j in i.league_gameweeks:
				overall_fpl_points[i] += j.fpl_points
				overall_league_points[i] += j.championship_points
				overall_fines[i] += j.fines
				running_league_points += j.championship_points
				gameweeks[j.fpl_event].append({
					'player': j.user,
					'fpl_points': j.fpl_points,
					'league_points': j.championship_points,
					'running_league_points': running_league_points,
					'fines': j.fines,
					'notes': j.notes
					})
		for i in gameweeks:
			newlist = sorted(gameweeks[i], key=lambda k: k['fpl_points'], reverse=True)
			gameweeks[i] = newlist
		for i in overall_fpl_points:
			overall_standings.append({'player': i.username, 'fpl_points': overall_fpl_points[i], 'P & L': '+£69'})
		for i in overall_league_points:
			for j in overall_standings:
				if j['player'] == i.username:
					j['league_points'] = overall_league_points[i]
		for i in overall_fines:
			for j in overall_standings:
				if j['player'] == i.username:
					j['fines'] = overall_fines[i]
		sorted_overall = sorted(overall_standings, key=lambda k: k['league_points'], reverse=True)
		self.leaderboard = sorted_overall
		self.gameweeks = gameweeks

	def __repr__(self):
		return "<FFLobject>"
