from mongoengine import *
import discord


class Contest(Document):

    contest_id = IntField(required=True, unique=True, null=False)

    def __str__(self):
        output = '('
        for field in Contest._fields.keys():
            output += f"{field}: {self[field]}, \n"
        output = output[0:-3] + ')'
        return output


# currently not in use
class Problem(EmbeddedDocument):

    contest_id = IntField()
    index = StringField()


class User(Document):

    user_id = IntField(required=True, unique=True, null=False)
    cf_handle = StringField(required=True, null=False)
    problem_stalk = BooleanField(required=True, default=True, null=False)
    contest_stalk = BooleanField(required=True, default=True, null=False)
    solved_problems = ListField(field=StringField())
    attempted_contests = ListField(field=IntField())

    def __str__(self):
        output = '('
        for field in User._fields.keys():
            output += f"{field}: {self[field]}, \n"
        output = output[0:-3] + ')'
        return output
