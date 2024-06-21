from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from src.user_model import User, Address
from src.product_model import Product
from src.log_model import Log
from src.log_blueprint import log_action
import json
from mongoengine.errors import NotUniqueError
from werkzeug.security import check_password_hash
from mongoengine.queryset.visitor import Q
from functools import wraps
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

product = Blueprint("product", __name__)



def roles_required(*required_roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt_identity()
            user_roles = claims.get('roles', '')
            fullname = claims.get('fullname', '') 
            username = claims.get('username', '') 
            if any(role in user_roles for role in required_roles):
                return fn(*args, **kwargs)
            else:
                return jsonify({"msg": "Forbidden"}), 403
        return decorator
    return wrapper


   

@product.route('/add_product', methods=['POST'])
@roles_required('truetruefalse', 'truetruetrue')
def add_product():
    data = request.get_json()
    claims = get_jwt_identity()
    fullname = claims.get('fullname', '')

    try:
        product = Product(**data)
        product.save()
        log_action(
    user=claims.get('username', ''),
    name= claims.get('fullname', ''),
    action="ADD",
    productkey=data.get("productkey"),
    category=data.get("category"),
    subcategory=data.get("subcategory"),
    brand=data.get("brand"),
    price=data.get("price"),
    amount=data.get("amount")
)
        
        return Response(json.dumps({"msg": "Product added"}), status=201, mimetype='application/json')
    except NotUniqueError:
        return jsonify({"msg": "Product with this key already exists"}), 400
    except Exception as e:
        return jsonify({"msg": str(e)}), 500



@product.route('/allproducts', methods=['GET'])
@roles_required('truefalsefalse','truetruefalse', 'truetruetrue')
def get_products():
    try:
        products = Product.objects().exclude('id')
        products_list = json.loads(products.to_json())
        return Response(json.dumps(products_list), status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 400

        

@product.route("/update_product/<string:key>", methods=["PATCH"])
@roles_required('truetruefalse', 'truetruetrue')
def update_product(key):
    try:
        data = request.get_json()
        price = data.get('price')
        amount = data.get('amount')
        claims = get_jwt_identity()
        

        product_to_update = Product.objects(key=key).first()
        if not product_to_update:
            return jsonify({"msg": "Product not found"}), 404

        # Check if the price is being updated
        if price is not None and price != product_to_update.price:
            product_to_update.modify(price=price)

        # Check if the amount is being updated
        if amount is not None and amount != product_to_update.amount:
            product_to_update.modify(amount=amount)

            log_action(
    user=claims.get('username', ''),
    name= claims.get('fullname', ''),
    action="UPDATE",
    productkey=key,
    category=data.get("category"),
    subcategory=data.get("subcategory"),
    brand=data.get("brand"),
    price=data.get("price"),
    amount=data.get("amount"),
    
)

        return jsonify({"msg": "Product updated successfully"}), 200
    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 400



@product.route("/delete_product/<string:key>", methods=["DELETE"])
@roles_required('truetruefalse', 'truetruetrue')
def delete_product(key):
    try:
        claims = get_jwt_identity()
        fullname = claims.get('fullname', '')
        product_to_delete = Product.objects(key=key).first()
        if not product_to_delete:
            return jsonify({"msg": "Product not found"}), 404


        product_data = {
            "productkey": product_to_delete.key,
            "category": product_to_delete.category,
            "subcategory": product_to_delete.subcategory,
            "brand": product_to_delete.brand,
            "price": product_to_delete.price,
            "amount": product_to_delete.amount
        }

        
        product_to_delete.delete()

        log_action(
            user= claims.get('username', ''),
            name= claims.get('fullname', ''),
            action="DELETE",
            **product_data
        )

        return jsonify({"msg": "Product deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 400




@product.route("/massive_delete_products/<string:category>/<string:subcategory>/<string:brand>", methods=["DELETE"])
@roles_required('truetruefalse', 'truetruetrue') 
def massive_delete_products(category, subcategory, brand):
    print(f"Category: {category}, Subcategory: {subcategory}, Brand: {brand}")  
    
    try:
        if category != 'None':
            if subcategory != 'None':
                if brand != 'None':
                    prodtodelete = Product.objects(category=category, subcategory=subcategory, brand=brand).all()
                else:
                    prodtodelete = Product.objects(category=category, subcategory=subcategory).all()
            else:
                if brand != 'None':
                    prodtodelete = Product.objects(category=category, brand=brand).all()
                else:
                    prodtodelete = Product.objects(category=category).all()
        else:
            if subcategory != 'None':
                if brand != 'None':
                    prodtodelete = Product.objects(subcategory=subcategory, brand=brand).all()
                else:
                    prodtodelete = Product.objects(subcategory=subcategory).all()
            else:
                if brand != 'None':
                    prodtodelete = Product.objects(brand=brand).all()
                else:
                    return make_response(jsonify({"message": "No criteria provided"}), 400)
        
        print(f'products--{prodtodelete}')            

        if not prodtodelete:
            return make_response(jsonify({"message": "No products found matching the criteria"}), 404)

        for product in prodtodelete:
            product.delete()

        return make_response(jsonify({"message": "Products deleted successfully"}), 200)

    except DoesNotExist:
        return make_response(jsonify({"message": "No products found matching the criteria"}), 404)
    












