# Taobao Utils

淘宝工具包，提供 RESTful API 和命令行工具来处理淘宝相关任务。

## 安装

项目使用 Poetry 进行依赖管理。

```bash
# 安装项目依赖
poetry install
```

## 配置

项目通常需要在当前工作目录下包含 `config.toml` 文件以进行配置。以下是一个配置样例：

```toml
# 目标 API URL
TARGET_URL = "https://example.com/api/endpoint"

# Excel 列名映射
URL_COLUMN = "商品链接"
STATUS_COLUMN = "状态"
SEND_TIME_COLUMN = "发送时间"
RESPONSE_COLUMN = "响应内容"

# 成功状态值（当状态为此列值时跳过处理）
STATUS_SUCCESS_VALUE = "是"

# 请求间隔配置
REQUEST_INTERVAL_MINUTES = 8       # 基础间隔（分钟）
RANDOM_INTERVAL_SECONDS_MIN = 2    # 额外随机延迟最小值（秒）
RANDOM_INTERVAL_SECONDS_MAX = 15   # 额外随机延迟最大值（秒）

# Cookie 配置 (可选)
Appname = "your_appname"
Token = "your_token"

# Web 应用配置
[app]
SECRET_KEY = "your-secret-key-here"
# DATABASE_URI = "sqlite:///taobaoutils.db" # 可选，默认使用 sqlite

# 日志配置
[logging]
LOG_LEVEL = "INFO"
LOG_TO_FILE = false
LOG_FILE_PATH = "app.log"

# 调度器服务配置
[scheduler]
SCHEDULER_SERVICE_URL = "http://localhost:8000"

# 请求体模板
[request_payload_template]
some_field = "value"
# linkData 字段用于动态替换 URL 和 ID
linkData = [
    { url = "{url}", num_iid = "" }
]

# 自定义请求头 (可选)
[custom_headers]
User-Agent = "Mozilla/5.0 ..."
```

### Request Payload 模板示例

在 `RequestConfig` 中，`payload` 字段支持使用 JSON 格式的模板。你可以使用 `{placeholder}` 语法来插入动态值。

**可用占位符：**
- `{title}`: 商品标题
- `{product_link}`: 商品链接
- `{product_id}`: 商品ID
- `{stock}`: 库存
- `{listing_code}`: 商家编码
- `{id}`: ProductListing ID
- `{user_id}`: 用户ID

**示例 Payload 模板：**

```json
{
  "sub_user": "12345678",
  "userids": [
    "87654321"
  ],
  "filter_copied": true,
  "copy_type": 1,
  "param_id": "1001",
  "is_search": "0",
  "linkData": [
    {
      "url": "{product_link}",
      "num_iid": "{product_id}"
    }
  ]
}
```

### Request Header 模板示例

`header` 字段也支持 JSON 格式，可以在其中使用占位符。以下是一个配置了各类请求头的示例：

```json
{
  "Host": "example.com",
  "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:145.0) Gecko/20100101 Firefox/145.0",
  "Accept": "application/json, text/plain, */*",
  "Accept-Language": "zh-CN,en-US;q=0.7,en;q=0.3",
  "Accept-Encoding": "gzip, deflate, br, zstd",
  "Content-Type": "application/json",
  "token": "your_fake_token_value",
  "appname": "your_fake_appname",
  "Content-Length": "215",
  "Origin": "https://example.com",
  "DNT": "1",
  "Sec-GPC": "1",
  "Connection": "keep-alive",
  "Referer": "https://example.com/",
  "Cookie": "token=your_fake_token_value; appname=your_fake_appname",
  "Sec-Fetch-Dest": "empty",
  "Sec-Fetch-Mode": "cors",
  "Sec-Fetch-Site": "same-origin",
  "Priority": "u=0"
}
```

## 使用方法

### 启动 API 服务器

启动 Flask API 开发服务器：

```bash
tb serve [--host HOST] [--port PORT]
```
默认运行在 `127.0.0.1:5000`。

### 处理 Excel 文件

使用命令行工具处理 Excel 文件：

```bash
tb process <excel_file_path>
```

该命令会读取指定的 Excel 文件，根据 `config.toml` 中的配置处理每一行数据，并更新状态。

## API 接口

### 认证接口 (Authentication)

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录，获取 access_token
- `POST /api/auth/refresh` - 刷新 access_token
- `GET /api/auth/me` - 获取当前用户信息
- `GET /api/auth/users` - 获取用户列表（可能需要权限）

### API Token 管理

- `GET /api/tokens` - 获取 API Token 列表
- `GET /api/tokens/<int:token_id>` - 获取指定 API Token

### 业务接口 (Product Listings & Tasks)

- `GET /api/product-listings` - 获取产品列表/日志
- `GET /api/product-listings/<int:log_id>` - 获取指定日志详情
- `POST /api/product-listings/upload` - 上传 Excel 文件进行处理
- `POST /api/scheduler/callback` - 调度器回调接口

### 请求配置 (Request Configs)

- `GET /api/request-configs` - 获取请求配置列表
- `GET /api/request-configs/<int:config_id>` - 获取指定请求配置

### 通用说明

大多数业务接口需要在请求头中携带 JWT 令牌：

```
Authorization: Bearer <access_token>
```

## 开发

使用 Poetry 管理依赖:

```bash
# 安装依赖
poetry install

# 添加新依赖
poetry add <package>

# 运行命令
poetry run tb <command>
```