# Taobao Utils

淘宝工具包，提供 RESTful API 和命令行工具来处理淘宝相关任务。

## 安装

项目使用 Poetry 进行依赖管理。

```bash
# 安装项目依赖
poetry install
```

## 配置

项目通常需要在当前工作目录下包含 `config.toml` 文件以进行配置（如 Excel 列名映射、数据库路径等）。

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