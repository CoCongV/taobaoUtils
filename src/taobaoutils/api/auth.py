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
        """更新当前用户信息，包括设置token和其他字段"""
        user = current_user()
        parser = reqparse.RequestParser()
        
        # Add arguments for all updatable fields
        parser.add_argument('username', type=str, required=False)
        parser.add_argument('email', type=str, required=False)
        parser.add_argument('password', type=str, required=False)
        parser.add_argument('is_active', type=bool, required=False)
        parser.add_argument('taobao_token', type=str, required=False) # Renamed from 'token' for clarity
        parser.add_argument('sub_user', type=str, required=False)
        parser.add_argument('userids', type=list, location='json', required=False) # Expects a list, will be json.dumps
        parser.add_argument('filter_copied', type=bool, required=False)
        parser.add_argument('copy_type', type=int, required=False)
        parser.add_argument('param_id', type=str, required=False)
        parser.add_argument('is_search', type=str, required=False)
        parser.add_argument('roles', type=list, location='json', required=False) # Expects a list, will be json.dumps
        
        args = parser.parse_args()
        
        updated_fields = {}

        # Update username
        if args['username'] is not None:
            if args['username'] != user.username:
                if User.query.filter_by(username=args['username']).first():
                    return {'error': '用户名已存在'}, 400
                user.username = args['username']
                updated_fields['username'] = args['username']

        # Update email
        if args['email'] is not None:
            if args['email'] != user.email:
                if User.query.filter_by(email=args['email']).first():
                    return {'error': '邮箱已被使用'}, 400
                user.email = args['email']
                updated_fields['email'] = args['email']

        # Update password
        if args['password']:
            user.set_password(args['password'])
            updated_fields['password'] = '******' # Mask password in response

        # Update is_active
        if args['is_active'] is not None:
            user.is_active = args['is_active']
            updated_fields['is_active'] = args['is_active']

        # Update taobao_token
        if args['taobao_token']:
            user.set_token(args['taobao_token'])
            updated_fields['taobao_token'] = True # Indicate presence

        # Update sub_user
        if args['sub_user'] is not None:
            user.sub_user = args['sub_user']
            updated_fields['sub_user'] = args['sub_user']

        # Update userids (stored as JSON string)
        if args['userids'] is not None:
            user.userids = json.dumps(args['userids'])
            updated_fields['userids'] = args['userids']

        # Update filter_copied
        if args['filter_copied'] is not None:
            user.filter_copied = args['filter_copied']
            updated_fields['filter_copied'] = args['filter_copied']

        # Update copy_type
        if args['copy_type'] is not None:
            user.copy_type = args['copy_type']
            updated_fields['copy_type'] = args['copy_type']

        # Update param_id
        if args['param_id'] is not None:
            user.param_id = args['param_id']
            updated_fields['param_id'] = args['param_id']

        # Update is_search
        if args['is_search'] is not None:
            user.is_search = args['is_search']
            updated_fields['is_search'] = args['is_search']

        # Update roles (stored as JSON string)
        if args['roles'] is not None:
            user.roles = json.dumps(args['roles'])
            updated_fields['roles'] = args['roles']
        
        if updated_fields:
            db.session.commit()
            return {'message': '用户信息更新成功', 'user': user.to_dict()}, 200
        
        return {'message': '没有更新任何信息'}, 200


class UsersResource(Resource):
    @auth_required
    def get(self):
        """获取所有用户"""
        users = User.query.all()
        return {'users': [user.to_dict() for user in users]}, 200
