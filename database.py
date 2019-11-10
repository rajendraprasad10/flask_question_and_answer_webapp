from flask import g
import sqlite3
 # coonect to data base
def connect_db():
    sql = sqlite3.connect('question.db')
    sql.row_factory = sqlite3.Row
    return sql

def get_db():
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db
