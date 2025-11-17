from taobaoutils.app import db
from flask_praetorian import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
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
    
    # 添加外键关联到用户
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('process_tasks', lazy=True))
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'url': self.url,
            'status': self.status,
            'send_time': self.send_time.isoformat() if self.send_time else None,
            'response': self.response,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }
    
    def __repr__(self):
        return f'<ProcessTask {self.id}: {self.url}>'

class User(UserMixin, db.Model):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, server_default='true')
    
    def set_password(self, password):
        """设置用户密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """检查用户密码"""
        return check_password_hash(self.password_hash, password)
    
    @property
    def rolenames(self):
        """返回用户角色列表"""
        return []
    
    @classmethod
    def lookup(cls, username):
        """根据用户名查找用户"""
        return cls.query.filter_by(username=username).one_or_none()
    
    @classmethod
    def identify(cls, id):
        """根据ID查找用户"""
        return cls.query.get(id)
    
    @property
    def identity(self):
        """返回用户ID"""
        return self.id
    
    def is_valid(self):
        """检查用户是否有效"""
        return self.is_active
    
    def to_dict(self):
        """将模型转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<User {self.username}>'