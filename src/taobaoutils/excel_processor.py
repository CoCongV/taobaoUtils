mport json
import random
import sys
import time
from datetime import datetime, timedelta

import pandas as pd
from colorama import init

from taobaoutils import config_data, logger
from taobaoutils.utils import send_request


# Initialize Colorama for specific colored output (not for general logging)
init()


def load_excel_data(excel_file_path):
    """
    加载 Excel 文件，确保必要的列存在，并处理时间列。
    :param excel_file_path: 要加载的 Excel 文件路径
    :return: pandas.DataFrame
    """
    try:
        df = pd.read_excel(excel_file_path, engine="openpyxl")
        # 确保必要的列存在，如果不存在则创建
        for col in [
            config_data["STATUS_COLUMN"],
            config_data["SEND_TIME_COLUMN"],
            config_data["RESPONSE_COLUMN"],
        ]:
            if col not in df.columns:
                df[col] = ""
        # 将时间列转换为 datetime 对象，以便进行比较
        df[config_data["SEND_TIME_COLUMN"]] = pd.to_datetime(
            df[config_data["SEND_TIME_COLUMN"]], errors="coerce"
        )
        return df
    except FileNotFoundError:
        logger.error(
            "错误：找不到 Excel 文件 '%s'。\n请确保路径正确。", excel_file_path
        )
        sys.exit(1)
    except Exception as e:
        logger.error("读取 Excel 文件时发生错误: %s", e)
        sys.exit(1)


def validate_columns(df):
    """
    验证 DataFrame 中是否存在所有必需的列。
    :param df: pandas.DataFrame
    """
    required_columns = [
        config_data["URL_COLUMN"],
        config_data["STATUS_COLUMN"],
        config_data["SEND_TIME_COLUMN"],
        config_data["RESPONSE_COLUMN"],
    ]
    if not all(col in df.columns for col in required_columns):
        logger.error("错误：Excel 文件必须包含以下列: %s", ", ".join(required_columns))
        sys.exit(1)


def save_dataframe(df, index, excel_file_path):
    """
    保存 DataFrame 到 Excel 文件。
    :param df: pandas.DataFrame
    :param index: 当前处理的行索引，用于日志输出
    :param excel_file_path: 要保存到的 Excel 文件路径
    """
    try:
        # 保存回 Excel 文件，先将时间列格式化为字符串
        df_to_save = df.copy()
        df_to_save[config_data["SEND_TIME_COLUMN"]] = df_to_save[
            config_data["SEND_TIME_COLUMN"]
        ].dt.strftime("%Y-%m-%d %H:%M:%S")
        df_to_save.to_excel(excel_file_path, index=False, engine="openpyxl")
        logger.info(
            "成功更新第 %s 行的状态、发送时间和响应内容，并已保存到文件。", index + 1
        )
    except Exception as e:
        logger.error("错误：更新 Excel 文件失败: %s", e)
        logger.error("请检查文件是否被其他程序占用。")


def process_row_logic(df, index, row, last_send_time):
    """
    处理 DataFrame 中的单行数据。
    :param df: pandas.DataFrame
    :param index: 当前行索引
    :param row: 当前行数据
    :param last_send_time: 上一次发送请求的时间
    :return: (datetime, bool) 更新后的 last_send_time 和是否处理了当前行
    """
    url = row[config_data["URL_COLUMN"]]
    status = row[config_data["STATUS_COLUMN"]]

    logger.info("\n--- 处理第 %s/%s 行 ---", index + 1, len(df))

    # 检查是否需要处理
    if pd.isna(url) or not str(url).strip():
        logger.info("商品链接为空，跳过。")
        return last_send_time, False

    url = str(url).strip()  # 确保URL是字符串并去除空白

    if str(status).strip() == config_data["STATUS_SUCCESS_VALUE"]:
        logger.info("状态已为 '%s'，跳过。", config_data["STATUS_SUCCESS_VALUE"])
        return last_send_time, False

    # 动态计算等待时间
    if last_send_time:
        target_interval = timedelta(minutes=config_data["REQUEST_INTERVAL_MINUTES"])
        elapsed_time = datetime.now() - last_send_time

        if elapsed_time < target_interval:
            wait_seconds = (target_interval - elapsed_time).total_seconds()
            # 增加随机秒数
            random_seconds = random.uniform(
                config_data["RANDOM_INTERVAL_SECONDS_MIN"],
                config_data["RANDOM_INTERVAL_SECONDS_MAX"],
            )
            total_wait = wait_seconds + random_seconds

            logger.info(
                "距离上次发送时间 %.0f 秒，未满 %.0f 秒。",
                elapsed_time.total_seconds(),
                target_interval.total_seconds(),
            )
            logger.info("将等待 %.2f 秒 (含随机延迟)...", total_wait)
            time.sleep(total_wait)

    # 构建请求体并发送请求
    payload = config_data["request_payload_template"]

    if (
        "linkData" in payload
        and isinstance(payload["linkData"], list)
        and payload["linkData"]
    ):
        num_iid = ""
        try:
            if "id=" in url:
                num_iid = url.split("id=")[1].split("&")[0]
        except Exception:
            logger.warning("无法从URL '%s' 中提取商品ID。", url)

        # Deep copy the payload to avoid modifying the template directly
        current_payload = json.loads(
            json.dumps(payload)
        )  # Simple deep copy for dict/list structure

        # Replace placeholder in URL
        if current_payload["linkData"][0]["url"] == "{url}":
            current_payload["linkData"][0]["url"] = url

        current_payload["linkData"][0]["num_iid"] = (
            num_iid if num_iid else current_payload["linkData"][0].get("num_iid", "")
        )
    else:
        current_payload = (
            payload  # Use payload directly if no linkData manipulation needed
        )

    # 发送请求并记录当前时间
    current_time = datetime.now()
    success, response_text = send_request(config_data["TARGET_URL"], current_payload)

    # 更新 DataFrame
    df.loc[index, config_data["SEND_TIME_COLUMN"]] = current_time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df.loc[index, config_data["RESPONSE_COLUMN"]] = response_text
    if success:
        df.loc[index, config_data["STATUS_COLUMN"]] = config_data[
            "STATUS_SUCCESS_VALUE"
        ]

    return current_time, True


def process_excel_main(excel_file_path):
    """
    主函数，执行整个流程。
    :param excel_file_path: 要处理的 Excel 文件路径
    """
    logger.info("开始执行脚本...")

    df = load_excel_data(excel_file_path)
    validate_columns(df)

    total_rows = len(df)
    logger.info("从 '%s' 文件中成功读取 %s 行数据。", excel_file_path, total_rows)

    # 获取上一次的发送时间
    last_send_time = df[config_data["SEND_TIME_COLUMN"]].dropna().max()
    if pd.isna(last_send_time):
        last_send_time = None
    logger.info("上一次有记录的发送时间: %s", last_send_time)

    # 遍历 DataFrame 的每一行
    for index, row in df.iterrows():
        new_last_send_time, processed = process_row_logic(
            df, index, row, last_send_time
        )
        if processed:
            last_send_time = new_last_send_time
            save_dataframe(df, index, excel_file_path)  # 每次处理完一行就保存

    logger.info("\n所有行处理完毕。脚本执行结束。\n")


if __name__ == "__main__":
    # For direct execution, provide a dummy path or handle it differently
    # In CLI context, this will be called with a path
    process_excel_main("dummy_path.xlsx")
