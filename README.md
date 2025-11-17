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

### 认证接口

- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录，返回JWT令牌
- `POST /api/refresh` - 刷新JWT令牌
- `GET /api/user` - 获取当前用户信息

### 业务接口

- `GET /api/process` - 获取所有处理任务
- `POST /api/process` - 创建新处理任务
- `GET /api/status` - 获取系统状态

所有业务接口都需要在请求头中提供JWT令牌：
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

# 运行
poetry run tb <command>
```