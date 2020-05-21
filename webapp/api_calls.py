import requests
import json
from datetime import datetime
from webapp import db


#https://fantasy.premierleague.com/api/entry/22702/history/
#https://fantasy.premierleague.com/api/leagues-classic/{league-id}/standings/
history_url = 'https://fantasy.premierleague.com/api/entry/'
static_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
#'https://fantasy.premierleague.com/api/entry/227902/event/32/picks/
player_url = 'https://fantasy.premierleague.com/api/element-summary/'
 
tree_fiddy_league = {
	'mark': 229086,
	'jagbir': 2028933,
	'scott': 1940244,
	'chris': 16474,
	'louis': 2948837,
	'jamie': 2037171,
	'lukas': 1401422
}

def getTeamDetails(fpl_id):
	url = history_url + str(fpl_id) + '/history/'
	r = requests.get(url)
	jsonResponse = r.json()
	return jsonResponse


def getCurrentWeekDetails():
	r = requests.get(static_url)
	data = r.json()
	events = data['events']
	for week in events:
		if week['is_current'] == True:
			return week

def getNextWeekDetails():
	r = requests.get(static_url)
	data = r.json()
	events = data['events']
	for week in events:
		if week['is_next'] == True:
			return week

def getPicks(fpl_id, week):
	url = history_url + str(fpl_id) + '/event/' + str(week)  + '/picks/'
	r = requests.get(url)
	picks = r.json()
	r2 = requests.get(static_url)
	static_data = r2.json()
	team = []
	for player in picks['picks']:
		for entry in static_data['elements']:
			if player['element'] == entry['id']:
				name = entry['first_name'] + " " + entry['second_name']
		player['name'] = name
		player_data = getPlayerDetails(player['element'])
		player_week_data = player_data['history'][-1]
		kickoff_time = datetime.strptime(player_week_data['kickoff_time'][:-1], '%Y-%m-%dT%H:%M:%S')
		now = datetime.now()
		if player_week_data['minutes'] > 0:
			player['minutes'] = True
		elif kickoff_time > now:
			player['minutes'] = ""
		else:
			player['minutes'] = False
		team.append(player)
	return {'team':team, 'points': picks['entry_history']['points']}

def getPlayerDetails(player_id):
	url = player_url + str(player_id) + "/"
	r = requests.get(url)
	data = r.json()
	return data

def getSelections(gameweek, fpl_id):
	picks = {}
	url = history_url + str(fpl_id) + '/event/' + str(gameweek)  + '/picks/'
	r = requests.get(url)
	picks = r.json()
	return picks

def getPicksHistory(gameweeks, fpl_id):
	pick_history = []
	for i in gameweeks:
		url = history_url + str(fpl_id) + '/event/' + str(i.fpl_event)  + '/picks/'
		r = requests.get(url)
		picks = r.json()
		pick_history.append({
			'gameweek': i.fpl_event,
			'picks': picks['picks'],
			'autosubs': picks['automatic_subs']
		})
	return pick_history
	
def getPlayers():
	positions = ['gk','def','mid','fw']
	teams = [
	'Arsenal',
	'Aston Villa',
	'Bournemouth',
	'Brighton',
	'Burnley',
	'Chelsea',
	'Crystal Palace',
	'Everton',
	'Leicester',
	'Liverpool',
	'Man City',
	'Man Utd',
	'Newcastle',
	'Norwich',
	'Sheffield Utd',
	'Southampton',
	'Spurs',
	'Watford',
	'West Ham',
	'Wolves' 
	]
	url = static_url
	r = requests.get(url)
	static_data = r.json()
	players = []
	for i in static_data['elements']:
		players.append({
			'name': i['web_name'],
			'position': positions[i['element_type']-1],
			'team': teams[i['team']-1] ,
			'id': i['id']
			})
	return players

def getGameweekHistory(player):
	url = player_url + str(player.element_id) + "/"
	r = requests.get(url)
	history = r.json()
	return history


