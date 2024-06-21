import mongoengine as me
from werkzeug.security import generate_password_hash


class DeliveryAddress(me.EmbeddedDocument):
    key = me.StringField(required=True)
    city = me.StringField(required=True)
    area = me.StringField(required=True)
    code = me.StringField(required=True)
    road = me.StringField(required=True)
    number = me.StringField(required=True)
    floor = me.StringField(required=True)
    bell = me.StringField(required=True)
    specifications = me.StringField(required=False)

class Address(me.EmbeddedDocument):
    key = me.StringField(required=True, unique=True)
    city = me.StringField(required=True)
    area = me.StringField(required=True)
    code = me.StringField(required=True)
    road = me.StringField(required=True)
    number = me.StringField(required=True)
    floor = me.StringField(required=True)
    bell = me.StringField(required=True)
    specifications = me.StringField(required=False)

class Roles(me.EmbeddedDocument):
    user = me.BooleanField(required=True)
    admin = me.BooleanField(required=True)
    boss = me.BooleanField(required=True)

class User(me.Document):
    firstname = me.StringField(required=True)
    lastname = me.StringField(required=True)
    phonenumber = me.IntField(required=True)
    email = me.StringField(required=True, unique=True)
    address = me.ListField(me.EmbeddedDocumentField(Address))
    username = me.StringField(required=True, unique=True)
    password = me.StringField(required=True)
    roles = me.EmbeddedDocumentField(Roles, default=lambda: Roles(user=True, admin=False, boss=False))
    meta = {"collection": "users", "db_alias": "AnagnostopoulosGiorgosFinalProjectCF5"}

    def save(self, *args, **kwargs):
        self.password = generate_password_hash(self.password)
        super(User, self).save(*args, **kwargs)


 
