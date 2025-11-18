from flask_restful import Resource, reqparse
from flask_praetorian import auth_required, current_user
from taobaoutils.app import db, guard
from taobaoutils.models import User


class RegisterResource(Resource):
    def post(self):
        """用户注册API"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required')
        parser.add_argument('password', type=str, required=True, help='Password is required')
        parser.add_argument('email', type=str, required=True, help='Email is required')
        args = parser.parse_args()
        
        # 检查用户是否已存在
        if User.query.filter_by(username=args['username']).first():
            return {'error': '用户名已存在'}, 400
        
        if User.query.filter_by(email=args['email']).first():
            return {'error': '邮箱已被使用'}, 400
        
        # 创建新用户
        user = User(username=args['username'], email=args['email'])
        user.set_password(args['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return {'message': '用户创建成功', 'user': user.to_dict()}, 201


class LoginResource(Resource):
    def post(self):
        """用户登录API，返回JWT令牌"""
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, required=True, help='Username is required')
        parser.add_argument('password', type=str, required=True, help='Password is required')
        args = parser.parse_args()
        
        # 验证用户
        user = guard.authenticate(args['username'], args['password'])
        
        # 生成令牌
        token = guard.encode_jwt_token(user)
        
        return {
            'message': '登录成功',
            'user': user.to_dict(),
            'access_token': token,
            'token_type': 'Bearer'
        }, 200


class RefreshResource(Resource):
    @auth_required
    def post(self):
        """刷新JWT令牌"""
        old_token = guard.read_token_from_header()
        new_token = guard.refresh_jwt_token(old_token)
        return {'access_token': new_token}, 200


class UserResource(Resource):
    @auth_required
    def get(self):
        """获取当前用户信息"""
        user = current_user()
        return {'user': user.to_dict()}, 200
    
    @auth_required
    def put(self):
        """更新当前用户信息，包括设置token"""
        user = current_user()
        parser = reqparse.RequestParser()
        parser.add_argument('token', type=str, required=False)
        args = parser.parse_args()
        
        # 更新用户token
        if args['token']:
            user.set_token(args['token'])
            db.session.commit()
            return {'message': '用户token更新成功', 'user': user.to_dict()}, 200
        
        return {'message': '没有更新任何信息'}, 200


class UsersResource(Resource):
    @auth_required
    def get(self):
        """获取所有用户"""
        users = User.query.all()
        return {'users': [user.to_dict() for user in users]}, 200
