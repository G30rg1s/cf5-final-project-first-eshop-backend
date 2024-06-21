from flask import Blueprint, request, Response, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from src.user_model import User, Address
from src.product_model import Product
from src.log_model import Log
import json
from mongoengine.errors import NotUniqueError
from werkzeug.security import check_password_hash
from mongoengine.queryset.visitor import Q
from functools import wraps
from datetime import datetime
import pytz

logs = Blueprint("logs", __name__)



def log_action(user, name, action, productkey, category, subcategory, brand, price, amount):
   
    utc_timestamp = datetime.now(pytz.utc)
    
   
    greek_timezone = pytz.timezone('Europe/Athens')
    greek_timestamp = utc_timestamp.astimezone(greek_timezone)
    
    log_entry = Log(
        timestamp=greek_timestamp,
        user=user,
        name=name,
        action=action,
        productkey=productkey,
        category=category,
        subcategory=subcategory,
        brand=brand,
        price=price,
        amount=amount,
    )
    try:
        log_entry.save()
    except Exception as e:
        print("Error saving log entry:", e)
        traceback.print_exc()




       


def roles_required(*required_roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt_identity()
            user_roles = claims.get('roles', '')
            if any(role in user_roles for role in required_roles):
                return fn(*args, **kwargs)
            else:
                return jsonify({"msg": "Forbidden"}), 403
        return decorator
    return wrapper




@logs.route('/bossgetlogs', methods=['GET'])
@roles_required('truetruetrue')
def get_logs():
    try:
        logs = Log.objects().exclude('id')
        logs_list = json.loads(logs.to_json())
        return Response(json.dumps(logs_list), status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 400
