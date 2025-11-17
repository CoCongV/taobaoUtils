import sys
import argparse
import logging
from pathlib import Path
from taobaoutils.app import create_app
from taobaoutils.utils import (
    load_config,
    setup_logging,
    load_excel_data,
    validate_columns,
    process_row,
    save_dataframe
)
import toml
import os
import pandas as pd


# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def start_server(host='127.0.0.1', port=5000, debug=False):
    """启动Flask服务器"""
    logger.info("Starting server on %s:%s", host, port)
    app = create_app()
    app.run(host=host, port=port, debug=debug)


def process_xlsx(file_path):
    """处理XLSX文件"""
    # 这里我们会复用原始main.py中的逻辑来处理Excel文件
    try:
        logger.info("Processing Excel file: %s", file_path)
        
        # 加载配置
        config_data = load_config()
        
        # 更新配置中的文件路径
        config_data['EXCEL_FILE_PATH'] = file_path
        
        # 设置日志记录器
        excel_logger = setup_logging(config_data)
        
        df = load_excel_data(config_data, excel_logger)
        validate_columns(df, config_data, excel_logger)
        
        total_rows = len(df)
        logger.info("Successfully loaded %s rows from '%s'", total_rows, file_path)
        
        # 获取上一次的发送时间
        last_send_time = df[config_data['SEND_TIME_COLUMN']].dropna().max()
        if pd.isna(last_send_time):
            last_send_time = None
        logger.info("Last send time: %s", last_send_time)
        
        # 遍历 DataFrame 的每一行
        processed_count = 0
        for index, row in df.iterrows():
            new_last_send_time, processed = process_row(
                df, index, row, last_send_time, config_data, excel_logger)
            if processed:
                last_send_time = new_last_send_time
                save_dataframe(df, index, config_data, excel_logger)  # 每次处理完一行就保存
                processed_count += 1
                
        logger.info("Processed %s rows. All done.", processed_count)
        
    except Exception as e:
        logger.error("Error processing Excel file: %s", e)
        sys.exit(1)


def main():
    """主CLI入口点"""
    parser = argparse.ArgumentParser(description='Taobao Utils CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # 服务器命令
    server_parser = subparsers.add_parser('server', help='Start the REST API server')
    server_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    server_parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    server_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # 处理Excel文件命令
    process_parser = subparsers.add_parser('process', help='Process Excel file')
    process_parser.add_argument('file', help='Path to the Excel file to process')
    
    args = parser.parse_args()
    
    if args.command == 'server':
        start_server(args.host, args.port, args.debug)
    elif args.command == 'process':
        if not Path(args.file).exists():
            logger.error("Error: File '%s' does not exist", args.file)
            sys.exit(1)
        process_xlsx(args.file)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()