# -*- coding: utf-8 -*-

import sys
from taobaoutils.utils import (
    load_config,
    setup_logging,
    load_excel_data,
    validate_columns,
    process_row,
    save_dataframe
)
import pandas as pd

# 加载配置
config_data = load_config()

# 配置日志
logger = setup_logging(config_data)


def main():
    """
    主函数，执行整个流程。
    """
    logger.info("开始执行脚本...")

    df = load_excel_data(config_data, logger)
    validate_columns(df, config_data, logger)

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
            df, index, row, last_send_time, config_data, logger)
        if processed:
            last_send_time = new_last_send_time
            save_dataframe(df, index, config_data, logger)  # 每次处理完一行就保存

    logger.info("\n所有行处理完毕。脚本执行结束。")


if __name__ == "__main__":
    main()