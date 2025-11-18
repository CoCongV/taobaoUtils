# -*- coding: utf-8 -*-

import json
import logging
import random
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import requests
from colorama import Fore, Style, init

from taobaoutils import config_data, logger
from taobaoutils.utils import (
    load_excel_data,
    process_row_logic,  # Renamed to avoid conflict with process_row in this file
    save_dataframe,
    validate_columns,
)

# Initialize Colorama for specific colored output (not for general logging)
init()


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
        logger.info("准备发送的请求体: %s", json.dumps(payload, indent=2, ensure_ascii=False))
        response = requests.post(target_url, data=json.dumps(payload), headers=headers, timeout=30)
        response.raise_for_status()  # 如果请求失败 (状态码 4xx 或 5xx), 则抛出异常
        
        logger.info("成功发送请求.\n状态码: %s", response.status_code)
        try:
            response_json = response.json()
            response_content = json.dumps(response_json, indent=2, ensure_ascii=False)
            if 'code' in response_json:
                if response_json['code'] == 800:
                    logger.info("响应内容: %s", response_content) # 成功响应，INFO级别
                else:
                    logger.error("响应内容: %s", response_content) # 非800响应，ERROR级别
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


def process_excel_main(excel_file_path):
    """
    主函数，执行整个流程。
    :param excel_file_path: 要处理的 Excel 文件路径
    """
    logger.info("开始执行脚本...")

    df = load_excel_data(config_data, logger, excel_file_path)
    validate_columns(df, config_data, logger)

    total_rows = len(df)
    logger.info("从 '%s' 文件中成功读取 %s 行数据。", excel_file_path, total_rows)

    # 获取上一次的发送时间
    last_send_time = df[config_data['SEND_TIME_COLUMN']].dropna().max()
    if pd.isna(last_send_time):
        last_send_time = None
    logger.info("上一次有记录的发送时间: %s", last_send_time)

    # 遍历 DataFrame 的每一行
    for index, row in df.iterrows():
        new_last_send_time, processed = process_row_logic(
            df, index, row, last_send_time, config_data, logger, send_request)
        if processed:
            last_send_time = new_last_send_time
            save_dataframe(df, index, config_data, logger, excel_file_path) # 每次处理完一行就保存

    logger.info("\n所有行处理完毕。脚本执行结束。\n")


if __name__ == "__main__":
    # For direct execution, provide a dummy path or handle it differently
    # In CLI context, this will be called with a path
    process_excel_main("dummy_path.xlsx") 
