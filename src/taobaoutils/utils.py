import json
from typing import Optional

import requests

from taobaoutils import config_data, logger


def send_request(target_url, payload, cookies: Optional[str] = None):
    """
    向目标 URL 发送 POST 请求。

    :param target_url: 请求的目标 URL。
    :param payload: 要发送的 JSON 数据。
    :param cookies: 可选的 Cookie 字符串，例如 "appname=value; token=value"。
    :return: 元组 (bool, str)，表示 (是否成功, 响应内容)
    """
    headers = {
        'Content-Type': 'application/json'
    }
    # 合并自定义请求头
    if 'custom_headers' in config_data and isinstance(config_data['custom_headers'], dict):
        headers.update(config_data['custom_headers'])

    # 添加 Cookie 头
    if cookies:
        headers['Cookie'] = cookies
        logger.info("已添加传入的 Cookie 头: %s", headers['Cookie'])
    else:
        appname_cookie = config_data.get('Appname')
        token_cookie = config_data.get('Token')

        if appname_cookie and token_cookie:
            headers['Cookie'] = f"appname={appname_cookie}; token={token_cookie}"
            logger.info("已添加从 config_data 构建的 Cookie 头: %s", headers['Cookie'])
        elif appname_cookie or token_cookie:
            logger.warning("config_data 中只配置了部分 Cookie 值 (Appname 或 Token)，Cookie 头未完整添加。")
        else:
            logger.info("config_data 中未配置 Cookie 值，未添加 Cookie 头。")

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
