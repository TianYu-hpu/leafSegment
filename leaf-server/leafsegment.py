import requests
import time
import threading

target_list = []
success_count = 0
fail_count = 0
max_retries = 3  # 单个请求最大重试次数
base_delay = 1  # 基础重试延迟(秒)
url = "http://127.0.0.1/api/segment/get/order_id"
lock = threading.Lock()  # 用于线程安全的锁

def fetch_data(start, end):
    global success_count, fail_count
    for i in range(start, end):
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()  # 自动处理4xx/5xx状态码

                data = response.json()
                with lock:
                    target_list.append(data)
                    success_count += 1
                break  # 成功则跳出重试循环
            except requests.exceptions.RequestException as e:
                print(f"第{i}次请求失败（尝试{attempt + 1}/{max_retries}）: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(base_delay * (attempt + 1))  # 指数退避延迟
                else:
                    with lock:
                        fail_count += 1

# 创建8个线程
threads = []
total_requests = 8000
thread_count = 8
requests_per_thread = total_requests // thread_count

for i in range(thread_count):
    start = i * requests_per_thread + 1
    end = (i + 1) * requests_per_thread + 1 if i < thread_count - 1 else total_requests + 1
    thread = threading.Thread(target=fetch_data, args=(start, end))
    threads.append(thread)
    thread.start()

# 等待所有线程完成
for thread in threads:
    thread.join()

# 结果校验
print(f"\n请求完成 - 成功: {success_count}, 失败: {fail_count}")
print(f"列表长度校验: {'通过' if len(target_list) == 8000 else '失败'}")

# 附加校验逻辑（可选）
if len(target_list) != 8000:
    print(f"警告：缺失数据量 {8000 - len(target_list)} 条")
    print("可能原因：")
    print("1. 服务器不稳定导致部分请求失败")
    print("2. 网络连接问题")
    print("3. 接口限流机制触发")
