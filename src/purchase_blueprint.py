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
import pytz 
from src.product_model import Product
from src.purchase_model import Purchase, ProductBuy
from bson import ObjectId
from mongoengine.errors import DoesNotExist

purchase = Blueprint("purchase", __name__)

@purchase.route('', methods=['DELETE'])
def remove_product_references(product):

    Purchase.objects(products__product=product).update(pull__products__product=product)


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


@purchase.route('/add_purchase', methods=['POST'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def add_purchase():
    data = request.json

    boxkey = data.get('boxkey')
    username = data.get('username')
    product_key = data.get('productkey')
    fullname = data.get('fullname')

    if not all([boxkey, username, product_key]):
        return jsonify({'error': 'Missing required fields'}), 400

    product = Product.objects(key=product_key).first()

    if not product:
        return jsonify({'error': 'Product not found'}), 404

    product_buy = ProductBuy(
        product=product,
        purchaseamount=1  
    )

    utc_timestamp = datetime.now(pytz.utc)
    
   
    greek_timezone = pytz.timezone('Europe/Athens')
    greek_timestamp = utc_timestamp.astimezone(greek_timezone)

    purchase = Purchase(
        purchaseKey=boxkey,
        timestamp=greek_timestamp,
        username=username,
        fullname=fullname,
        products=[product_buy],
        deliveryaddress=None,
        userPending=True,
        adminPending=False
    )

    try:
        purchase.save()
        return jsonify({'message': 'Purchase added successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@purchase.route('/add_more', methods=['POST'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def add_more():
    data = request.json
    print("Received data for add_more:", data)

    boxkey = data.get('boxkey')
    username = data.get('username')
    product_key_data = data.get('productkey')

    if not boxkey or not username or not product_key_data:
        print("Missing required fields:", {'boxkey': boxkey, 'username': username, 'productkey': product_key_data})
        return jsonify({'error': 'Missing required fields'}), 400

    
    product_key = product_key_data.get('key') if isinstance(product_key_data, dict) else product_key_data

    if not product_key:
        print("Product key is missing in the provided data:", product_key_data)
        return jsonify({'error': 'Product key is missing'}), 400

    try:
        purchase = Purchase.objects.get(purchaseKey=boxkey, username=username)
        print("Found purchase:", purchase)
    except DoesNotExist:
        print("Purchase not found with key and username:", {'purchaseKey': boxkey, 'username': username})
        return jsonify({'error': 'Purchase not found'}), 404

    try:
        product = Product.objects.get(key=product_key)
        print("Found product:", product)
    except DoesNotExist:
        print("Product not found with key:", product_key)
        return jsonify({'error': 'Product not found'}), 404

   
    product_buy = ProductBuy(product=product, purchaseamount=1)  

    try:
        purchase.update(push__products=product_buy)
        print("Product added to purchase successfully")
        return jsonify({'message': 'Product added to Purchase successfully'}), 201
    except ValidationError as e:
        print("ValidationError while updating purchase:", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print("Exception while updating purchase:", str(e))
        return jsonify({'error': str(e)}), 500



@purchase.route('/user_tempbox/<string:username>', methods=['GET'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def find_purchase(username):
    try:
        
        purchase = Purchase.objects.get(username=username, userPending=True)
       
        products_data = []
        for product_buy in purchase.products:
            product = Product.objects.get(id=product_buy.product.id)
            product_info = {
               'key': product.key ,
               'category': product.category ,
               'subcategory': product.subcategory ,
               'brand': product.brand ,
               'price': product.price ,
               'amount': product.amount 
            }
            product_buy_info = {
                'product': product_info,
                'purchaseamount': product_buy.purchaseamount
            }
            products_data.append(product_buy_info)

        response_data = {
            'msg': 'Purchase retrieved successfully',
            'purchaseKey': purchase.purchaseKey,
            'timestamp': purchase.timestamp,
            'username': purchase.username,
            'fullname': purchase.fullname,
            'products': products_data,
            'deliveryaddress':purchase.deliveryaddress,
            'userPending': purchase.userPending,
            'adminPending': purchase.adminPending
        }

        

        return jsonify(response_data), 200

    except Purchase.DoesNotExist:
        print(f"No pending purchase found for user {username}")
        return jsonify({'error': 'No pending purchase found for this user'}), 404

    except Exception as e:
        error_msg = f"Failed to retrieve purchase for user {username}: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500



@purchase.route('/detailed_pastbox/<string:username>/<string:boxkey>', methods=['GET'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def find_past_detailed_purchase(username, boxkey):
    try:
        purchase = Purchase.objects.get(username=username, purchaseKey=boxkey)
        
        products_data = []
        
        for product_buy in purchase.products:
            try:
                product = Product.objects.get(id=product_buy.product.id)
                product_info = {
                    'key': product.key,
                    'category': product.category,
                    'subcategory': product.subcategory,
                    'brand': product.brand,
                    'price': product.price,
                    'amount': product.amount
                }
            except Product.DoesNotExist:
                product_info = {
                    'key': 'product deleted',
                    'category': '',
                    'subcategory': '',
                    'brand': '',
                    'price': '',
                    'amount': ''
                }
                print(f"Product with ID {product_buy.product.id} not found.")
            except Exception as e:
                product_info = {
                    'key': 'product retrieval error',
                    'category': '',
                    'subcategory': '',
                    'brand': '',
                    'price': '',
                    'amount': ''
                }
                print(f"Error retrieving product: {str(e)}")
            
            product_buy_info = {
                'product': product_info,
                'purchaseamount': product_buy.purchaseamount
            }
            products_data.append(product_buy_info)

        # Assuming delivery address is correctly retrieved from purchase.deliveryaddress
        delivery_address = {
            'key': purchase.deliveryaddress.key,
            'city': purchase.deliveryaddress.city,
            'area': purchase.deliveryaddress.area,
            'code': purchase.deliveryaddress.code,
            'road': purchase.deliveryaddress.road,
            'number': purchase.deliveryaddress.number,
            'floor': purchase.deliveryaddress.floor,
            'bell': purchase.deliveryaddress.bell,
            'specifications': purchase.deliveryaddress.specifications
        }

        response_data = {
            'msg': 'Purchase retrieved successfully',
            'boxkey': purchase.purchaseKey,
            'timestamp': purchase.timestamp,
            'username': purchase.username,
            'fullname': purchase.fullname,
            'products': products_data,
            'deliveryaddress': delivery_address,
            'userPending': purchase.userPending,
            'adminPending': purchase.adminPending
        }

        return jsonify(response_data), 200

    except Purchase.DoesNotExist:
        print(f"No past purchase found for user {username} with box key {boxkey}")
        return jsonify({'error': 'No past purchase found for this user and box key'}), 404

    except Exception as e:
        error_msg = f"Failed to retrieve past purchase for user {username} and box key {boxkey}: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500





@purchase.route('/user_pasttempboxes/<string:username>', methods=['GET'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def find_past_purchases(username):
    try:
        purchases = Purchase.objects.filter(username=username, userPending=False)
        
        if not purchases:
            return jsonify({'error': f'No past purchases found for user {username}'}), 404
        
        all_purchases_data = []
        
        for purchase in purchases:
            products_data = []
            
            for product_buy in purchase.products:
                try:
                    product = Product.objects.get(id=product_buy.product.id)
                    product_info = {
                        'key': product.key,
                        'category': product.category,
                        'subcategory': product.subcategory,
                        'brand': product.brand,
                        'price': product.price,
                        'amount': product.amount
                    }
                except Product.DoesNotExist:
                    product_info = {
                        'key': 'product deleted',
                        'category': '',
                        'subcategory': '',
                        'brand': '',
                        'price': '',
                        'amount': ''
                    }
                    print(f"Product with ID {product_buy.product.id} not found.")
                except Exception as e:
                    product_info = {
                        'key': 'product retrieval error',
                        'category': '',
                        'subcategory': '',
                        'brand': '',
                        'price': '',
                        'amount': ''
                    }
                    print(f"Error retrieving product: {str(e)}")
                
                product_buy_info = {
                    'product': product_info,
                    'purchaseamount': product_buy.purchaseamount
                }
                products_data.append(product_buy_info)

            # Assuming delivery address is correctly retrieved from purchase.deliveryaddress
            delivery_address = {
                'key': purchase.deliveryaddress.key,
                'city': purchase.deliveryaddress.city,
                'area': purchase.deliveryaddress.area,
                'code': purchase.deliveryaddress.code,
                'road': purchase.deliveryaddress.road,
                'number': purchase.deliveryaddress.number,
                'floor': purchase.deliveryaddress.floor,
                'bell': purchase.deliveryaddress.bell,
                'specifications': purchase.deliveryaddress.specifications
            }

            purchase_info = {
                'boxkey': purchase.purchaseKey,
                'timestamp': purchase.timestamp,
                'username': purchase.username,
                'fullname': purchase.fullname,
                'products': products_data,
                'deliveryaddress': delivery_address,
                'userPending': purchase.userPending,
                'adminPending': purchase.adminPending
            }
            all_purchases_data.append(purchase_info)

        response_data = {
            'msg': 'Past purchases retrieved successfully',
            'purchases': all_purchases_data
        }

        return jsonify(response_data), 200

    except Purchase.DoesNotExist:
        print(f"No past purchases found for user {username}")
        return jsonify({'error': f'No past purchases found for user {username}'}), 404

    except Exception as e:
        error_msg = f"Failed to retrieve past purchases for user {username}: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500




@purchase.route('/delivery_pending', methods=['GET'])
@roles_required('truetruefalse', 'truetruetrue')
def admin_delivery_pending():
    try:
        purchases = Purchase.objects(adminPending=True, userPending=False)
        
        if not purchases:
            return jsonify({'error': 'No pending purchases found'}), 404
        
        all_purchases_data = []
        
        for purchase in purchases:
            products_data = []
            
            for product_buy in purchase.products:
                try:
                    product = Product.objects.get(id=product_buy.product.id)
                    product_info = {
                        'key': product.key,
                        'category': product.category,
                        'subcategory': product.subcategory,
                        'brand': product.brand,
                        'price': product.price,
                        'amount': product.amount
                    }
                except Product.DoesNotExist:
                    product_info = {
                        'key': 'product deleted',
                        'category': '',
                        'subcategory': '',
                        'brand': '',
                        'price': '',
                        'amount': ''
                    }
                    print(f"Product with ID {product_buy.product.id} not found.")
                except Exception as e:
                    product_info = {
                        'key': 'product retrieval error',
                        'category': '',
                        'subcategory': '',
                        'brand': '',
                        'price': '',
                        'amount': ''
                    }
                    print(f"Error retrieving product: {str(e)}")
                
                product_buy_info = {
                    'product': product_info,
                    'purchaseamount': product_buy.purchaseamount
                }
                products_data.append(product_buy_info)

            address = purchase.deliveryaddress
            address_data = {
                'key': address.key,
                'city': address.city,
                'area': address.area,
                'code': address.code,
                'road': address.road,
                'number': address.number,
                'floor': address.floor,
                'bell': address.bell,
                'specifications': address.specifications
            }

            purchase_data = {
                'msg': 'Purchase retrieved successfully',
                'boxkey': purchase.purchaseKey,
                'timestamp': purchase.timestamp,
                'username': purchase.username,
                'fullname': purchase.fullname,
                'products': products_data,
                'deliveryaddress': address_data,
                'userPending': purchase.userPending,
                'adminPending': purchase.adminPending
            }

            all_purchases_data.append(purchase_data)

        return jsonify(all_purchases_data), 200

    except Exception as e:
        error_msg = f"Failed to retrieve purchases: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500




@purchase.route('/finish_delivery/<string:boxkey>', methods=['PATCH'])
@roles_required('truetruefalse', 'truetruetrue')  
def admin_finish_delivery(boxkey):
    try:
        
        Purchase.objects(purchaseKey=boxkey).update(set__adminPending=False)

        print("Updated adminPending field for purchase with boxkey:", boxkey)
        return jsonify({'message': 'Purchase updated successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500















@purchase.route('/checkout_box/<string:boxkey>/<string:username>', methods=['PATCH'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def checkout_box(boxkey, username):
    data = request.get_json()
    print(f"Received JSON data: {data}") 
   
    try:
        purchase = Purchase.objects(purchaseKey=boxkey).first()
        if not purchase:
            return jsonify({'msg': 'No purchase found with provided key and username'}), 404

        print(f"Fetched purchase: {purchase}")  

        products_data = data.get('products', [])
        deliveryaddress_data = data.get('deliveryaddress', {})

        for product_data in products_data:
            product_key = product_data.get('product', {}).get('key')
            purchase_amount = product_data.get('purchaseamount', 1)

            for product_buy in purchase.products:
                if product_buy.product.key == product_key:
                    product_buy.purchaseamount = purchase_amount
                    if product_buy.product.amount >= purchase_amount:
                        product_buy.product.amount -= purchase_amount
                        product_buy.product.save()
                    else:
                        return jsonify({'msg': f'Not enough stock available for product with key {product_buy.product.key}'}), 400

        purchase.save()

        print("Updated purchase amounts")  

        purchase.update(
            set__userPending=False,
            set__adminPending=True,
            set__deliveryaddress=deliveryaddress_data
        )
        print("Updated userPending, adminPending, and deliveryaddress fields")  

        updated_purchase = Purchase.objects(purchaseKey=boxkey).first()
        if not updated_purchase:
            return jsonify({'msg': 'No purchase found with provided key and username'}), 404

        return jsonify({'msg': 'Checkout completed successfully', 'purchases': updated_purchase.to_json()}), 200

    except Exception as e:
        print(f"An error occurred: {str(e)}")  
        return jsonify({'msg': 'An error occurred', 'error': str(e)}), 500



@purchase.route('/delete_tempbox/<string:boxkey>/<string:username>', methods=['DELETE'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def delete_tempbox(boxkey, username):
    try:
        # Find the box by purchasekey and username
        box_to_delete = Purchase.objects(purchaseKey=boxkey, username=username, userPending=True).first()

        if box_to_delete:
            # Delete the box if found
            box_to_delete.delete()
            return jsonify({"message": "Tempbox deleted successfully"}), 200
        else:
            return jsonify({"message": "Tempbox not found"}), 404
    except Exception as e:
        # Handle exceptions
        return jsonify({"message": "An error occurred", "error": str(e)}), 500



@purchase.route('/delete_tempbox_product/<string:boxkey>/<string:username>/<string:productkey>', methods=['DELETE'])
@roles_required('truefalsefalse', 'truetruefalse', 'truetruetrue')
def delete_tempbox_product(boxkey, username, productkey):
    try:
        # Find the purchase using boxkey and username
        purchase = Purchase.objects.get(purchaseKey=boxkey, username=username)
        print("Found purchase:", purchase)
    except DoesNotExist:
        print("Purchase not found with key and username:", {'purchaseKey': boxkey, 'username': username})
        return jsonify({'error': 'Purchase not found'}), 404

    # Find the ProductBuy in the purchase containing the specified product key
    product_buy_to_remove = None
    for product_buy in purchase.products:
        if product_buy.product.key == productkey:
            product_buy_to_remove = product_buy
            break

    if not product_buy_to_remove:
        print("Product not found in the purchase with key:", productkey)
        return jsonify({'error': 'Product not found in the purchase'}), 404

    try:
        # Remove the ProductBuy from the purchase
        purchase.update(pull__products=product_buy_to_remove)
        print("ProductBuy removed from purchase successfully")
        return jsonify({'message': 'Product removed from Purchase successfully'}), 200
    except ValidationError as e:
        print("ValidationError while updating purchase:", str(e))
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print("Exception while updating purchase:", str(e))
        return jsonify({'error': str(e)}), 500





