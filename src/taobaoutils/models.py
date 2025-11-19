import json
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_praetorian import SQLAlchemyUserMixin

from taobaoutils.app import db


class User(db.Model, SQLAlchemyUserMixin):
    """用户模型，兼容 Flask-Praetorian"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 淘宝相关字段
    taobao_token = db.Column(db.Text, nullable=True)
    sub_user = db.Column(db.String(255), nullable=True)
    userids = db.Column(db.Text, nullable=True)  # Stored as JSON string
    filter_copied = db.Column(db.Boolean, default=True, nullable=False)
    copy_type = db.Column(db.Integer, default=1, nullable=False)
    param_id = db.Column(db.String(255), nullable=True)
    is_search = db.Column(db.String(255), default="0", nullable=False)

    # Praetorian 需要的属性
    roles = db.Column(db.Text, nullable=True)  # 可以存储JSON格式的角色列表

    # Relationship to ProductListing
    product_listings = db.relationship('ProductListing', backref='user', lazy=True)

    def __init__(self, username, email, password=None, sub_user=None, userids=None, filter_copied=True, copy_type=1, param_id=None, is_search="0", **kwargs):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
        self.sub_user = sub_user
        self.filter_copied = filter_copied
        self.copy_type = copy_type
        self.param_id = param_id
        self.is_search = is_search
        if userids is not None:
            self.userids = json.dumps(userids)
        # 设置其他属性
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def set_token(self, token):
        """设置淘宝token"""
        self.taobao_token = token
        self.updated_at = datetime.utcnow()

    @property
    def rolenames(self):
        """Praetorian 需要的属性，返回用户角色"""
        if self.roles:
            try:
                return json.loads(self.roles)
            except Exception:
                return []
        return ['user']  # 默认角色

    @property
    def identity(self):
        """Praetorian 需要的属性，返回用户唯一标识"""
        return self.id

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        """转换为字典格式"""
        userids_list = []
        if self.userids:
            try:
                userids_list = json.loads(self.userids)
            except Exception:
                pass
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'taobao_token': bool(self.taobao_token), # Indicate presence of token, not the token itself
            'sub_user': self.sub_user,
            'userids': userids_list,
            'filter_copied': self.filter_copied,
            'copy_type': self.copy_type,
            'param_id': self.param_id,
            'is_search': self.is_search
        }


class ProductListing(db.Model):
    __tablename__ = 'product_listings' # Renamed table

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=True) # Made nullable
    send_time = db.Column(db.DateTime, default=datetime.utcnow)
    response_content = db.Column(db.Text, nullable=True)
    response_code = db.Column(db.Integer, nullable=True)

    # New columns for product listing information
    product_id = db.Column(db.String(255), nullable=True)
    product_link = db.Column(db.String(500), nullable=True)
    title = db.Column(db.String(500), nullable=True)
    stock = db.Column(db.Integer, nullable=True)
    listing_code = db.Column(db.String(255), nullable=True)

    # Foreign key to User model
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def __repr__(self):
        return f"<ProductListing {self.id} - {self.product_id or self.product_link}>" # Updated to use product_link

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
            "send_time": self.send_time.isoformat() if self.send_time else None,
            "response_content": self.response_content,
            "response_code": self.response_code,
            "product_id": self.product_id,
            "product_link": self.product_link,
            "title": self.title,
            "stock": self.stock,
            "listing_code": self.listing_code,
            "user_id": self.user_id, # Added user_id
        }