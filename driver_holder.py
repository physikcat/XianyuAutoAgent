from selenium import webdriver
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.edge.options import Options
import json
import os
import time

# 配置镜像源加速下载
os.environ["WDM_EDGEDRIVER_URL"] = "https://npm.taobao.org/mirrors/edgedriver"

class DriverHolder: 
    def __init__(self):
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
        self.driver = webdriver.Edge(service=service, options=edge_options) 
    
    def get_xianyu_cookie(self):
        # 设置智能等待策略
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(15)
        
        # 加载已有Cookie（如果存在）
        if os.path.exists('xianyu_cookies.json'):
            with open('xianyu_cookies.json', 'r') as f:
                cookies = json.load(f)
                self.driver.get('https://www.goofish.com/')  # 必须先访问域名
                for cookie in cookies:
                    self.driver.add_cookie(cookie)
            print("已加载历史Cookie，尝试保持会话...")
        
        # 访问目标页面
        self.driver.get('https://www.goofish.com/')
        print("当前页面标题:", self.driver.title)

        # 会话状态检查
        if "login" not in self.driver.current_url:
            print("检测到有效会话，跳过登录...")
        else:
            # 人工介入登录
            input("请手动完成登录后按回车保存Cookie...")
            
            # 验证登录成功
            if "login" in self.driver.current_url:
                raise Exception("登录状态未生效，请检查登录操作") 
        
        self.driver.get('https://www.goofish.com/im?spm=a21ybx.home.sidebar.1.4c053da6EEIHQx')  
        cookies = self.driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        # 获取并保存新Cookie
        with open('xianyu_cookies.json', 'w') as f:
            json.dump(cookies, f, indent=2)
        with open('xianyu_cookies.txt', 'w') as f:
            f.write(cookie_str)
        print(f"成功保存{len(cookies)}个Cookie")
        
        return cookie_str

    def update_cookie(self): 
        # self.driver.get('https://www.goofish.com/im?spm=a21ybx.home.sidebar.1.4c053da6EEIHQx') 
        self.driver.refresh()
        self.driver.implicitly_wait(5)
        cookies = self.driver.get_cookies()
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        return cookie_str

        
    def close(self):
        self.driver.quit()