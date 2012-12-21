from __future__ import print_function, division

import json
from collections import defaultdict

from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer, asc
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from bottle import route, run, static_file
import trueskill

db_engine = create_engine('sqlite:///games.sqlite', echo=False)
Session = scoped_session(sessionmaker(autoflush=True, autocommit=False, bind=db_engine))

Base = declarative_base()


class Game(Base):
    __tablename__ = 'games'

    game_id = Column(Integer, autoincrement=True, primary_key=True)
    player1 = Column(String)
    player2 = Column(String)
    winner = Column(Integer)

    def __init__(self, player1, player2, winner):
        self.player1 = player1
        self.player2 = player2
        self.winner = winner


@route('/games/get')
@route('/games/get/')
def get_games():
    try:
        s = Session()
        fields = ['game_id', 'player1', 'player2', 'winner']
        games = s.query(Game.game_id, Game.player1, Game.player2, Game.winner).all()
        ret = {'success': 1,
                'games' : map(lambda x: dict(zip(fields, x)), games)}
    except Exception as e:
        ret = {'success': 0,
                'message': str(e)}
    return json.dumps(ret)


@route('/games/add/<player1>/<player2>/<winner>')
@route('/games/add/<player1>/<player2>/<winner>/')
def add_game(player1, player2, winner):
    try:
        if int(winner) < 1 or int(winner) > 2:
            raise RuntimeError("winner needs to be either 1 or 2")
        s = Session()
        s.add(Game(player1, player2, winner))
        ret = {'success': 1}
        s.commit()
    except Exception as e:
        ret = {'success': 0,
                'message': str(e)}
    return json.dumps(ret)


@route('/games/remove/<game_id>')
@route('/games/remove/<game_id>/')
def remove_game(game_id):
    try:
        s = Session()
        s.query(Game).filter(Game.game_id==game_id).delete()
        s.commit()
        ret = {'success': 1}
    except Exception as e:
        ret = {'success': 0,
               'message': str(e)}
    return json.dumps(ret)


@route('/games/allplayers')
@route('/games/allplayers/')
def all_players():
    try:
        s = Session()
        unzipped = zip(*s.query(Game.player1, Game.player2).all())
        players = list(set(unzipped[0]).union(unzipped[1]))
        ret = {'success': 1, 'players': players}
    except Exception as e:
        ret = {'success': 0,
               'message': str(e)}
    return json.dumps(ret)




@route('/ratings')
@route('/ratings/')
def ratings():
    to_table = lambda x: {'player': x[0], 'mu': x[1].mu, 'sigma': x[1].sigma, 'skill': x[1].mu - 3 * x[1].sigma}
    s = Session()
    games = s.query(Game).order_by(asc(Game.game_id)).all()
    rankings = fit_trueskill(games)
    return json.dumps({'success': 1, 'ratings': map(to_table, rankings.items())})


@route('/')
@route('/<path>')
def static(path=None):
    if path is None:
        path = 'index.html'
    return static_file(path, 'static/')


def fit_trueskill(sorted_games):
    env = trueskill.TrueSkill(mu=5, sigma=3, beta=1, tau=0.3, draw_probability=0)
    ratings = defaultdict(env.create_rating)
    for game in sorted_games:
        rating1 = ratings[game.player1]
        rating2 = ratings[game.player2]
        if game.winner == 1:
            rating1, rating2 = env.rate_1vs1(rating1, rating2)
        else:
            rating2, rating1 = env.rate_1vs1(rating2, rating1)
        ratings[game.player1] = rating1
        ratings[game.player2] = rating2
    return ratings


if __name__ == '__main__':
    Base.metadata.create_all(db_engine, checkfirst=True)
    run(host='10.54.151.5', port=8888)
