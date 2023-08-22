from peewee import *

db = SqliteDatabase('people.db')


class User(Model):
    telegram_id = IntegerField()
    command = TextField()
    date_command = TextField()
    hotel_list = TextField()

    class Meta:
        database = db


db.connect()
db.create_tables([User])
