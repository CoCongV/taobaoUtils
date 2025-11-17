# Taobao Utils

淘宝工具包，提供 RESTful API 和命令行工具来处理淘宝相关任务。

## 安装

```bash
poetry install
```

## 使用方法

### 启动 RESTful API 服务器

```bash
tb server [--host HOST] [--port PORT] [--debug]
```

### 处理 Excel 文件

```bash
tb process <excel_file_path>
```

## API 接口

- `GET /api/process` - 获取所有处理任务
- `POST /api/process` - 创建新处理任务
- `GET /api/status` - 获取系统状态

## 开发

使用 Poetry 管理依赖:

```bash
# 安装依赖
poetry install

# 添加新依赖
poetry add <package>

# 运行
poetry run tb <command>
```