from mongoengine import *
import discord


class Problem(EmbeddedDocument):
    contest_id = IntField()
    index = StringField()


class User(Document):

    user_id = IntField(required=True, unique=True, null=False)
    cf_handle = StringField(required=True, null=False)
    problem_stalk = BooleanField(required=True, default=True, null=False)
    contest_stalk = BooleanField(required=True, default=True, null=False)
    solved_problems = EmbeddedDocumentListField(Problem)
    attempted_contests = ListField(field=IntField())