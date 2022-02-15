import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
from sqlalchemy.sql.expression import true

from .database.models import *
from .auth.auth import AuthError, requires_auth, get_token_auth_header

app = Flask(__name__)
setup_db(app)
cors = CORS(app, resources={r"*": {"origins": "*"}})

# CORS HEaders
@app.after_request
def after_request(response):
    response.headers.add(
      "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
    response.headers.add(
      "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTION,PATCH"
        )
    return response


'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this function will add one
'''
# db_drop_and_create_all()

'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is 
    the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=['GET'])
def retrieve_drinks():
    try:
        drinksCollection = Drink.query.all()
        if len(drinksCollection) == 0:
            abort(404)
        newest_drink = [drink.short() for drink in drinksCollection]
        return jsonify({
                'success': True, 
                'drinks': newest_drink}, 200)
    except Exception:
        abort(422)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail", methods=['GET'])
@requires_auth('get:drinks-detail')
def retrieve_drinksdetail(payload):
    drinksdetail = Drink.query.all()
    if len(drinksdetail) == 0:
        abort(404)

    return jsonify(
        {"success": True,
         "drinks": [d.long() for d in drinksdetail]
        })
    

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=['POST'])
@requires_auth('post:drinks')
def create_drink(payload):
    # Get the request json
    req = dict(request.json)
    try:
        drink = Drink(title=req.get('title'),recipe=json.dumps(req.get('recipe')))
        drink.insert()
        all_drinks = Drink.query.all()
        newest_drink = [drink.long() for drink in all_drinks]
    except Exception:
        abort(422)

    return jsonify({'success': True, 
                    'drinks': newest_drink},
                    200)


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods = ['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload,id):
    # get the body
    req = request.get_json()

    # get the drink with requested Id
    drink = Drink.query.filter(Drink.id == id).one_or_none()

    if not drink:
        abort(404)

    try:
        req_title = req.get('title')
        req_recipe = req.get('recipe')

        # If title has to be updated
        if req_title:
            drink.title = req_title 

        if req_recipe:
            drink.recipe = json.dumps(req.get('recipe'))

        # update the drink
        drink.update()

    except Exception:
        abort(422)
    
    return jsonify({'success': True, 'drinks': [drink.long()]},200)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload,id):
    # Fetch the body
    req = request.get_json()

    # get the drink for requested Id
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)

    try:
        # delete the drink
        drink.delete()
    except Exception:
        abort(422)

    return jsonify({'success': True, 'delete': id}, 200)
    
# Error Handling
'''
Example error handling for unprocessable entity
'''

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''
@app.errorhandler(404)
def resource_not_found(error):
   return jsonify({
        "success": False,
        "error": 404,
        "message": "unprocessable"
    }), 404

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(error):
    print(error)
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code

@app.errorhandler(401)
def unauthorized(error):
    print(error)
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'Unathorized'
    }), 401

@app.errorhandler(500)
def internal_server_error(error):
    print(error)
    return jsonify({
        "success": False,
        "error": 500,
        "message": 'Internal Server Error'
    }), 500

@app.errorhandler(400)
def bad_request(error):
    print(error)
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'Bad Request'
    }), 400

@app.errorhandler(405)
def method_not_allowed(error):
    print(error)
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'Method Not Allowed'
    }), 405

if __name__ == "__main__":
    app.debug = True
    app.run()
