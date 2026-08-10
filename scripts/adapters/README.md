# 设备适配器(Adapters)

车间 ERP 的设备层协议适配器,用于把车间设备数据(失蜡炉 / 油压机 / 电子天平 / 3D 打印机)实时推送到 MES REST API。

## 当前状态

| 适配器 | 状态 | 协议 |
|--------|------|------|
| `opc_ua_bridge.py` | 💡 Demo (伪代码参考) | OPC UA |
| `mqtt_bridge.py` | 💡 计划中 | MQTT |
| `modbus_bridge.py` | 💡 计划中 | Modbus TCP |
| `balance_reader.py` | 💡 计划中 | RS-232 (梅特勒 XPR) |

## 架构

```
设备层:  失蜡炉 ─┐                ┌─→ MES REST API
       油压机 ─┤  OPC UA / MQTT  ├─→  /dunhuang_gold_mes/api/v1/device/metric
       3D打印机 ┤ ───────────────┤
       电子天平 ┘                └─→  /dunhuang_gold_mes/api/v1/device/heartbeat
```

## 接入新设备的步骤

1. 在设备台账/设备台账中创建设备(`gold.equipment`)
2. 选择通讯协议(`opc_ua` / `mqtt` / `modbus` / `rs232`)
3. 填写 IP / 端口 / 节点 ID
4. 启动对应适配器,指定节点映射
5. 验证看板 → 设备状态 → 实时数据

## OPC UA 适配器 (Demo)

参考 `opc_ua_bridge.py`(伪代码),完整实现需要安装:

```bash
pip install opcua==0.98.13 requests>=2.31
```

### 配置示例

```yaml
endpoint: opc.tcp://192.168.10.21:4840
nodes:
  - LWF-001.temperature      # 失蜡炉温度
  - LWF-001.vacuum_kpa        # 真空度
  - OBP-001.pressure_ton     # 油压机压力
  - OBP-001.stroke_count     # 压次累计
poll_interval: 5  # 秒
```

### 启动

```bash
python opc_ua_bridge.py \
  --endpoint opc.tcp://192.168.10.21:4840 \
  --api-url http://localhost:8069 \
  --api-user admin \
  --api-password admin \
  --nodes LWF-001.temperature,LWF-001.vacuum_kpa
```

## MQTT 适配器 (计划中)

适用:
- 3D 打印机 (Form 3+ / Anycubic)
- 称重传感器
- 工业网关

```bash
pip install paho-mqtt==1.6.1
```

## Modbus 适配器 (计划中)

适用:
- 雕蜡机 (Roland DWX-52D)
- 抛光机
- 离心铸造机

```bash
pip install pymodbus==3.5.2
```

## 电子天平 (计划中)

梅特勒 XPR 系列串口协议,采集 0.001g 精度的重量数据。

```bash
pip install pyserial==3.5
```

## 真实部署建议

1. **网络**: 车间设备通过工业以太网 / OPC UA 网关连接到生产网
2. **隔离**: 设备子网与 ERP 子网通过防火墙隔离
3. **可靠性**: 适配器进程用 systemd 守护,失败自动重启
4. **监控**: 适配器心跳监控 + Prometheus exporter
