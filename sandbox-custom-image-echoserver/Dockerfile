# ============================================
# Custom font 扩展镜像
# 基于 sandbox-code-interpreter 镜像进行扩展
# ============================================

# 基于sandbox-code-interpreter 镜像
FROM  serverless-registry.cn-hangzhou.cr.aliyuncs.com/functionai/sandbox-code-interpreter:v0.9.29

LABEL layer="echoserver-extension"
LABEL description="Echo Server extension based on All-in-One"
LABEL maintainer="Your Team"

USER root

# 复制 Echo Server Python 脚本
COPY echo_server.py /usr/local/bin/echo_server.py
RUN chmod +x /usr/local/bin/echo_server.py

# 复制 Process Compose 配置文件
# entrypoint.sh 会自动扫描 /etc/sandbox/config/ 目录下所有 process-compose.*.yaml 文件
COPY config/process-compose.echoserver.yaml /etc/sandbox/config/process-compose.echoserver.yaml

# 复制 Nginx 配置文件
# entrypoint.sh 会自动扫描并复制 /etc/sandbox/config/nginx/ 目录下的配置
RUN mkdir -p /etc/sandbox/config/nginx/http.d /etc/sandbox/config/nginx/conf.d
COPY config/nginx-echoserver-upstream.conf /etc/sandbox/config/nginx/http.d/echoserver-upstream.conf
COPY config/nginx-echoserver-routes.conf /etc/sandbox/config/nginx/conf.d/echoserver-routes.conf

# 环境变量
ENV ECHO_SERVER_HOST=0.0.0.0 \
    ECHO_SERVER_PORT=9000

# 主端口 5000 已经在 all-in-one 中暴露


# entrypoint.sh 会自动加载所有 process-compose.*.yaml 文件
# 使用入口脚本启动
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["process-compose", "up", "--tui=false", "--no-server"]

