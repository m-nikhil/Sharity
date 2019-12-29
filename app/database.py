from flask import g

def init_db(client):
    g.db = client


def teardown_db():
    db = g.pop('db', None)

    if db is not None:
        db.close()

def get_db():
    if 'db' not in g:
        g.db = init_db()

    return g.db