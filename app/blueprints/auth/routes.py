from flask import request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt
)
from app.blueprints.auth import auth_bp
from app.models.user import User
from app.extensions import db

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({"error": "Champs manquants / حقول مفقودة"}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Nom d'utilisateur déjà utilisé / اسم المستخدم موجود بالفعل"}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({"error": "Email déjà utilisé / البريد الإلكتروني موجود بالفعل"}), 400

    # Force role to 'user' for public registration to prevent escalation
    user = User(username=data['username'], email=data['email'], role='user')
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "User registered successfully", "user": user.to_dict()}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"error": "Nom d'utilisateur ou mot de passe manquant / اسم المستخدم أو كلمة المرور مفقودة"}), 400

    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict()
        }), 200

    return jsonify({"error": "Identifiants invalides / بيانات اعتماد غير صالحة"}), 401

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    return jsonify(access_token=access_token), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    # In a real app with blocklisting, we would add the JTI to the blocklist here
    return jsonify({"message": "Logged out"}), 200

@auth_bp.route('/password-reset', methods=['POST'])
def password_reset():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({"error": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    # In a real app, send an email with a reset link.
    # For this demo, we'll just return success.
    return jsonify({"message": "Password reset link sent to email"}), 200
