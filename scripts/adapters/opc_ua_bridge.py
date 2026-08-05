"""
OPC UA Bridge to Odoo MES (Stub Demo)
======================================

【说明】完整版需: pip install opcua==0.98.13 requests>=2.31
本文件是参考架构,实际部署时根据车间设备型号调整节点映射。

将 OPC UA 设备节点值(失蜡炉 / 油压机 / 3D 打印机)实时推送到 MES REST API。
"""
import os
import sys
import time
import json
import logging
import argparse
from datetime import datetime
from threading import Event, Thread

# 模拟 opcua 库(若未安装)
try:
    import requests
except ImportError:
    requests = None

try:
    from opcua import Client, ua
except ImportError:
    Client = None
    ua = None


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("opc_ua_bridge")


class MESClient:
    """Odoo MES REST API 客户端"""

    def __init__(self, api_url, username, password):
        self.api_url = api_url.rstrip("/")
        self.session = requests.Session() if requests else None
        if self.session:
            self.session.auth = (username, password)
        self.connected = False

    def post_metric(self, device_code, metrics, context=None):
        if not self.session:
            logger.warning("requests 未安装, 跳过推送")
            return False
        payload = {
            "device_code": device_code,
            "metrics": metrics,
            "context": context or {},
        }
        try:
            r = self.session.post(
                f"{self.api_url}/gold_mes/api/v1/device/metric",
                json=payload,
                timeout=5,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"推送失败: {e}")
            return False

    def heartbeat(self, device_code, state="running"):
        if not self.session:
            return False
        try:
            r = self.session.post(
                f"{self.api_url}/gold_mes/api/v1/device/heartbeat",
                json={"device_code": device_code, "state": state},
                timeout=5,
            )
            r.raise_for_status()
            return True
        except Exception as e:
            logger.warning(f"心跳失败: {e}")
            return False


class OPCUABridge:
    """OPC UA → MES 桥接"""

    def __init__(self, endpoint, mes_client, nodes_config, poll_interval=5):
        self.endpoint = endpoint
        self.mes = mes_client
        self.nodes = self._parse_nodes(nodes_config)
        self.poll_interval = poll_interval
        self.client = None
        self.running = Event()

    def _parse_nodes(self, config):
        """节点: 'device_code.metric' 列表"""
        nodes = {}
        for item in config.split(","):
            item = item.strip()
            if not item:
                continue
            parts = item.split(".", 1)
            if len(parts) != 2:
                continue
            device, metric = parts
            nodes.setdefault(device, []).append(metric)
        return nodes

    def connect(self):
        if Client is None:
            logger.error("opcua 未安装. pip install opcua==0.98.13")
            return False
        logger.info(f"连接 OPC UA: {self.endpoint}")
        self.client = Client(self.endpoint)
        try:
            self.client.connect()
            logger.info("OPC UA 连接成功")
            return True
        except Exception as e:
            logger.error(f"OPC UA 连接失败: {e}")
            return False

    def disconnect(self):
        if self.client:
            self.client.disconnect()

    def _read(self, metric):
        """读取节点值,失败返回 None"""
        try:
            node = self.client.get_node(f"ns=2;s={metric}")
            return node.get_value()
        except Exception as e:
            logger.warning(f"节点 {metric} 读取失败: {e}")
            return None

    def _poll_once(self):
        for device, metrics in self.nodes.items():
            data = {}
            for m in metrics:
                v = self._read(m)
                if v is not None:
                    data[m] = v
            if data:
                self.mes.post_metric(device, data)
                logger.info(f"推送 {device}: {data}")

    def heartbeat_loop(self):
        """每 60 秒心跳"""
        while not self.running.is_set():
            for device in self.nodes.keys():
                self.mes.heartbeat(device)
            time.sleep(60)

    def run(self):
        if not self.connect():
            return
        Thread(target=self.heartbeat_loop, daemon=True).start()
        logger.info(f"开始轮询 {self.poll_interval} 秒")
        try:
            while not self.running.is_set():
                self._poll_once()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            pass
        finally:
            self.disconnect()

    def stop(self):
        self.running.set()


def main():
    parser = argparse.ArgumentParser(description="OPC UA Bridge to Odoo MES")
    parser.add_argument("--endpoint", default="opc.tcp://192.168.10.21:4840")
    parser.add_argument("--api-url", default="http://localhost:8069")
    parser.add_argument("--api-user", default="admin")
    parser.add_argument("--api-password", default="admin")
    parser.add_argument("--nodes", default="LWF-001.temperature,LWF-001.vacuum_kpa")
    parser.add_argument("--interval", type=int, default=5)
    args = parser.parse_args()

    mes = MESClient(args.api_url, args.api_user, args.api_password)
    bridge = OPCUABridge(args.endpoint, mes, args.nodes, args.interval)
    try:
        bridge.run()
    except KeyboardInterrupt:
        bridge.stop()


if __name__ == "__main__":
    main()
