from taobaoutils.api.resources import ProductListingResource, ExcelUploadResource, SchedulerCallbackResource
from taobaoutils.api.auth import RegisterResource, LoginResource, RefreshResource, UserResource, UsersResource, APITokenResource
from taobaoutils.api.request_config import RequestConfigListResource, RequestConfigResource


def initialize_routes(api):
    # 认证相关路由
    api.add_resource(RegisterResource, '/api/auth/register')
    api.add_resource(LoginResource, '/api/auth/login')
    api.add_resource(RefreshResource, '/api/auth/refresh')
    api.add_resource(UserResource, '/api/auth/me')
    api.add_resource(UsersResource, '/api/auth/users')
    
    # API Token管理路由
    api.add_resource(APITokenResource, '/api/tokens', '/api/tokens/<int:token_id>')
    
    # 业务相关路由
    api.add_resource(ProductListingResource, '/api/product-listings', '/api/product-listings/<int:log_id>')
    api.add_resource(ExcelUploadResource, '/api/product-listings/upload')
    api.add_resource(SchedulerCallbackResource, '/api/scheduler/callback') # 添加新的回调端点

    # RequestConfig routes
    api.add_resource(RequestConfigListResource, '/api/request-configs')
    api.add_resource(RequestConfigResource, '/api/request-configs/<int:config_id>')