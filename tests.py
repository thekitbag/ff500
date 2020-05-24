from datetime import datetime, timedelta
import unittest
from webapp import app, db
from webapp.models import User, League, Player, GameweekPerformance

class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = User(username='mark')
        u.set_password('Password1')
        self.assertFalse(u.check_password('password'))
        self.assertTrue(u.check_password('Password1'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_joinLeague(self):
        u = User(username='mark', fpl_id=229086)
        l = League(league_id=1, league_name='ff500')
        u.joinLeague(l)
        a = [member for member in l.members]
        b = [league for league in u.memberships]
        self.assertEqual(a[0].entrant, u)
        self.assertEqual(b[0].league, l)

    def test_getHistory(self):
        u = User(username='mark', fpl_id=229086)
        u.getHistory()
        a = [gw for gw in u.fpl_gameweeks]
        self.assertEqual(a[0].fpl_points, 96)
        self.assertEqual(a[0].user_id, 1)
        self.assertLess(len(a), 38)
        self.assertEqual(a[0].chip, '3xc')

    def test_getPicksHistory(self):
        u = User(username='mark', fpl_id=229086)
        u.getHistory()
        u.getPicksHistory()
        Player.buildPlayerTable()
        a = [pick for pick in u.picks]
        self.assertEqual(a[0].element_id, 93)
        self.assertEqual(a[7].is_captain, 1)
        self.assertEqual(a[0].user, u)

"""commenting out as this takes a while to run
class GameweekPerformanceModelCase(unittest.TestCase):
    def test_buildGameweekPerformanceTable(self):
        Player.buildPlayerTable()
        GameweekPerformance.buildGameweekPerformanceTable()
        a = GameweekPerformance.query.filter_by(fpl_event=1).first()
        self.assertEqual(a.element_id, 1)
        b = Player.query.filter_by(name='Mustafi').first()
        b_gameweeks = b.gameweek_performances
        self.assertEqual(b_gameweeks[0].points, 0)
        self.assertEqual(b_gameweeks[13].points, 4)
        self.assertLess(len(b_gameweeks), 38)
        c = Player.query.filter_by(name='Maitland-Niles').first()
        c_gameweeks = c.gameweek_performances
        self.assertEqual(c_gameweeks[5].red_cards, 1)
"""

class FineModelCase(unittest.TestCase):
    f= Fine(name='red card', description='any player gets a red')
    l = League(league_id=1, league_name='ff500')
    l.fines.append(f)
    self.assertEqual(l.fines, 93)




if __name__ == '__main__':
    unittest.main(verbosity=2)