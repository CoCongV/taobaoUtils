from taobaoutils.app import db
from datetime import datetime

class ProcessTask(db.Model):
    """处理任务模型"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), default='pending')
    send_time = db.Column(db.DateTime, nullable=True)
    response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status,
            'send_time': self.send_time.isoformat() if self.send_time else None,
            'response': self.response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<ProcessTask {self.id}: {self.url}>'