# -*- coding: utf-8 -*-

import time
import pandas as pd
import requests
import json
import sys
import random
import logging
import toml  # Import the toml library
import os  # Import the os module
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init

# Initialize Colorama for specific colored output (not for general logging)
init()

# 加载配置
try:
    # config.toml 应该位于当前工作目录
    config_path = Path(os.getcwd()) / "config.toml"
    if not config_path.exists():
        raise FileNotFoundError(f"config.toml 文件未找到于: {config_path}")
    config_data = toml.load(config_path)
except Exception as e:
    print(f"错误：加载 config.toml 文件失败: {e}")
    sys.exit(1)


# 自定义日志格式化器，用于彩色输出
class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED,
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,  # 将INFO级别也设置为绿色，与成功响应一致
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


# 配置日志
def setup_logging():
    logger = logging.getLogger(__name__)
    logger.setLevel(
        getattr(logging, config_data['logging']['LOG_LEVEL'].upper(), logging.INFO))

    # 移除所有现有的处理器，避免重复输出
    if logger.hasHandlers():
        logger.handlers.clear()

    if config_data['logging']['LOG_TO_FILE']:
        handler = logging.FileHandler(
            config_data['logging']['LOG_FILE_PATH'], encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s')
    else:
        handler = logging.StreamHandler(sys.stdout)
        formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s')

    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = setup_logging()


def send_request(target_url, payload):
    """
    向目标 URL 发送 POST 请求。

    :param target_url: 请求的目标 URL。
    :param payload: 要发送的 JSON 数据。
    :return: 元组 (bool, str)，表示 (是否成功, 响应内容)
    """
    headers = {
        'Content-Type': 'application/json'
    }
    # 合并自定义请求头
    if 'custom_headers' in config_data and isinstance(config_data['custom_headers'], dict):
        headers.update(config_data['custom_headers'])

    response_content = ""
    try:
        logger.info("准备发送的请求体: %s", json.dumps(
            payload, indent=2, ensure_ascii=False))
        response = requests.post(target_url, data=json.dumps(
            payload), headers=headers, timeout=30)
        response.raise_for_status()  # 如果请求失败 (状态码 4xx 或 5xx), 则抛出异常

        logger.info("成功发送请求。\n状态码: %s", response.status_code)
        try:
            response_json = response.json()
            response_content = json.dumps(
                response_json, indent=2, ensure_ascii=False)
            if 'code' in response_json:
                if response_json['code'] == 800:
                    logger.info("响应内容: %s", response_content)  # 成功响应，INFO级别
                else:
                    # 非800响应，ERROR级别
                    logger.error("响应内容: %s", response_content)
            else:
                logger.info("响应内容: %s", response_content)
        except json.JSONDecodeError:
            response_content = response.text
            logger.warning("响应内容不是有效的 JSON 格式: %s", response_content)
        return True, response_content

    except requests.exceptions.RequestException as e:
        response_content = str(e)
        logger.error("发送请求时发生错误: %s", response_content)
        return False, response_content


def load_excel_data():
    """
    加载 Excel 文件，确保必要的列存在，并处理时间列。
    :return: pandas.DataFrame
    """
    try:
        df = pd.read_excel(config_data['EXCEL_FILE_PATH'], engine='openpyxl')
        # 确保必要的列存在，如果不存在则创建
        for col in [config_data['STATUS_COLUMN'], config_data['SEND_TIME_COLUMN'], config_data['RESPONSE_COLUMN']]:
            if col not in df.columns:
                df[col] = ''
        # 将时间列转换为 datetime 对象，以便进行比较
        df[config_data['SEND_TIME_COLUMN']] = pd.to_datetime(
            df[config_data['SEND_TIME_COLUMN']], errors='coerce')
        return df
    except FileNotFoundError:
        logger.error("错误：找不到 Excel 文件 '%s'。\n请确保 config.toml 中的 EXCEL_FILE_PATH 配置正确。",
                     config_data['EXCEL_FILE_PATH'])
        sys.exit(1)
    except Exception as e:
        logger.error("读取 Excel 文件时发生错误: %s", e)
        sys.exit(1)


def validate_columns(df):
    """
    验证 DataFrame 中是否存在所有必需的列。
    :param df: pandas.DataFrame
    """
    required_columns = [config_data['URL_COLUMN'], config_data['STATUS_COLUMN'],
                        config_data['SEND_TIME_COLUMN'], config_data['RESPONSE_COLUMN']]
    if not all(col in df.columns for col in required_columns):
        logger.error("错误：Excel 文件必须包含以下列: %s", ', '.join(required_columns))
        sys.exit(1)


def save_dataframe(df, index):
    """
    保存 DataFrame 到 Excel 文件。
    :param df: pandas.DataFrame
    :param index: 当前处理的行索引，用于日志输出
    """
    try:
        # 保存回 Excel 文件，先将时间列格式化为字符串
        df_to_save = df.copy()
        df_to_save[config_data['SEND_TIME_COLUMN']
                   ] = df_to_save[config_data['SEND_TIME_COLUMN']].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_to_save.to_excel(
            config_data['EXCEL_FILE_PATH'], index=False, engine='openpyxl')
        logger.info("成功更新第 %s 行的状态、发送时间和响应内容，并已保存到文件。", index + 1)
    except Exception as e:
        logger.error("错误：更新 Excel 文件失败: %s", e)
        logger.error("请检查文件是否被其他程序占用。")


def process_row(df, index, row, last_send_time):
    """
    处理 DataFrame 中的单行数据。
    :param df: pandas.DataFrame
    :param index: 当前行索引
    :param row: 当前行数据
    :param last_send_time: 上一次发送请求的时间
    :return: (datetime, bool) 更新后的 last_send_time 和是否处理了当前行
    """
    url = row[config_data['URL_COLUMN']]
    status = row[config_data['STATUS_COLUMN']]

    logger.info("\n--- 处理第 %s/%s 行 ---", index + 1, len(df))

    # 检查是否需要处理
    if pd.isna(url) or not str(url).strip():
        logger.info("商品链接为空，跳过。")
        return last_send_time, False

    url = str(url).strip()  # 确保URL是字符串并去除空白

    if str(status).strip() == config_data['STATUS_SUCCESS_VALUE']:
        logger.info("状态已为 '%s'，跳过。", config_data['STATUS_SUCCESS_VALUE'])
        return last_send_time, False

    # 动态计算等待时间
    if last_send_time:
        target_interval = timedelta(
            minutes=config_data['REQUEST_INTERVAL_MINUTES'])
        elapsed_time = datetime.now() - last_send_time

        if elapsed_time < target_interval:
            wait_seconds = (target_interval - elapsed_time).total_seconds()
            # 增加随机秒数
            random_seconds = random.uniform(
                config_data['RANDOM_INTERVAL_SECONDS_MIN'], config_data['RANDOM_INTERVAL_SECONDS_MAX'])
            total_wait = wait_seconds + random_seconds

            logger.info("距离上次发送时间 %.0f 秒，未满 %.0f 秒。", elapsed_time.total_seconds(
            ), target_interval.total_seconds())
            logger.info("将等待 %.2f 秒 (含随机延迟)...", total_wait)
            time.sleep(total_wait)

    # 构建请求体并发送请求
    payload = config_data['request_payload_template']

    if "linkData" in payload and isinstance(payload["linkData"], list) and payload["linkData"]:
        num_iid = ""
        try:
            if "id=" in url:
                num_iid = url.split("id=")[1].split("&")[0]
        except Exception:
            logger.warning("无法从URL '%s' 中提取商品ID。", url)

        # Deep copy the payload to avoid modifying the template directly
        # Simple deep copy for dict/list structure
        current_payload = json.loads(json.dumps(payload))

        # Replace placeholder in URL
        if current_payload["linkData"][0]["url"] == "{url}":
            current_payload["linkData"][0]["url"] = url

        current_payload["linkData"][0]["num_iid"] = num_iid if num_iid else current_payload["linkData"][0].get(
            "num_iid", "")
    else:
        current_payload = payload  # Use payload directly if no linkData manipulation needed

    # 发送请求并记录当前时间
    current_time = datetime.now()
    success, response_text = send_request(
        config_data['TARGET_URL'], current_payload)

    # 更新 DataFrame
    df.loc[index, config_data['SEND_TIME_COLUMN']
           ] = current_time.strftime('%Y-%m-%d %H:%M:%S')
    df.loc[index, config_data['RESPONSE_COLUMN']] = response_text
    if success:
        df.loc[index, config_data['STATUS_COLUMN']
               ] = config_data['STATUS_SUCCESS_VALUE']

    return current_time, True


def main():
    """
    主函数，执行整个流程。
    """
    logger.info("开始执行脚本...")

    df = load_excel_data()
    validate_columns(df)

    total_rows = len(df)
    logger.info("从 '%s' 文件中成功读取 %s 行数据。",
                config_data['EXCEL_FILE_PATH'], total_rows)

    # 获取上一次的发送时间
    last_send_time = df[config_data['SEND_TIME_COLUMN']].dropna().max()
    if pd.isna(last_send_time):
        last_send_time = None
    logger.info("上一次有记录的发送时间: %s", last_send_time)

    # 遍历 DataFrame 的每一行
    for index, row in df.iterrows():
        new_last_send_time, processed = process_row(
            df, index, row, last_send_time)
        if processed:
            last_send_time = new_last_send_time
            save_dataframe(df, index)  # 每次处理完一行就保存

    logger.info("\n所有行处理完毕。脚本执行结束。")


if __name__ == "__main__":
    main()
