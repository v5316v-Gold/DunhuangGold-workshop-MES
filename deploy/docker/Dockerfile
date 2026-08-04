# 贵金属车间 ERP — Odoo 17 镜像
# 基础镜像: Odoo 17.0 官方
FROM odoo:17.0

# 维护者
LABEL maintainer="ERP-Architect-01 <gold-mes@internal>" \
      version="17.0.1.0.0" \
      description="贵金属首饰加工车间 ERP - 油压 + 失蜡铸造"

# 切换 root 安装依赖
USER root

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip \
        python3-dev \
        build-essential \
        libldap2-dev \
        libsasl2-dev \
        libssl-dev \
        libxml2-dev \
        libxmlsec1-dev \
        libxslt1-dev \
        libjpeg-dev \
        zlib1g-dev \
        libpq-dev \
        locales \
        fonts-noto-cjk \
        fonts-wqy-microhei \
        node-less \
        npm \
        && rm -rf /var/lib/apt/lists/*

# 中文 locale
RUN sed -i '/zh_CN.UTF-8/s/^# //g' /etc/locale.gen && locale-gen
ENV LANG=zh_CN.UTF-8 \
    LANGUAGE=zh_CN:zh \
    LC_ALL=zh_CN.UTF-8

# Python 依赖(预留)
# COPY requirements.txt /tmp/requirements.txt
# RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

# 复制本模块
COPY --chown=odoo:odoo addons/ /mnt/odoo/addons/

# MES REST API 路径配置
ENV ODOO_ADDONS_PATH=/mnt/odoo/addons,/usr/lib/python3/dist-packages/odoo/addons
ENV ODOO_RC=/etc/odoo/odoo.conf

# 创建数据目录
RUN mkdir -p /var/lib/odoo /var/log/odoo /mnt/odoo/filestore /mnt/odoo/sessions \
    && chown -R odoo:odoo /var/lib/odoo /var/log/odoo /mnt/odoo

# 健康检查
HEALTHCHECK --interval=60s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8069/web/health || exit 1

# 切回 odoo 用户
USER odoo

# 默认命令
CMD ["odoo", "--db_host=postgres", "--db_port=5432", \
     "--db_user=odoo", "--db_password=odoo", "--db_name=gold_mes", \
     "--addons-path=/mnt/odoo/addons", \
     "--limit-memory-hard=0", "--limit-time-real=0", "--max-cron-threads=2"]
