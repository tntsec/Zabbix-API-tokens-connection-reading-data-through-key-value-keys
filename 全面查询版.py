import requests
import json
import datetime
import sys
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 警告（仅用于自签名证书）
disable_warnings(InsecureRequestWarning)

class ZabbixAPI:
    def __init__(self, url, api_token):
        self.url = url
        self.api_token = api_token
        self.headers = {"Content-Type": "application/json-rpc"}
    
    def _make_request(self, method, params):
        """发送 API 请求"""
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": self.api_token,
            "id": 1
        }
        
        try:
            response = requests.post(
                self.url,
                data=json.dumps(payload),
                headers=self.headers,
                verify=False  # 生产环境应使用有效证书并改为 True
            )
            response.raise_for_status()
            result = response.json()
            
            if "error" in result:
                error_msg = result["error"]["data"]
                raise Exception(f"API 错误: {error_msg}")
                
            return result.get("result", [])
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求失败: {e}")
    
    def get_items_by_key(self, key, host=None):
        """通过键值获取监控项列表"""
        params = {
            "output": ["itemid", "name", "key_", "hostid", "value_type"],
            "search": {"key_": key},
            "selectHosts": ["host"],
        }
        
        # 如果指定了主机名，添加主机过滤
        if host:
            params["search"]["host"] = host
        
        items = self._make_request("item.get", params)
        
        # 整理结果格式
        formatted_items = []
        for item in items:
            host_name = item["hosts"][0]["host"] if item.get("hosts") else "未知主机"
            formatted_items.append({
                "itemid": item["itemid"],
                "name": item["name"],
                "key": item["key_"],
                "hostid": item["hostid"],
                "host": host_name,
                "value_type": item["value_type"]
            })
        
        return formatted_items
    
    def get_latest_item_value(self, item_id):
        """获取指定监控项的最新数值"""
        params = {
            "output": ["itemid", "value", "clock"],
            "itemids": item_id,
            "sortfield": "clock",
            "sortorder": "DESC",
            "limit": 1
        }
        
        history_data = self._make_request("history.get", params)
        return history_data[0] if history_data else None


def display_items(items):
    """显示监控项列表"""
    if not items:
        print("未找到匹配的监控项")
        return
    
    print("\n找到以下监控项:")
    print("-" * 80)
    print(f"{'序号':<5} | {'主机':<20} | {'监控项名称':<30} | {'键值':<30}")
    print("-" * 80)
    
    for idx, item in enumerate(items, 1):
        print(f"{idx:<5} | {item['host'][:20]:<20} | {item['name'][:30]:<30} | {item['key'][:30]:<30}")
    
    print("-" * 80)


def main():
    # 配置信息
    ZABBIX_URL = "https://your-zabbix-server/zabbix/api_jsonrpc.php"
    API_TOKEN = "your_api_token_here"  # 替换为你的 API Token
    
    # 创建 API 客户端
    zabbix = ZabbixAPI(ZABBIX_URL, API_TOKEN)
    
    print("=" * 60)
    print("Zabbix 监控项数据查询工具 (通过键值查询)")
    print("=" * 60)
    
    # 获取用户输入的键值
    key = input("请输入要查询的键值 (如 'system.cpu.util[,idle]'): ").strip()
    if not key:
        print("错误：键值不能为空")
        return
    
    # 可选：指定主机名
    host_filter = input("可选：输入主机名进行过滤 (直接回车跳过): ").strip() or None
    
    # 搜索监控项
    print(f"\n搜索键值 '{key}'...")
    items = zabbix.get_items_by_key(key, host_filter)
    
    if not items:
        print(f"未找到匹配键值 '{key}' 的监控项")
        return
    
    display_items(items)
    
    # 如果只有一个监控项，直接显示结果
    if len(items) == 1:
        selected_item = items[0]
    else:
        # 让用户选择监控项
        while True:
            try:
                choice = input("\n请输入要查询的监控项序号 (输入 'q' 退出): ").strip()
                if choice.lower() == 'q':
                    print("程序已退出")
                    return
                
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(items):
                    selected_item = items[choice_idx]
                    break
                else:
                    print(f"错误：请输入 1-{len(items)} 之间的数字")
            except ValueError:
                print("错误：请输入有效的数字")
    
    # 获取最新数值
    print(f"\n获取监控项 '{selected_item['name']}' 的最新数据...")
    item_value = zabbix.get_latest_item_value(selected_item["itemid"])
    
    if not item_value:
        print(f"警告：监控项 {selected_item['itemid']} 没有可用数据")
        return
    
    # 转换时间戳为可读格式
    timestamp = int(item_value["clock"])
    last_check = datetime.datetime.fromtimestamp(timestamp)
    
    # 输出结果
    print("\n" + "=" * 60)
    print(f"主机: {selected_item['host']}")
    print(f"监控项 ID: {selected_item['itemid']}")
    print(f"监控项名称: {selected_item['name']}")
    print(f"键值: {selected_item['key']}")
    print(f"最新数值: {item_value['value']}")
    print(f"最后检查时间: {last_check.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"原始时间戳: {timestamp}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n发生错误: {e}")
        sys.exit(1)
