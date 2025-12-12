import json

from flask import g, jsonify, request
from flask_praetorian import auth_required, current_user
from flask_restful import Resource, reqparse

from taobaoutils.app import db, guard
from taobaoutils.models import APIToken, User


def api_token_required(func):
    """
    API Token认证装饰器，用于验证外部服务的API请求
    检查Authorization header中的Bearer token
    """

    def wrapper(*args, **kwargs):
        # 获取Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"message": "Authorization header is required"}), 401

        # 检查Bearer前缀
        if not auth_header.startswith("Bearer "):
            return jsonify({"message": "Invalid authorization header format"}), 401

        # 提取token
        token = auth_header.split("Bearer ")[1]

        # 查找并验证token
        # 由于我们只存储了哈希值，所以需要遍历所有token进行验证
        all_tokens = APIToken.query.filter_by(is_active=True).all()
        valid_token = None

        for api_token in all_tokens:
            if api_token.verify_token(token):
                valid_token = api_token
                break

        if not valid_token:
            return jsonify({"message": "Invalid or expired API token"}), 401

        # 更新最后使用时间
        valid_token.update_last_used()

        # 将token和用户信息存储在请求上下文中
        g.api_token = valid_token
        g.user = valid_token.user

        return func(*args, **kwargs)

    # 保留原始函数的文档字符串和元数据
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


class RegisterResource(Resource):
    def post(self):
        """用户注册API"""
        parser = reqparse.RequestParser()
        parser.add_argument("username", type=str, required=True, help="Username is required")
        parser.add_argument("password", type=str, required=True, help="Password is required")
        parser.add_argument("email", type=str, required=True, help="Email is required")
        args = parser.parse_args()

        # 检查用户是否已存在
        if User.query.filter_by(username=args["username"]).first():
            return {"error": "用户名已存在"}, 400

        if User.query.filter_by(email=args["email"]).first():
            return {"error": "邮箱已被使用"}, 400

        # 创建新用户
        user = User(username=args["username"], email=args["email"])
        user.set_password(args["password"])

        db.session.add(user)
        db.session.commit()

        return {"message": "用户创建成功", "user": user.to_dict()}, 201


class LoginResource(Resource):
    def post(self):
        """用户登录API，返回JWT令牌"""
        parser = reqparse.RequestParser()
        parser.add_argument("username", type=str, required=True, help="Username is required")
        parser.add_argument("password", type=str, required=True, help="Password is required")
        args = parser.parse_args()

        # 验证用户
        user = guard.authenticate(args["username"], args["password"])

        # 生成令牌
        token = guard.encode_jwt_token(user)

        return {"message": "登录成功", "user": user.to_dict(), "access_token": token, "token_type": "Bearer"}, 200


class RefreshResource(Resource):
    @auth_required
    def post(self):
        """刷新JWT令牌"""
        old_token = guard.read_token_from_header()
        new_token = guard.refresh_jwt_token(old_token)
        return {"access_token": new_token}, 200


class UserResource(Resource):
    @auth_required
    def get(self):
        """获取当前用户信息"""
        user = current_user()
        return {"user": user.to_dict()}, 200

    @auth_required
    def put(self):
        """更新当前用户信息，包括设置token和其他字段"""
        user = current_user()
        parser = reqparse.RequestParser()

        # Add arguments for all updatable fields
        parser.add_argument("username", type=str, required=False)
        parser.add_argument("email", type=str, required=False)
        parser.add_argument("password", type=str, required=False)
        parser.add_argument("is_active", type=bool, required=False)
        parser.add_argument("taobao_token", type=str, required=False)  # Renamed from 'token' for clarity
        parser.add_argument("roles", type=list, location="json", required=False)  # Expects a list, will be json.dumps

        args = parser.parse_args()

        updated_fields = {}

        # Update username
        if args["username"] is not None:
            if args["username"] != user.username:
                if User.query.filter_by(username=args["username"]).first():
                    return {"error": "用户名已存在"}, 400
                user.username = args["username"]
                updated_fields["username"] = args["username"]

        # Update email
        if args["email"] is not None:
            if args["email"] != user.email:
                if User.query.filter_by(email=args["email"]).first():
                    return {"error": "邮箱已被使用"}, 400
                user.email = args["email"]
                updated_fields["email"] = args["email"]

        # Update password
        if args["password"]:
            user.set_password(args["password"])
            updated_fields["password"] = "******"  # Mask password in response

        # Update is_active
        if args["is_active"] is not None:
            user.is_active = args["is_active"]
            updated_fields["is_active"] = args["is_active"]

        # Update taobao_token
        if args["taobao_token"]:
            user.set_token(args["taobao_token"])
            updated_fields["taobao_token"] = True  # Indicate presence

        # Update roles (stored as JSON string)
        if args["roles"] is not None:
            user.roles = json.dumps(args["roles"])
            updated_fields["roles"] = args["roles"]

        if updated_fields:
            db.session.commit()
            return {"message": "用户信息更新成功", "user": user.to_dict()}, 200

        return {"message": "没有更新任何信息"}, 200


class UsersResource(Resource):
    @auth_required
    def get(self):
        """获取所有用户"""
        users = User.query.all()
        return {"users": [user.to_dict() for user in users]}, 200


class APITokenResource(Resource):
    """API Token管理资源"""

    @auth_required
    def get(self, token_id=None):
        """
        获取用户的API tokens或特定token信息

        Args:
            token_id: 可选的token ID，如果提供则获取特定token
        """
        user = current_user()

        if token_id:
            # 获取特定token
            token = APIToken.query.filter_by(id=token_id, user_id=user.id).first()
            if not token:
                return {"message": "Token not found"}, 404
            return {"token": token.to_dict()}, 200
        else:
            # 获取所有token
            tokens = APIToken.query.filter_by(user_id=user.id).all()
            return {"tokens": [token.to_dict() for token in tokens]}, 200

    @auth_required
    def post(self):
        """创建新的API token"""
        user = current_user()
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True, help="Token name is required")
        parser.add_argument("scopes", type=list, location="json", default=["read", "write"])
        parser.add_argument("expires_days", type=int, required=False)
        args = parser.parse_args()

        # 生成token
        # 生成token
        token_value, token = APIToken.create_token(
            user_id=user.id, name=args["name"], scopes=args["scopes"], expires_days=args["expires_days"]
        )

        # 保存到数据库
        db.session.add(token)
        db.session.commit()

        # 返回token信息，只在创建时显示完整token
        return {
            "token": {
                "id": token.id,
                "name": token.name,
                "token": token_value,  # 只在创建时返回完整token
                "display_token": f"{token.prefix}...{token.suffix}",
                "scopes": token.get_scopes(),
                "created_at": token.created_at.isoformat(),
                "expires_at": token.expires_at.isoformat() if token.expires_at else None,
            },
            "message": "请妥善保存此token，它只会显示一次",
        }, 201

    @auth_required
    def put(self, token_id):
        """
        更新API token信息
        - 可以启用/禁用token
        - 可以更新名称
        """
        user = current_user()
        token = APIToken.query.filter_by(id=token_id, user_id=user.id).first()

        if not token:
            return {"message": "Token not found"}, 404

        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=False)
        parser.add_argument("is_active", type=bool, required=False)
        parser.add_argument("scopes", type=list, location="json", required=False)
        args = parser.parse_args()

        # 更新token信息
        if args["name"] is not None:
            token.name = args["name"]

        if args["is_active"] is not None:
            token.is_active = bool(args["is_active"])

        if args["scopes"] is not None:
            token.scopes = json.dumps(args["scopes"])

        db.session.commit()
        return {"token": token.to_dict()}, 200

    @auth_required
    def delete(self, token_id):
        """删除API token"""
        user = current_user()
        token = APIToken.query.filter_by(id=token_id, user_id=user.id).first()

        if not token:
            return {"message": "Token not found"}, 404

        db.session.delete(token)
        db.session.commit()
        return {"message": "Token deleted successfully"}, 200
