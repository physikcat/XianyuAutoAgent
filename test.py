

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options
import json
import os
import time

import base64
# import json
import asyncio
# import time
# import os
import websockets
# # from driver_holder import DriverHolder 
# from loguru import logger
# # from dotenv import load_dotenv
from XianyuApis import XianyuApis

# from utils.xianyu_utils import generate_mid, generate_uuid, trans_cookies, generate_device_id, decrypt
# from XianyuAgent import XianyuReplyBot
# from context_manager import ChatContextManager

# 配置镜像源加速下载
os.environ["WDM_EDGEDRIVER_URL"] = "https://npm.taobao.org/mirrors/edgedriver"

def capture_xianyu_cookie():
    # 配置用户数据目录（保持会话持久化）
    user_data_dir = os.path.join(os.getcwd(), "edge_profile")
    edge_options = Options()
    edge_options.add_argument(f"--user-data-dir={user_data_dir}")  # 持久化存储会话数据
    edge_options.add_argument("--disable-blink-features=AutomationControlled")
    edge_options.add_argument("--disable-features=msEdgeSync")  # 禁用账户同步
    edge_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    
    # 自动管理驱动（只安装一次）
    driver_path = EdgeChromiumDriverManager().install()
    print(f"驱动安装路径: {driver_path}")
    service = Service(driver_path) 

    # 启动浏览器（复用已有会话）
    driver = webdriver.Edge(service=service, options=edge_options)
    
    try:
        # 设置智能等待策略
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(15)
        
        # 加载已有Cookie（如果存在）
        if os.path.exists('xianyu_cookies.json'):
            with open('xianyu_cookies.json', 'r') as f:
                cookies = json.load(f)
                driver.get('https://www.goofish.com/')  # 必须先访问域名
                for cookie in cookies:
                    driver.add_cookie(cookie)
            print("已加载历史Cookie，尝试保持会话...")

        # 访问目标页面
        driver.get('https://www.goofish.com/login')
        print("当前页面标题:", driver.title)
        
        # 会话状态检查
        if "login" not in driver.current_url:
            print("检测到有效会话，跳过登录...")
        else:
            # 人工介入登录
            input("请手动完成登录后按回车保存Cookie...")
            
            # 验证登录成功
            if "login" in driver.current_url:
                raise Exception("登录状态未生效，请检查登录操作")
        
        cookies = driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        print(cookie_str)
        # 获取并保存新Cookie
        cookies = driver.get_cookies()
        with open('xianyu_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        with open('xianyu_cookies.txt', 'w') as f:
            f.write(cookie_str)
        print(f"成功保存{len(cookies)}个Cookie")
        
        return cookies

    except Exception as e:
        print(f"操作异常: {str(e)}")
        # 失败时保留浏览器实例便于调试
        input("按回车关闭浏览器...")
        raise
    finally:
        input("按回车关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    captured_cookies = capture_xianyu_cookie()
    print("获取到的Cookie示例：")
    print(json.dumps(captured_cookies[:2], indent=2)) 