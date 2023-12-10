from flask import Flask, request, jsonify, make_response, session
import jwt
import datetime
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'

# Mock database for demonstration purposes
users = [
    {'id': 1, 'username': 'user1', 'password': 'password1'},
    {'id': 2, 'username': 'user2', 'password': 'password2'}
]


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(days=31)


def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        #token = request.args.get('token')
        token = session['token']
        if not token:
            return jsonify({'Alert!': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = [user for user in users if user['id'] == data['id']][0]
        # You can use the JWT errors in exception
        # except jwt.InvalidTokenError:
        #     return 'Invalid token. Please log in again.'
        except Exception as E:
            print(E)
            return jsonify({'Message': 'Invalid token'}), 403
        return func(current_user, *args, **kwargs)
    return decorated


@app.route('/register', methods=['POST'])
def register():
    data = request.json()
    username = data['username']
    password = data['password']

    # Check if the username is already taken
    if any(user['username'] == username for user in users):
        return jsonify({'message': 'Username already exists!'}), 400

    # Create a new user
    user = {'id': len(users) + 1, 'username': username, 'password': password}
    users.append(user)

    return jsonify({'message': 'User registered successfully!'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']
    if not data or not username or not password:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    user = [user for user in users if user['username'] == username][0]
    if not user:
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    if user['password'] == password:
        session['logged_in'] = True
        token = jwt.encode(
            {
                'id': user['id'],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
            },
            app.config['SECRET_KEY']
        )
        token = bytes(token, 'utf-8')
        session['token'] = token
        return jsonify({'token': token.decode('UTF-8')})
    return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})


@app.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    # Perform any necessary logout actions
    return jsonify({'message': 'Logged out successfully!'})


@app.route('/protected', methods=['GET'])
@token_required
def protected(current_user):
    return jsonify({'message': 'This is a protected route!', 'user': current_user})


if __name__ == '__main__':
    app.debug = True
    app.run()
