import requests
import json

# 配置信息
ZABBIX_URL = "https://your-zabbix-server/zabbix/api_jsonrpc.php"
API_TOKEN = "your_api_token_here"  # 替换为你的 API Token
KEY = "system.cpu.util[,idle]"    # 替换为要查询的键值
HOST = "your-host-name"            # 替换为目标主机名（可选）

# 通过键值获取监控项ID
def get_item_id(key, host=None):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.get",
        "params": {
            "output": ["itemid"],
            "search": {"key_": key},
            "filter": {"host": [host]} if host else {}
        },
        "auth": API_TOKEN,
        "id": 1
    }
    response = requests.post(ZABBIX_URL, json=payload, verify=False)
    items = response.json().get("result", [])
    return items[0]["itemid"] if items else None

# 获取监控项最新数值
def get_latest_value(item_id):
    payload = {
        "jsonrpc": "2.0",
        "method": "history.get",
        "params": {
            "output": ["value"],
            "itemids": item_id,
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 1
        },
        "auth": API_TOKEN,
        "id": 2
    }
    response = requests.post(ZABBIX_URL, json=payload, verify=False)
    history = response.json().get("result", [])
    return history[0]["value"] if history else None

# 主程序
if __name__ == "__main__":
    # 获取监控项ID
    item_id = get_item_id(KEY, HOST)
    
    if not item_id:
        print(f"错误: 未找到键值 '{KEY}' 的监控项")
        exit(1)
    
    # 获取最新数值
    value = get_latest_value(item_id)
    
    if value is None:
        print(f"警告: 监控项 {item_id} 没有可用数据")
        exit(2)
    
    # 输出结果
    print(value)
