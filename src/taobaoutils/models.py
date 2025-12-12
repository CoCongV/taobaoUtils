import json
import secrets
from datetime import UTC, datetime, timedelta

from flask_praetorian import SQLAlchemyUserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from taobaoutils.app import db, guard


class User(db.Model, SQLAlchemyUserMixin):
    """用户模型，兼容 Flask-Praetorian"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

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
    product_listings = db.relationship("ProductListing", backref="user", lazy=True)

    def __init__(
        self,
        username,
        email,
        password=None,
        sub_user=None,
        userids=None,
        filter_copied=True,
        copy_type=1,
        param_id=None,
        is_search="0",
        **kwargs,
    ):
        self.username = username
        self.email = email
        if password:
            self.set_password(password)
        # 设置其他属性
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_password(self, password):
        """设置密码哈希"""
        self.password_hash = guard.hash_password(password)

    def verify_password(self, password):
        """验证密码"""
        return guard.pwd_ctx.verify(password, self.password_hash)

    # Flask-Praetorian compatibility
    check_password = verify_password

    @property
    def password(self):
        return self.password_hash

    @password.setter
    def password(self, password):
        self.set_password(password)

    def set_token(self, token):
        """设置淘宝token"""
        self.taobao_token = token
        self.updated_at = datetime.now(UTC)

    @property
    def rolenames(self):
        """Praetorian 需要的属性，返回用户角色"""
        if self.roles:
            try:
                return json.loads(self.roles)
            except Exception:
                return []
        return ["user"]  # 默认角色

    @property
    def identity(self):
        """Praetorian 需要的属性，返回用户唯一标识"""
        return self.id

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_search": self.is_search,
        }


class ProductListing(db.Model):
    """产品列表模型"""

    __tablename__ = "product_listings"  # Renamed table

    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(50), nullable=False, default="requested")  # 修改默认值为'requested'
    send_time = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    response_content = db.Column(db.Text, nullable=True)  # 存储API响应内容
    response_code = db.Column(db.Integer, nullable=True)  # 存储API响应状态码

    # New columns for product listing information
    product_id = db.Column(db.String(255), nullable=True)  # 淘宝商品ID
    product_link = db.Column(db.String(500), nullable=True)  # 商品链接
    title = db.Column(db.String(500), nullable=True)  # 商品标题
    stock = db.Column(db.Integer, nullable=True)  # 库存
    listing_code = db.Column(db.String(255), nullable=True)  # 商家编码

    # Foreign key to User model
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # Foreign key to RequestConfig model
    request_config_id = db.Column(db.Integer, db.ForeignKey("request_configs.id"), nullable=False)
    request_config = db.relationship("RequestConfig", backref="product_listings", lazy=True)

    def __init__(
        self,
        user_id,
        request_config_id,
        status="requested",
        send_time=None,
        response_content=None,
        response_code=None,
        product_id=None,
        product_link=None,
        title=None,
        stock=None,
        listing_code=None,
    ):
        self.user_id = user_id
        self.request_config_id = request_config_id
        self.status = status
        self.send_time = send_time or datetime.now(UTC)
        self.response_content = response_content
        self.response_code = response_code
        self.product_id = product_id
        self.product_link = product_link
        self.title = title
        self.stock = stock
        self.listing_code = listing_code

    def __repr__(self):
        return f"<ProductListing {self.id} - {self.product_id or self.product_link}>"  # Updated to use product_link

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
            "listing_code": self.listing_code,  # 上架编码
            "user_id": self.user_id,
            "request_config_id": self.request_config_id,
        }


class RequestConfig(db.Model):
    """请求配置模型"""

    __tablename__ = "request_configs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    request_url = db.Column(db.String(500), nullable=True)  # 目标URL
    taobao_token = db.Column(db.Text, nullable=True)
    body = db.Column(db.Text, nullable=False)  # 存储为JSON字符串
    header = db.Column(db.Text, nullable=False)  # 存储为JSON字符串，用于HTTP头

    # Scheduler Params
    request_interval_minutes = db.Column(db.Integer, default=8, nullable=True)
    random_min = db.Column(db.Integer, default=2, nullable=True)
    random_max = db.Column(db.Integer, default=15, nullable=True)

    user = db.relationship("User", backref="request_configs", lazy=True)

    def __init__(
        self,
        user_id,
        name,
        body,
        header,
        request_url=None,
        taobao_token=None,
        request_interval_minutes=8,
        random_min=2,
        random_max=15,
    ):
        self.user_id = user_id
        self.name = name
        self.request_url = request_url
        self.taobao_token = taobao_token
        # Ensure body is stored as string
        self.body = json.dumps(body) if isinstance(body, (dict, list)) else body
        # Ensure header is stored as string
        self.header = json.dumps(header) if isinstance(header, (dict, list)) else header
        self.request_interval_minutes = request_interval_minutes
        self.random_min = random_min
        self.random_max = random_max

    def __repr__(self):
        return f"<RequestConfig {self.id} - {self.name}>"

    def generate_body(self, product):
        """
        根据ProductListing对象生成具体的请求体
        """
        if not self.body:
            return {}

        template_str = self.body
        # Use to_dict() to get product attributes
        params = product.to_dict()

        for key, value in params.items():
            val_str = str(value) if value is not None else ""
            template_str = template_str.replace(f"{{{key}}}", val_str)

        return json.loads(template_str)

    def set_cookie(self, cookie_data):
        """
        将cookie数据存入header字段中

        Args:
            cookie_data: 字典格式的cookie数据
        """
        # 获取现有的header数据
        headers = {}
        if self.header:
            try:
                headers = json.loads(self.header)
            except json.JSONDecodeError:
                pass

        # 处理cookie数据并添加到header中
        if cookie_data:
            # 检查cookie_data是字典还是字符串
            if isinstance(cookie_data, dict):
                # 如果是字典，将其格式化为字符串
                cookie_str = "; ".join([f"{key}={value}" for key, value in cookie_data.items()])
            else:
                # 如果已经是字符串，直接使用
                cookie_str = str(cookie_data)

            # 将cookie添加到header中
            headers["Cookie"] = cookie_str

            # 保存更新后的header
            self.header = json.dumps(headers)

    def to_dict(self):
        body_obj = None
        if self.body:
            try:
                body_obj = json.loads(self.body)
            except json.JSONDecodeError:
                pass

        header_obj = None
        if self.header:
            try:
                header_obj = json.loads(self.header)
            except json.JSONDecodeError:
                pass

        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "request_url": self.request_url,
            "taobao_token": self.taobao_token,
            "body": body_obj,
            "header": header_obj,
            "request_interval_minutes": self.request_interval_minutes,
            "random_min": self.random_min,
            "random_max": self.random_max,
        }


class APIToken(db.Model):
    """API Token模型，用于外部服务访问"""

    __tablename__ = "api_tokens"

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(255), nullable=False, unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)  # Token名称，方便用户识别
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    scopes = db.Column(db.Text, nullable=True)  # JSON格式存储权限范围
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    expires_at = db.Column(db.DateTime, nullable=True)  # 可选的过期时间
    last_used_at = db.Column(db.DateTime, nullable=True)  # 最后使用时间
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    prefix = db.Column(db.String(10), nullable=False)  # Token前缀，用于识别
    suffix = db.Column(db.String(6), nullable=False)  # Token后缀，用于用户识别

    # 关联到用户
    user = db.relationship("User", backref=db.backref("api_tokens", lazy=True))

    @staticmethod
    def generate_token(user_id, name, scopes=None, expires_days=None):
        """
        生成新的API Token

        Args:
            user_id: 用户ID
            name: Token名称
            scopes: 权限范围列表
            expires_days: 过期天数，None表示永不过期

        Returns:
            tuple: (原始token字符串, APIToken对象)
        """
        # 生成安全的随机token
        token_bytes = secrets.token_urlsafe(32)  # 生成安全的随机字符串

        # 创建前缀和后缀用于显示（不用于验证）
        prefix = token_bytes[:10]
        suffix = token_bytes[-6:]

        # 计算过期时间
        expires_at = None
        if expires_days:
            expires_at = datetime.now(UTC) + timedelta(days=expires_days)

        # 生成哈希值用于存储
        token_hash = generate_password_hash(token_bytes)

        # 创建token记录
        token = APIToken(
            token_hash=token_hash,
            name=name,
            user_id=user_id,
            scopes=json.dumps(scopes) if scopes else None,
            expires_at=expires_at,
            prefix=prefix,
            suffix=suffix,
        )

        return token_bytes, token

    def verify_token(self, token):
        """
        验证token是否有效

        Args:
            token: 待验证的token字符串

        Returns:
            bool: token是否有效
        """
        # 检查token是否激活
        if not self.is_active:
            return False

        # 检查token是否过期
        if self.expires_at and datetime.now(UTC) > self.expires_at.replace(tzinfo=UTC):
            return False

        # 验证token哈希
        return check_password_hash(self.token_hash, token)

    def update_last_used(self):
        """更新最后使用时间"""
        self.last_used_at = datetime.now(UTC)
        db.session.commit()

    def get_scopes(self):
        """获取权限范围列表"""
        if self.scopes:
            try:
                return json.loads(self.scopes)
            except Exception:
                pass
        return []

    def to_dict(self):
        """转换为字典格式，不包含完整token"""
        return {
            "id": self.id,
            "name": self.name,
            "display_token": f"{self.prefix}...{self.suffix}",
            "user_id": self.user_id,
            "scopes": self.get_scopes(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "is_active": self.is_active,
        }
