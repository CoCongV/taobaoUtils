from flask_restful import Resource, reqparse
from flask_praetorian import auth_required
from taobaoutils.app import db
from taobaoutils.models import RequestLog, User
from taobaoutils import config_data, logger
from datetime import datetime


class RequestLogResource(Resource):
    @auth_required
    def get(self, log_id=None):
        if log_id:
            log = RequestLog.query.get_or_404(log_id)
            return log.to_dict()
        else:
            logs = RequestLog.query.order_by(RequestLog.send_time.desc()).all()
            return [log.to_dict() for log in logs]

    @auth_required
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('url', type=str, required=True, help='URL cannot be blank!')
        parser.add_argument('status', type=str, required=True, help='Status cannot be blank!')
        parser.add_argument('response_content', type=str, required=False)
        parser.add_argument('response_code', type=int, required=False)
        args = parser.parse_args()

        new_log = RequestLog(
            url=args['url'],
            status=args['status'],
            send_time=datetime.utcnow(),
            response_content=args['response_content'],
            response_code=args['response_code']
        )
        db.session.add(new_log)
        db.session.commit()
        logger.info("New request log added: %s", new_log.url)
        return new_log.to_dict(), 201