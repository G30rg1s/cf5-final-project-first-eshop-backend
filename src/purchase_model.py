import mongoengine as me
from src.product_model import Product
from src.user_model import Address, DeliveryAddress
from mongoengine import DateTimeField


class ProductBuy(me.EmbeddedDocument):
    product = me.ReferenceField(Product)
    purchaseamount = me.IntField()

class Purchase(me.Document):
    timestamp = me.DateTimeField() 
    purchaseKey = me.StringField(required=True)
    username = me.StringField(required=True)
    fullname = me.StringField()
    products = me.ListField(me.EmbeddedDocumentField(ProductBuy))
    deliveryaddress = me.EmbeddedDocumentField(DeliveryAddress)
    userPending = me.BooleanField(default=True)
    adminPending = me.BooleanField(default=False)
    
    meta = {"collection": "purchases", "db_alias": "AnagnostopoulosGiorgosFinalProjectCF5"}
