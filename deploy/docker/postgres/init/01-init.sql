-- 贵金属车间 ERP - PostgreSQL 初始化
-- 字符集 / 排序规则 / 时区

-- 设置字符集
ALTER DATABASE gold_mes SET client_encoding = 'UTF8';
ALTER DATABASE gold_mes SET default_transaction_isolation = 'read committed';

-- 中文全文检索
-- 注: 需先安装 zhparser 扩展(/usr/share/postgresql/15/extension/zhparser.control)
-- CREATE EXTENSION IF NOT EXISTS zhparser;
-- CREATE TEXT SEARCH CONFIGURATION gold_zhcfg (PARSER = zhparser);
-- ALTER TEXT SEARCH CONFIGURATION gold_zhcfg ADD MAPPING FOR n,v,a,i,e,l WITH simple;

-- 时区
SET timezone = 'Asia/Shanghai';

-- 优化: gold_mes 数据量大,设置合适的统计
ALTER DATABASE gold_mes SET default_statistics_target = 100;
