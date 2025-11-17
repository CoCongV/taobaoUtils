from flask import Flask
from flask_restful import Api
from flask_sqlalchemy import SQLAlchemy
from pathlib import Path
import os

# 初始化 Flask 扩展
db = SQLAlchemy()

def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(__name__)
    
    # 配置数据库
    # 使用当前工作目录下的 sqlite 数据库
    db_path = Path.cwd() / 'taobao.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化扩展
    db.init_app(app)
    
    # 创建 API 实例
    api = Api(app)
    
    # 注册路由和资源
    from taobaoutils.resources import ProcessResource, StatusResource
    
    api.add_resource(ProcessResource, '/api/process')
    api.add_resource(StatusResource, '/api/status')
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
    return app