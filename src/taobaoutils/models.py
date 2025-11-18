from datetime import datetime
from taobaoutils.app import db

class RequestLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    send_time = db.Column(db.DateTime, default=datetime.utcnow)
    response_content = db.Column(db.Text, nullable=True)
    response_code = db.Column(db.Integer, nullable=True)
    
    def __repr__(self):
        return f"<RequestLog {self.id} - {self.url}>"

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "status": self.status,
            "send_time": self.send_time.isoformat() if self.send_time else None,
            "response_content": self.response_content,
            "response_code": self.response_code
        }