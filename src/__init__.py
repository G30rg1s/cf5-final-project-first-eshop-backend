from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from mongoengine import connect
from src.user_blueprint import user
from src.product_blueprint import product
from src.log_blueprint import logs
from src.purchase_blueprint import purchase



app = Flask(__name__)
jwt = JWTManager(app)
app.config["JWT_SECRET_KEY"] = "super secret and difficult to guess key"

connect(
    host="mongodb+srv://firstEshopAdmin:12345@cluster0.h6fel0s.mongodb.net/",
    db="AnagnostopoulosGiorgosFinalProjectCF5",
    alias="AnagnostopoulosGiorgosFinalProjectCF5",
)

cors = CORS(
    app,
    resources={r"*": {"origins": ["http://localhost:4200"]}},
)

app.register_blueprint(user, url_prefix="/user")
app.register_blueprint(product, url_prefix="/product")
app.register_blueprint(logs, url_prefix="/logs")
app.register_blueprint(purchase, url_prefix="/purchase")



