import webapp.api_calls as api_calls
from webapp.models import FPL_Gameweek, LeagueGameweek, User, Player, GameweekPerformance, GameweekPick, League
from webapp import db
import time

def ff350_calc(league):
	"""take a league in starting state and calculates leaguegameweeks from the FPL
	gameweeks of its entrants"""
	gameweeks = {}
	for i in league.members:
		for j in i.entrant.fpl_gameweeks:
			if j.fpl_event < 30:
				fines = calculateFines(j)
				month = calculateMonth(j)
				lgw = LeagueGameweek(league_id=league.league_id, fpl_event=j.fpl_event, user=j.user, \
									 fpl_points = j.fpl_points, fines=fines['fines'], notes=fines['reasons'], month=month)
				db.session.add(lgw)
				db.session.commit()
				if j.fpl_event not in gameweeks:
					gameweeks[j.fpl_event] = []
				gameweeks[j.fpl_event].append((j.user, j.fpl_points))
	for k in gameweeks.items():
		standings = {}
		week = k[0]
		scores = {}
		for key,val in k[1]:
			scores[key] = val
		champ_points = assignChampionshipPoints(scores)
		standings[week] = champ_points
		for wk, points in standings.items():
			print('point.items()', points.items())
			for i,j in points.items():
				league_gameweek = LeagueGameweek.query.filter_by(user=i, fpl_event=wk, league_id=league.league_id).first()
				league_gameweek.championship_points = j
				fpl_gw = FPL_Gameweek.query.filter_by(user=i, fpl_event=wk).first()
				if fpl_gw.chip:
					if j == -2:
						league_gameweek.fines += 20
						league_gameweek.notes += ' Played chip and came last'

	league.status = 'running'
	db.session.commit()

def createScoreTable(number_of_players):
	if number_of_players == 2:
		scores = [0,1]
	elif number_of_players == 3:
		scores = [-1,0,1]
	elif number_of_players == 4:
		scores = [-1,0,1,2]
	elif number_of_players == 5:
		scores = [-1,0,0,1,2]
	elif 11 > number_of_players > 5:
		scores = [-2,-1]
		for i in range(number_of_players - 5):
			scores.append(0)
		for i in range(1,4):
			scores.append(i)
	elif number_of_players > 10:
		scores = [-3,-2,-1]
		for i in range(number_of_players - 8):
			scores.append(0)
		for i in range(1,6):
			scores.append(i)
	return scores

def assignChampionshipPoints(scores):
	"""takes a scores dictionary and assigns points"""
	number_of_players = len(scores)
	score_points = createScoreTable(number_of_players)
	champ_points = {}
	sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
	res = []
	prev = None
	for i,(k,v) in enumerate(sorted_scores):
		if v!=prev:
			place,prev = i+1,v
		res.append((k,place))
	positions = []
	for i in range(number_of_players):
		positions.append([])
	for tup in res:
		positions[tup[1]-1].append(tup[0])
	for lst in positions:
		pool = 0
		if len(lst) > 0:
			for j in range(len(lst)):			
				score = score_points.pop()
				pool += score
				points = pool/len(lst)
			for person in lst:
				champ_points[person] = points
	return champ_points


def getSelections(user, fpl_gameweek):
	gameweek_data = db.session.query(GameweekPick, GameweekPerformance
		).filter(GameweekPick.fpl_event == GameweekPerformance.fpl_event).filter(
		GameweekPick.element_id == GameweekPerformance.element_id).filter(
		GameweekPick.user == user).filter(
		GameweekPick.fpl_event == fpl_gameweek.fpl_event).all()
	return gameweek_data

def calculateFines(fpl_gameweek):
	fines = 0
	reasons = []
	user = fpl_gameweek.user
	selections = getSelections(user, fpl_gameweek)
	red_card_check = redCard(selections)
	if red_card_check['red_cards'] > 0:
		fines += 20
		reasons.append('red card: ' + red_card_check['players'][0])
	benchees = benchPlayerPoints(selections)
	for i in benchees:
		fines += 20
		reasons.append(f"{i['name']} got {i['points']} points on the bench")
	if captain_and_vice_no_mins(selections) == True:
		fines += 20
		reasons.append("Captain and VC didn't play")
	if tripleCaptainFail(selections) == True:
		fines += 20
		reasons.append("Triple Captain Fail")
	if elevenPlayersFail(selections) == True:
		fines += 20
		reasons.append("Couldn't field 11 players")

	joined_reasons = " ".join(reasons)
	return {'fines': fines, 'reasons': joined_reasons}


def redCard(selections):
	red_cards = 0
	players = []
	for i in selections:
		if i[0].pick_number < 12  and i[1].red_cards > 0:
			red_cards += 1
			players.append(i[1].player_name)
	return {'red_cards': red_cards, 'players': players}

def benchPlayerPoints(selections):
	benchees = []
	for i in selections:
		if i[0].pick_number > 11 and i[1].points > 9.5:
			benchees.append({'name': i[1].player_name , 'points':i[1].points})
	return benchees

def captain_and_vice_no_mins(selections):
	captain = True
	vc = True
	for i in selections:
		if i[0].is_captain == 1 and i[1].minutes > 0:
			captain = False
		if i[0].is_vice_captain == 1 and i[1].minutes > 0:
			vc = False
	if captain == True and vc == True:
		return True
	else: return False

def tripleCaptainFail(selections):
	fail = False
	captain_points = 0
	if selections != []:
		gameweek = selections[0][0].fpl_event
		user = selections[0][0].user
		fpl_gameweek = FPL_Gameweek.query.filter_by(user=user, fpl_event=gameweek).first()
		if fpl_gameweek.chip == '3xc':
			for i in selections:
				if i[0].is_captain == 1:
					captain_points += i[1].points
			if captain_points < 3:
				fail = True
	return fail

def elevenPlayersFail(selections):
	fail = False
	players = set()
	for i in selections:
		if i[0].pick_number < 12 and i[1].minutes > 0:
			players.add(i[1].element_id)
	if len(players) < 11:
		fail = True
	return fail

def calculateMonth(fpl_gameweek):
	for i in fpl_phases:
		if fpl_gameweek.fpl_event >= i['start_event'] and fpl_gameweek.fpl_event <= i['stop_event']:
			return i['name']

def monthlyStandings(league):
	data = {}
	for i in fpl_phases:
		data[i['name']] = {
		'leaderboard': {},
		'gameweeks': [],
		'losers': []
		}
	for member in league.members:
		for i in data:
			data[i]['leaderboard'][member.entrant] = 0
	for gw in league.league_gameweeks:
		data[gw.month]['gameweeks'].append(gw)
	for mnth in data:
		for mgw in data[mnth]['gameweeks']:
			data[mnth]['leaderboard'][mgw.user] += mgw.fpl_points
	for i in data:
		 leaderboard = sorted(data[i]['leaderboard'].items(), key=lambda x: x[1], reverse=True)
		 data[i]['leaderboard'] = leaderboard
	return data




fpl_phases = [
      
      {
         "id":2,
         "name":"August",
         "start_event":1,
         "stop_event":4
      },
      {
         "id":3,
         "name":"September",
         "start_event":5,
         "stop_event":7
      },
      {
         "id":4,
         "name":"October",
         "start_event":8,
         "stop_event":10
      },
      {
         "id":5,
         "name":"November",
         "start_event":11,
         "stop_event":14
      },
      {
         "id":6,
         "name":"December",
         "start_event":15,
         "stop_event":20
      },
      {
         "id":7,
         "name":"January",
         "start_event":21,
         "stop_event":24
      },
      {
         "id":8,
         "name":"February",
         "start_event":25,
         "stop_event":28
      },
      {
         "id":9,
         "name":"March",
         "start_event":29,
         "stop_event":29
      }
   ]






























