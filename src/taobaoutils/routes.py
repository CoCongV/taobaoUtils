from taobaoutils.resources import RequestLogResource, RegistrationResource


def initialize_routes(api):
    api.add_resource(RequestLogResource, '/logs', '/logs/<int:log_id>')
    api.add_resource(RegistrationResource, '/register')