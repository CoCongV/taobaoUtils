"""淘宝工具包"""

__version__ = '0.1.0'

from .app import create_app, db
from .models import ProcessTask, User
from .utils import load_config, setup_logging
import logging

# 初始化全局日志记录器
try:
    config_data = load_config()
    logger = setup_logging(config_data)
    logger.info("logger initialized successfully")
except Exception as e:
    # 如果配置文件尚未存在或加载失败，则创建一个基本的日志记录器
    logger = logging.getLogger('taobaoutils')
    logger.setLevel(logging.INFO)

    # 添加处理器（如果没有）
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.warning(f"Failed to init logger: {e}")

__all__ = ['create_app', 'db', 'ProcessTask', 'User', 'logger']
