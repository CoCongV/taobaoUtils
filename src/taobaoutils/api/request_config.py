import json

from flask_praetorian import auth_required, current_user
from flask_restful import Resource, reqparse

from taobaoutils.app import db
from taobaoutils.models import RequestConfig

VALID_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}


class RequestConfigListResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("name", type=str, required=True, help="Name is required")
        self.parser.add_argument("request_url", type=str, required=False)
        self.parser.add_argument("method", type=str, required=False, default="POST")
        self.parser.add_argument("body", type=dict, required=False)
        self.parser.add_argument("header", type=dict, required=False)
        self.parser.add_argument("request_interval_minutes", type=int, required=False)
        self.parser.add_argument("random_min", type=int, required=False)
        self.parser.add_argument("random_max", type=int, required=False)

    @auth_required
    def get(self):
        user_id = current_user().id
        configs = RequestConfig.query.filter_by(user_id=user_id).all()
        return [config.to_dict() for config in configs]

    @auth_required
    def post(self):
        args = self.parser.parse_args()
        user_id = current_user().id

        method = args.get("method", "POST").upper()
        if method not in VALID_METHODS:
            return {"message": f"Invalid HTTP method. Allowed: {', '.join(VALID_METHODS)}"}, 400

        new_config = RequestConfig(
            user_id=user_id,
            name=args["name"],
            request_url=args.get("request_url"),
            method=method,
            body=args["body"],
            header=args["header"],
            request_interval_minutes=args.get("request_interval_minutes", 8),
            random_min=args.get("random_min", 2),
            random_max=args.get("random_max", 15),
        )

        db.session.add(new_config)
        db.session.commit()

        return new_config.to_dict(), 201


class RequestConfigResource(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("name", type=str, required=False)
        self.parser.add_argument("request_url", type=str, required=False)
        self.parser.add_argument("method", type=str, required=False)
        self.parser.add_argument("body", type=dict, required=False)
        self.parser.add_argument("header", type=dict, required=False)
        self.parser.add_argument("request_interval_minutes", type=int, required=False)
        self.parser.add_argument("random_min", type=int, required=False)
        self.parser.add_argument("random_max", type=int, required=False)

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

        if args["name"]:
            config.name = args["name"]
        if args["request_url"]:
            config.request_url = args["request_url"]
        if args["method"]:
            method = args["method"].upper()
            if method not in VALID_METHODS:
                return {"message": f"Invalid HTTP method. Allowed: {', '.join(VALID_METHODS)}"}, 400
            config.method = method
        if args["body"]:
            config.body = json.dumps(args["body"])
        if args["header"]:
            config.header = json.dumps(args["header"])
        if args["request_interval_minutes"] is not None:
            config.request_interval_minutes = args["request_interval_minutes"]
        if args["random_min"] is not None:
            config.random_min = args["random_min"]
        if args["random_max"] is not None:
            config.random_max = args["random_max"]

        db.session.commit()

        return config.to_dict()

    @auth_required
    def delete(self, config_id):
        user_id = current_user().id
        config = RequestConfig.query.filter_by(id=config_id, user_id=user_id).first_or_404()

        db.session.delete(config)
        db.session.commit()

        return {"message": "RequestConfig deleted successfully"}, 200
