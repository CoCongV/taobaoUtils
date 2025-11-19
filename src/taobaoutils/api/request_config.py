import json

from flask_restful import Resource, reqparse
from flask_praetorian import auth_required, current_user
from taobaoutils.app import db
from taobaoutils.models import RequestConfig


class RequestConfigListResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=True, help='Name is required')
        self.parser.add_argument('taobao_token', type=str, required=False)
        self.parser.add_argument('payload', type=dict, required=False)
        self.parser.add_argument('cookie', type=dict, required=False)

    @auth_required
    def get(self):
        user_id = current_user().id
        configs = RequestConfig.query.filter_by(user_id=user_id).all()
        return [config.to_dict() for config in configs]

    @auth_required
    def post(self):
        args = self.parser.parse_args()
        user_id = current_user().id
        
        new_config = RequestConfig(
            user_id=user_id,
            name=args['name'],
            taobao_token=args['taobao_token'],
            payload=args['payload'],
            cookie=args['cookie']
        )
        
        db.session.add(new_config)
        db.session.commit()
        
        return new_config.to_dict(), 201


class RequestConfigResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('name', type=str, required=False)
        self.parser.add_argument('taobao_token', type=str, required=False)
        self.parser.add_argument('payload', type=dict, required=False)
        self.parser.add_argument('cookie', type=dict, required=False)

    @auth_required
    def get(self, config_id):
        user_id = current_user().id
        config = RequestConfig.query.filter_by(id=config_id, user_id=user_id).first_or_404()
        return config.to_dict()

    @auth_required
    def put(self, config_id):
        args = self.parser.parse_args()
        user_id = current_user().id
        config = RequestConfig.query.filter_by(id=config_id, user_id=user_id).first_or_404()
        
        if args['name']:
            config.name = args['name']
        if args['taobao_token']:
            config.taobao_token = args['taobao_token']
        if args['payload']:
            config.payload = json.dumps(args['payload'])
        if args['cookie']:
            config.cookie = json.dumps(args['cookie'])
            
        db.session.commit()
        
        return config.to_dict()

    @auth_required
    def delete(self, config_id):
        user_id = current_user().id
        config = RequestConfig.query.filter_by(id=config_id, user_id=user_id).first_or_404()
        
        db.session.delete(config)
        db.session.commit()
        
        return {'message': 'RequestConfig deleted successfully'}, 200
