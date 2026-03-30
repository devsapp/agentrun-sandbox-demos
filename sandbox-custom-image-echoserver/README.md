# Echo Server 扩展示例

这是一个基于 sandbox-code-interpreter 镜像的扩展示例，展示了如何添加自定义服务。

## 功能特性

1. **Python Echo Server**：一个简单的 HTTP echo 服务器，GET 请求返回 "ok\n"
2. **Nginx 反向代理**：通过 nginx 将 `/echo` 路径代理到 echo server
3. **Process Compose 集成**：使用 process-compose 管理 echo server 进程
4. **简单扩展**：只需将配置文件放在正确位置，无需修改基础镜像

## 文件结构

```
sandbox-custom-image-echoserver/
├── Dockerfile                          # 扩展镜像定义
├── echo_server.py                     # Python echo server 实现
├── README.md                          # 本文档
└── config/
    ├── process-compose.echoserver.yaml # Process Compose 配置
    ├── nginx-echoserver-upstream.conf  # Nginx upstream 配置
    └── nginx-echoserver-routes.conf    # Nginx 路由配置
```

## 工作原理

扩展镜像通过以下方式集成到 sandbox-code-interpreter：

1. **Process Compose 配置**：将 `process-compose.*.yaml` 文件复制到 `/etc/sandbox/config/` 目录，服务会自动启动
2. **Nginx Upstream 配置**：将 `nginx-*-upstream.conf` 文件复制到 `/etc/sandbox/config/nginx/http.d/` 目录，entrypoint.sh 会自动复制到 nginx 配置目录
3. **Nginx 路由配置**：将 `nginx-*-routes.conf` 文件复制到 `/etc/sandbox/config/nginx/conf.d/` 目录，entrypoint.sh 会自动扫描并复制到 nginx 配置目录

## 构建镜像

```bash
cd sandbox-custom-image-echoserver

# 构建 echoserver 扩展镜像
docker build -f Dockerfile -t echoserver-extension:latest .
```

## 运行容器

```bash
docker run --rm \
  -p 5000:5000 \
  --name echoserver-test \
  echoserver-extension:latest
```

## 测试服务

### 1. 测试 Echo Server（通过 Nginx 代理）

```bash
# 发送 GET 请求
curl http://localhost:5000/echo
# 返回: ok
```

## 如何扩展 sandbox-code-interpreter 镜像

基于此示例，你可以轻松添加自己的服务。以下是完整的扩展步骤：

### 步骤 1: 创建项目目录

```bash
mkdir -p your-service
cd your-service
```

### 步骤 2: 创建服务脚本

创建你的服务脚本（Python、Node.js、Go 等），例如 `your_service.py`：

```python
#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(b'ok\n')

if __name__ == '__main__':
    port = int(os.environ.get('YOUR_SERVICE_PORT', 9001))
    host = os.environ.get('YOUR_SERVICE_HOST', '0.0.0.0')
    server = HTTPServer((host, port), Handler)
    print(f"[your-service] Starting server on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[your-service] Shutting down server...")
        server.shutdown()
```

### 步骤 3: 创建 Process Compose 配置

创建 `config/process-compose.your-service.yaml`：

```yaml
version: "0.5"

log_level: info

environment:
  - PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

processes:
  your-service:
    command: "python3 /usr/local/bin/your_service.py"
    availability:
      restart: "always"
      backoff_seconds: 2
      max_restarts: 5
    readiness_probe:
      # HTTP 健康检查（推荐）
      http_get:
        host: localhost
        port: ${YOUR_SERVICE_PORT:-9001}
        path: /
      initial_delay_seconds: 1
      period_seconds: 10
      timeout_seconds: 2
      success_threshold: 1
      failure_threshold: 3
    environment:
      - YOUR_SERVICE_HOST=0.0.0.0
      - YOUR_SERVICE_PORT=9001
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    log_configuration:
      disable_json: true
      no_metadata: false
      add_timestamp: true
      timestamp_format: "2006-01-02 15:04:05.000"
      fields_to_append:
        - level=INFO
```

### 步骤 4: 创建 Nginx 配置

#### 4.1 创建 Upstream 配置

创建 `config/nginx-your-service-upstream.conf`：

```nginx
# Your Service Upstream 定义
upstream your_service {
    server localhost:9001;
    keepalive 16;
}
```

#### 4.2 创建路由配置

创建 `config/nginx-your-service-routes.conf`：

```nginx
# Your Service Nginx 路由配置
location /your-service {
    proxy_pass http://your_service;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
    
    # 支持 WebSocket（如果需要）
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
}
```

### 步骤 5: 创建 Dockerfile

创建 `Dockerfile`：

```dockerfile
# ============================================
# Custom font 扩展镜像
# 基于 sandbox-code-interpreter 镜像进行扩展
# ============================================

# 基于 sandbox-code-interpreter 镜像
FROM serverless-registry.cn-hangzhou.cr.aliyuncs.com/functionai/sandbox-code-interpreter:v0.9.29

LABEL layer="your-service-extension"
LABEL description="Your Service extension based on sandbox-code-interpreter"
LABEL maintainer="Your Team"

USER root

# 复制服务脚本
COPY your_service.py /usr/local/bin/your_service.py
RUN chmod +x /usr/local/bin/your_service.py

# 复制 Process Compose 配置文件
# entrypoint.sh 会自动扫描 /etc/sandbox/config/ 目录下所有 process-compose.*.yaml 文件
COPY config/process-compose.your-service.yaml /etc/sandbox/config/process-compose.your-service.yaml

# 复制 Nginx 配置文件
# entrypoint.sh 会自动扫描并复制 /etc/sandbox/config/nginx/ 目录下的配置
RUN mkdir -p /etc/sandbox/config/nginx/http.d /etc/sandbox/config/nginx/conf.d
COPY config/nginx-your-service-upstream.conf /etc/sandbox/config/nginx/http.d/your-service-upstream.conf
COPY config/nginx-your-service-routes.conf /etc/sandbox/config/nginx/conf.d/your-service-routes.conf

# 环境变量
ENV YOUR_SERVICE_HOST=0.0.0.0 \
    YOUR_SERVICE_PORT=9001

# 主端口 5000 已经在基础镜像中暴露

# entrypoint.sh 会自动加载所有 process-compose.*.yaml 文件
# 使用入口脚本启动
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["process-compose", "up", "--tui=false", "--no-server"]
```

### 步骤 6: 构建和运行

```bash
# 构建镜像
docker build -f Dockerfile -t your-service-extension:latest .

# 运行容器
docker run -d \
  -p 5000:5000 \
  --name your-service-test \
  your-service-extension:latest

# 测试服务
curl http://localhost:5000/your-service
```

## 配置说明

### Process Compose 配置

`process-compose.*.yaml` 文件定义了：
- **服务启动命令**：服务如何启动
- **健康检查配置**：用于 process-compose 判断服务是否就绪
- **环境变量**：服务运行所需的环境变量
- **日志配置**：日志格式和输出方式

### Nginx 配置

#### Upstream 配置（`nginx-*-upstream.conf`）

定义后端服务地址，在 Dockerfile 中复制到 `/etc/sandbox/config/nginx/http.d/`。

```nginx
upstream your_service {
    server localhost:9001;  # 服务内部端口
    keepalive 16;
}
```

#### 路由配置（`nginx-*-routes.conf`）

定义 URL 路径到 upstream 的映射，在 Dockerfile 中复制到 `/etc/sandbox/config/nginx/conf.d/`，entrypoint.sh 会自动扫描并复制到 nginx 配置目录。

**基本路由配置：**

```nginx
location /your-service {
    proxy_pass http://your_service;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}
```

**使用 rewrite 规则示例：**

如果需要重写 URL 路径，可以使用 `rewrite` 指令。例如，将 `/api/v1/echo` 重写为 `/echo` 后转发到后端服务：

```nginx
location /api/v1/echo {
    # 重写 URL：将 /api/v1/echo 重写为 /echo
    rewrite ^/api/v1/echo(.*)$ /echo$1 break;
    
    proxy_pass http://echoserver;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

**rewrite 指令说明：**

- `rewrite ^/api/v1/echo(.*)$ /echo$1 break;`
  - `^/api/v1/echo(.*)$`：匹配以 `/api/v1/echo` 开头的路径，`(.*)` 捕获后续部分
  - `/echo$1`：重写为目标路径，`$1` 是捕获的后续部分
  - `break`：停止处理后续 rewrite 规则，直接使用重写后的 URI 进行 proxy_pass

**更多 rewrite 示例：**

```nginx
# 示例 1: 移除路径前缀
# /api/echo/xxx -> /echo/xxx
location /api/echo {
    rewrite ^/api/echo(.*)$ /echo$1 break;
    proxy_pass http://echoserver;
}

# 示例 2: 添加路径前缀
# /echo -> /v1/echo
location /echo {
    rewrite ^/echo(.*)$ /v1/echo$1 break;
    proxy_pass http://echoserver;
}

# 示例 3: 路径转换
# /old-path/xxx -> /new-path/xxx
location /old-path {
    rewrite ^/old-path(.*)$ /new-path$1 break;
    proxy_pass http://echoserver;
}
```

## 配置文件命名规范

为了保持一致性，建议使用以下命名规范：

1. **Process Compose 配置**：`process-compose.<service-name>.yaml`
   - 示例：`process-compose.echoserver.yaml`

2. **Nginx Upstream 配置**：`nginx-<service-name>-upstream.conf`
   - 示例：`nginx-echoserver-upstream.conf`

3. **Nginx 路由配置**：`nginx-<service-name>-routes.conf`
   - 示例：`nginx-echoserver-routes.conf`

## 注意事项

1. **端口冲突**：确保自定义服务的端口不与现有服务冲突
   - Code Interpreter: 5001
   - Browser Tool: 3000
   - 建议使用 9000+ 端口范围

2. **健康检查**：在 process-compose 配置中可以使用进程检查（`exec`）或 HTTP 检查（`http_get`）。HTTP 检查更可靠，因为它验证服务是否真正可响应请求。如果服务监听特定端口，建议配置 `http_get` 检查，即使只是检查根路径 `/`。

3. **日志格式**：建议使用与 process-compose 兼容的日志格式，便于统一管理

4. **服务命名**：在 process-compose 配置中，服务名称（`processes` 下的 key）应该唯一，避免与其他服务冲突

5. **Nginx 路由路径**：确保路由路径（`location` 后的路径）不与现有服务冲突
   - Code Interpreter: `/`, `/contexts`, `/execute`, 等
   - Browser Tool: `/ws/automation`, `/recordings`, 等

## 故障排查

### 服务未启动

```bash
# 检查 process-compose 日志
docker logs your-service-test | grep your-service

# 检查服务是否在运行
docker exec your-service-test pgrep -f your_service.py

# 检查 process-compose 配置是否加载
docker exec your-service-test ls -la /etc/sandbox/config/process-compose.*.yaml
```

### Nginx 配置错误

```bash
# 测试 nginx 配置
docker exec your-service-test /usr/local/openresty/nginx/sbin/nginx -t

# 查看 nginx 错误日志
docker exec your-service-test tail -f /var/log/nginx/error.log

# 检查 upstream 配置源文件（源目录）
docker exec your-service-test cat /etc/sandbox/config/nginx/http.d/your-service-upstream.conf

# 检查路由配置源文件（源目录）
docker exec your-service-test cat /etc/sandbox/config/nginx/conf.d/your-service-routes.conf

# 检查路由配置是否已复制到 nginx 配置目录（目标目录）
docker exec your-service-test cat /usr/local/openresty/nginx/conf/conf.d/your-service-routes.conf
```

### 路由不工作

```bash
# 检查 nginx 配置是否已加载
docker exec your-service-test ls -la /usr/local/openresty/nginx/conf/conf.d/

# 检查服务是否可达
docker exec your-service-test curl http://localhost:9001/

# 检查 nginx 访问日志
docker exec your-service-test tail -f /var/log/nginx/access.log
```

## 参考

- [Process Compose 文档](https://github.com/F1bonacc1/process-compose)
- [Nginx 配置文档](https://nginx.org/en/docs/)
