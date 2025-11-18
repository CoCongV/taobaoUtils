from pathlib import Path

from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from flask_praetorian import Praetorian

from taobaoutils.auth import RegisterResource, LoginResource, RefreshResource, UserResource, UsersResource
from taobaoutils.models import User
from taobaoutils.resources import ProcessResource, StatusResource
from taobaoutils.utils import load_config


# 初始化 Flask 扩展
db = SQLAlchemy()
guard = Praetorian()


def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(__name__)

    # 加载配置
    config_data = load_config()

    # 添加密钥用于JWT签名
    app.config['SECRET_KEY'] = config_data.get('SECRET_KEY', 'your-secret-key-change-in-production')
    app.config['JWT_ACCESS_LIFESPAN'] = config_data.get('JWT_ACCESS_LIFESPAN', {'hours': 24})
    app.config['JWT_REFRESH_LIFESPAN'] = config_data.get('JWT_REFRESH_LIFESPAN', {'days': 30})

    # 配置数据库
    db_path = Path.cwd() / config_data.get('DATABASE_FILE', 'taobao.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 初始化扩展
    db.init_app(app)

    guard.init_app(app, User)

    # 创建 API 实例
    api = Api(app)

    api.add_resource(RegisterResource, '/api/register')
    api.add_resource(LoginResource, '/api/login')
    api.add_resource(RefreshResource, '/api/refresh')
    api.add_resource(UserResource, '/api/user')
    api.add_resource(UsersResource, '/api/users')

    api.add_resource(ProcessResource, '/api/process')
    api.add_resource(StatusResource, '/api/status')

    # 创建数据库表
    with app.app_context():
        db.create_all()
 
    return app
