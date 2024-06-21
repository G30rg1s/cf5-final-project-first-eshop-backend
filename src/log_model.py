import mongoengine as me
from mongoengine import DateTimeField


class Log(me.Document):
    timestamp = me.DateTimeField()
    user = me.StringField()
    name = me.StringField()
    action = me.StringField()
    productkey = me.StringField()
    category = me.StringField()
    subcategory = me.StringField()
    brand = me.StringField()
    price = me.IntField()
    amount = me.IntField()
    
    
    
    meta = {"collection": "logs", "db_alias": "AnagnostopoulosGiorgosFinalProjectCF5"}


   