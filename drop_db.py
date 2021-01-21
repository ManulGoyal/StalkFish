from mongoengine import *

db = connect('StalkDB')
db.drop_database('StalkDB')