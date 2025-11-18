from taobaoutils.api.resources import ProductListingResource, ExcelUploadResource # Added ExcelUploadResource
from taobaoutils.api.auth import RegisterResource, LoginResource, RefreshResource, UserResource, UsersResource


def initialize_routes(api):
    # 认证相关路由
    api.add_resource(RegisterResource, '/api/auth/register')
    api.add_resource(LoginResource, '/api/auth/login')
    api.add_resource(RefreshResource, '/api/auth/refresh')
    api.add_resource(UserResource, '/api/auth/me')
    api.add_resource(UsersResource, '/api/auth/users')
    
    # 业务相关路由
    api.add_resource(ProductListingResource, '/api/product-listings', '/api/product-listings/<int:log_id>') # Renamed endpoint and resource
    api.add_resource(ExcelUploadResource, '/api/product-listings/upload') # New endpoint for Excel upload