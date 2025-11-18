from taobaoutils.api.resources import RequestLogResource
from taobaoutils.api.auth import RegisterResource, LoginResource, RefreshResource, UserResource, UsersResource


def initialize_routes(api):
    # 认证相关路由
    api.add_resource(RegisterResource, '/api/auth/register')
    api.add_resource(LoginResource, '/api/auth/login')
    api.add_resource(RefreshResource, '/api/auth/refresh')
    api.add_resource(UserResource, '/api/auth/me')
    api.add_resource(UsersResource, '/api/auth/users')
    
    # 业务相关路由
    api.add_resource(RequestLogResource, '/api/logs', '/api/logs/<int:log_id>')