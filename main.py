from __future__ import print_function, division

import json
from sqlalchemy import create_engine, Column, String, DateTime, Boolean, Integer
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from bottle import route, run, static_file

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
        if winner < 1 or winner > 2:
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



@route('/')
@route('/<path>')
def static(path=None):
    if path is None:
        path = 'index.html'
    return static_file(path, 'static/')


if __name__ == '__main__':
    Base.metadata.create_all(db_engine, checkfirst=True)
    run(host='10.54.151.5', port=8888)
