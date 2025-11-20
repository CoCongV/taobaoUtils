import logging
import toml
import sys
import os
from pathlib import Path
from colorama import Fore, Style, init

# Initialize Colorama for specific colored output (not for general logging)
init()


# --- Configuration Loading ---
def load_config(): 
    try:
        # config.toml 应该位于当前工作目录
        config_path = Path(os.getcwd()) / "config.toml"
        if not config_path.exists():
            raise FileNotFoundError(f"config.toml 文件未找到于: {config_path}")
        return toml.load(config_path)
    except Exception as e:
        print(f"错误：加载 config.toml 文件失败: {e}")
        sys.exit(1)


config_data = load_config()

# --- Logging Setup ---
# 自定义日志格式化器，用于彩色输出


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED,
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN, # 将INFO级别也设置为绿色，与成功响应一致
    }

    def format(self, record):
        log_message = super().format(record)
        # 如果是文件输出，不着色
        if config_data['logging']['LOG_TO_FILE']:
            return log_message
        
        # 如果是终端输出，根据级别着色
        levelname = record.levelname
        if levelname in self.COLORS:
            return self.COLORS[levelname] + log_message + Style.RESET_ALL
        return log_message


def setup_logging():
    _logger = logging.getLogger(__name__)
    _logger.setLevel(getattr(logging, config_data['logging']['LOG_LEVEL'].upper(), logging.INFO))

    # 移除所有现有的处理器，避免重复输出
    if _logger.hasHandlers():
        _logger.handlers.clear()

    if config_data['logging']['LOG_TO_FILE']:
        handler = logging.FileHandler(config_data['logging']['LOG_FILE_PATH'], encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')

    handler.setFormatter(formatter)
    _logger.addHandler(handler)
    return _logger


logger = setup_logging()
