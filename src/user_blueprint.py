from flask import Blueprint, request, Response, jsonify 
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, get_jwt
from src.user_model import User, Address
import json
from mongoengine.errors import NotUniqueError
from werkzeug.security import check_password_hash
from mongoengine.queryset.visitor import Q
from functools import wraps

user = Blueprint("user", __name__)

def roles_required(*required_roles):
    def wrapper(fn):
        @wraps(fn)
        @jwt_required()
        def decorator(*args, **kwargs):
            claims = get_jwt_identity()
            user_roles = claims.get('roles', '')
            print("User Roles:", user_roles)  
            print("Required Roles:", required_roles)  
            if any(role in user_roles for role in required_roles):
                return fn(*args, **kwargs)
            else:
                return jsonify({"msg": "Forbidden"}), 403
        return decorator
    return wrapper




@user.route("/register", methods=["POST"])
def register():
    try:
        data = request.get_json()
        User(**data).save() 
        return Response(json.dumps({"msg": "User registered"}), status=201)
    except NotUniqueError:
        return Response(json.dumps({"msg": "Email already in use"}), status=400)
    except Exception as e:
        print(e)
        return Response(json.dumps({"msg": str(e)}), status=400)


@user.route("/check_duplicate_email/<string:email>", methods=["GET"])
def check_duplicate_email(email):
    try:
        if User.objects(email=email):
            return Response(json.dumps({"msg": "Email already in use"}), status=400)
        return Response(json.dumps({"msg": "Email available"}), status=200)
    except Exception as e:
        print(e)
        return Response(json.dumps({"msg": str(e)}), status=400)


@user.route("/check_duplicate_username/<string:username>", methods=["GET"])
def check_duplicate_username(username):
    try:
        if User.objects(username=username):
            return Response(json.dumps({"msg": "Username already in use"}), status=400)
        return Response(json.dumps({"msg": "Username available"}), status=200)
    except Exception as e:
        print(e)
        return Response(json.dumps({"msg": str(e)}), status=400)



@user.route("/login", methods=["POST"])
def login():
    try:
        data = request.get_json()
        user = User.objects(username=data["username"]).first()
        if user:
            if check_password_hash(user.password, data["password"]):
                fullname = f"{user.firstname}  {user.lastname}"
                Roles = f" {user.roles.user}{user.roles.admin}{user.roles.boss}"
                roles = Roles.lower()
                  
                 
                identity = {"fullname": fullname, "username": user.username,  "roles": roles}
                access_token = create_access_token(identity=identity)
                return Response(
                    json.dumps(
                        {"msg": "Login successful", "access_token": access_token}
                    ),
                    status=200,
                )
        return Response(json.dumps({"msg": "Invalid credentials"}), status=400)
    except Exception as e:
        print(e)
        return Response(json.dumps({"msg": str(e)}), status=400)



@user.route("/myprofile/<string:username>", methods=["GET"])
def getMyDetails(username):
    try:
        user = User.objects(username=username).first()
        if not user:
            return Response(json.dumps({"msg": "User not found"}), status=404, mimetype='application/json')
        user_data = {
            "firstname": user.firstname,
            "lastname": user.lastname,
            "phonenumber": user.phonenumber,
            "email": user.email,
            "username": user.username,
            "address": [addr.to_mongo().to_dict() for addr in user.address]
        }
        return jsonify(user_data), 200
    except Exception as e:
        print(e)
        return Response(json.dumps({"msg": str(e)}), status=400, mimetype='application/json')


@user.route("/add_address/<string:username>", methods=["POST"])
def addNewAddress(username):
    try:
        user = User.objects(username=username).first()
        if not user:
            return Response(json.dumps({"msg": "User not found"}), status=404)

        data = request.get_json()
        key = data.get('key')
        city = data.get('city')
        area = data.get('area')
        code = data.get('code')
        road = data.get('road')
        number = data.get('number')
        floor = data.get('floor')
        bell = data.get('bell')
        specifications = data.get('specifications')

        
        new_address = Address(
            key=key,
            city=city,
            area=area,
            code=code,
            road=road,
            number=number,
            floor=floor,
            bell=bell,
            specifications=specifications
        )

        
        
        User.objects(username=username).update_one(push__address=new_address)

        return Response(json.dumps({"msg": "Address added successfully"}), status=200)
    except Exception as e:
        print(e)
        return Response(json.dumps({"msg": str(e)}), status=400)



@user.route("/delete_address/<string:username>/<string:key>", methods=["DELETE"])
def delete_address(username, key):
    try:
        user = User.objects(username=username).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404

        address_to_delete = None
        for address in user.address:
            if address.key == key:
                address_to_delete = address
                break
        
        if not address_to_delete:
            return jsonify({"msg": "Address not found"}), 404
        
       # user.address.remove(address_to_delete)
        User.objects(username=username).update_one(pull__address=address_to_delete)
        
        return jsonify({"msg": "Address deleted successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 400



@user.route("/update_address/<string:username>/<string:key>/<string:bell>/<string:specifications>", methods=["PATCH"])
def update_address(username, key, bell, specifications):
    try:
        user = User.objects(username=username).first()
        if not user:
            return jsonify({"msg": "User not found"}), 404

       # data = request.get_json()
        new_bell = bell
        new_specifications = specifications

        address_to_update = None
        for address in user.address:
            if address.key == key:
                address_to_update = address
                break
        
        if not address_to_update:
            return jsonify({"msg": "Address not found"}), 404

        if new_bell is not None:
            address_to_update.bell = new_bell
        if new_specifications is not None:
            address_to_update.specifications = new_specifications
        
        
        user.modify(address=user.address)

        return jsonify({"msg": "Address updated successfully"}), 200

    except Exception as e:
        print(e)
        return jsonify({"msg": str(e)}), 400



@user.route('/users', methods=['GET'])
@roles_required('truetruefalse', 'truetruetrue')
def get_users():
    try:
       
        users = User.objects().exclude('id')
        users_list = json.loads(users.to_json())

       
        for user in users_list:
            roles = f"{user['roles']['user']}{user['roles']['admin']}{user['roles']['boss']}".lower()
            user['roles_string'] = roles

       
        return Response(json.dumps(users_list), status=200, mimetype='application/json')
    
    except Exception as e:
       
        print(e)
        return jsonify({"msg": str(e)}), 400


@user.route("/update_role/<string:role1>", methods=["PATCH"])
@roles_required('truetruetrue')
def update_role(role1):
    try:
        data = request.get_json()
        username = data.get('username')

        if not username:
            return jsonify({"msg": "Invalid input"}), 400

        user_to_update = User.objects(username=username).first()
        if not user_to_update:
            return jsonify({"msg": "User not found"}), 404

        print("role1:", role1)

        if role1 == 'truefalsefalse':
            user_to_update.roles.user = True
            user_to_update.roles.admin = False
            user_to_update.roles.boss = False
        elif role1 == 'truetruefalse':
            user_to_update.roles.user = True
            user_to_update.roles.admin = True
            user_to_update.roles.boss = False
        elif role1 == 'truetruetrue':
            user_to_update.roles.user = True
            user_to_update.roles.admin = True
            user_to_update.roles.boss = True
        else:
            return jsonify({"msg": "Invalid role1"}), 400

        # Update user's roles directly in the database
        User.objects(username=username).update(set__roles=user_to_update.roles)

        print("Roles updated:", user_to_update.roles)

        return jsonify({"msg": "User updated successfully"}), 200
    except Exception as e:
        print(e)
        return jsonify({"msg": "Failed to update user roles"}), 500