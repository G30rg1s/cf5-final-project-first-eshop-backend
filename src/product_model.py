import mongoengine as me

class Product(me.Document):
    key = me.StringField(unique=True, required=True)
    category = me.StringField(required=True)
    subcategory = me.StringField(required=True)
    brand = me.StringField(required=True)
    price = me.IntField(required=True)
    amount = me.IntField(required=True)
    meta = {"collection": "products", "db_alias": "AnagnostopoulosGiorgosFinalProjectCF5"}