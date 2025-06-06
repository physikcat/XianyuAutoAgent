import base64
import json
import asyncio
import time
import os
import websockets
from driver_holder import DriverHolder
driver = DriverHolder() 

from loguru import logger
from dotenv import load_dotenv
from XianyuApis import XianyuApis

from utils.xianyu_utils import generate_mid, generate_uuid, trans_cookies, generate_device_id, decrypt 
from XianyuAgent import XianyuReplyBot
from context_manager import ChatContextManager


class XianyuLive:
    def __init__(self, driver):
        cookies_str = driver.get_xianyu_cookie()
        self.driver = driver 
        self.xianyu = XianyuApis()
        self.base_url = 'wss://wss-goofish.dingtalk.com/'
        self.cookies_str = cookies_str
        self.cookies = trans_cookies(cookies_str)
        self.myid = self.cookies['unb']
        self.device_id = generate_device_id(self.myid)
        self.context_manager = ChatContextManager()
        
        # 心跳相关配置
        self.heartbeat_interval = 15  # 心跳间隔15秒
        self.heartbeat_timeout = 5    # 心跳超时5秒
        self.last_heartbeat_time = 0
        self.last_heartbeat_response = 0
        self.heartbeat_task = None
        self.update_task = None  # 定时任务句柄
        self.ws = None 
        self.ignore_user_ids = [] # 忽略名单 
        self.black_user_ids = [] # 黑名单 

    async def send_msg(self, ws, cid, toid, text):
        text = {
            "contentType": 1,
            "text": {
                "text": text
            }
        }
        text_base64 = str(base64.b64encode(json.dumps(text).encode('utf-8')), 'utf-8')
        msg = {
            "lwp": "/r/MessageSend/sendByReceiverScope",
            "headers": {
                "mid": generate_mid()
            },
            "body": [
                {
                    "uuid": generate_uuid(),
                    "cid": f"{cid}@goofish",
                    "conversationType": 1,
                    "content": {
                        "contentType": 101,
                        "custom": {
                            "type": 1,
                            "data": text_base64
                        }
                    },
                    "redPointPolicy": 0,
                    "extension": {
                        "extJson": "{}"
                    },
                    "ctx": {
                        "appVersion": "1.0",
                        "platform": "web"
                    },
                    "mtags": {},
                    "msgReadStatusSetting": 1
                },
                {
                    "actualReceivers": [
                        f"{toid}@goofish",
                        f"{self.myid}@goofish"
                    ]
                }
            ]
        }
        await ws.send(json.dumps(msg)) 
    
    async def send_info(self, ws, message): 
        send_user_name = message["1"]["10"]["reminderTitle"]
        send_user_id = message["1"]["10"]["senderUserId"] 
        cid = message["1"]["2"].split('@')[0]
        toid = send_user_id 
        print("发货", cid, toid)


        info0  = """账号昵称：\t 会员名：\t （会员名在设置里-账号与安全里的第一行）""" 
        info1  = """ 先把这些发我一下""" 
        await self.send_msg(ws, cid, send_user_id, info0)
        await asyncio.sleep(1)
        await self.send_msg(ws, cid, send_user_id, info1)
        await asyncio.sleep(30)
        logger.info("准备发送图片") 
        text = {
            "contentType": 2,
            "image":{"pics":[{"height":804,"type":0,"url":"https://img.alicdn.com/imgextra/i2/1574452518/O1CN0147UFuH1UTILK9CUa8_!!1574452518-0-xy_chat.jpg","width":1080}]} 
        }
        text_base64 = str(base64.b64encode(json.dumps(text).encode('utf-8')), 'utf-8')
        msg = {
            "lwp": "/r/MessageSend/sendByReceiverScope",
            "headers": {
                "mid": generate_mid()
            },
            "body": [
                {
                    "uuid": generate_uuid(),
                    "cid": f"{cid}@goofish",
                    "conversationType": 1,
                    "content": {
                        "contentType": 101,
                        "custom": {
                            "type": 1,
                            "data": text_base64
                        }
                    },
                    "redPointPolicy": 0,
                    "extension": {
                        "extJson": "{}"
                    },
                    "ctx": {
                        "appVersion": "1.0",
                        "platform": "web"
                    },
                    "mtags": {},
                    "msgReadStatusSetting": 1
                },
                {
                    "actualReceivers": [
                        f"{toid}@goofish",
                        f"{self.myid}@goofish"
                    ]
                }
            ]
        }
        await ws.send(json.dumps(msg)) 
        info2  = """丰田凯美瑞  二手汽车  自动档 空间大 省油 私家轿车  越野车 SUV MPV \t 关于车况：车况精品 经过第三方权威检测，三包，保证无事故 无泡水 让您买的放心! 低首付提爱车！不需要任何资质，不好也可以，有两证就能做下来，做有车一族，为您遮风挡雨，车就是您移动的家!""" 
        info3 = """ 标价 99，别的随便填，你先发布一下这个闲置 """
        await self.send_msg(ws, cid, send_user_id, info2)
        await asyncio.sleep(2)
        await self.send_msg(ws, cid, send_user_id, info3)
        

    async def init(self, ws):
        token = self.xianyu.get_token(self.cookies, self.device_id)['data']['accessToken']
        msg = {
            "lwp": "/reg",
            "headers": {
                "cache-header": "app-key token ua wv",
                "app-key": "444e9908a51d1cb236a27862abc769c9",
                "token": token,
                "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5) OS(Windows/10) Browser(Chrome/133.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5",
                "dt": "j",
                "wv": "im:3,au:3,sy:6",
                "sync": "0,0;0;0;",
                "did": self.device_id,
                "mid": generate_mid()
            }
        }
        await ws.send(json.dumps(msg))
        # 等待一段时间，确保连接注册完成
        await asyncio.sleep(1)
        msg = {"lwp": "/r/SyncStatus/ackDiff", "headers": {"mid": "5701741704675979 0"}, "body": [
            {"pipeline": "sync", "tooLong2Tag": "PNM,1", "channel": "sync", "topic": "sync", "highPts": 0,
             "pts": int(time.time() * 1000) * 1000, "seq": 0, "timestamp": int(time.time() * 1000)}]}
        await ws.send(json.dumps(msg))
        logger.info('连接注册完成')
    
    async def update_cookie(self):
        try: 
            logger.info('更新cookie ... ') 
            cookies_str = self.driver.update_cookie() 
            self.cookies_str = cookies_str
            self.cookies = trans_cookies(cookies_str)
            self.myid = self.cookies['unb']
            self.device_id = generate_device_id(self.myid) 
            logger.info('更新完毕') 
        except Exception as e:
            logger.error(f"更新Cookie失败: {e}")
    
    async def run_periodic_update(self):
        """定时更新 Cookie 的后台任务"""
        while True:
            await asyncio.sleep(3600)  # 1小时 = 3600秒
            logger.info("定时任务：更新 Cookie...")
            await self.update_cookie()

    async def check_cookie_valid(self):
        """检查Cookie是否有效"""
        try:
            # 尝试获取token，如果失败则说明Cookie已过期
            token_response = self.xianyu.get_token(self.cookies, self.device_id)
            if token_response.get('ret') and token_response['ret'][0] != "SUCCESS::调用成功":
                logger.error(f"Cookie已过期: {token_response}")
                await self.update_cookie()
                return False
            return True
        except Exception as e:
            logger.error(f"检查Cookie时出错: {e}")
            return False

    def is_chat_message(self, message):
        """判断是否为用户聊天消息"""
        try:
            if (
                isinstance(message, dict) 
                and "1" in message 
                and isinstance(message["1"], dict)  # 确保是字典类型
                and "10" in message["1"]
                and isinstance(message["1"]["10"], dict)  # 确保是字典类型
                and "reminderContent" in message["1"]["10"]
            ): 
                send_message = message["1"]["10"]["reminderContent"] 
                if send_message.count('发来一条新消息'): 
                    return False
                else: 
                    return True  
                
        except Exception:
            return False

    def is_sync_package(self, message_data):
        """判断是否为同步包消息"""
        try:
            return (
                isinstance(message_data, dict)
                and "body" in message_data
                and "syncPushPackage" in message_data["body"]
                and "data" in message_data["body"]["syncPushPackage"]
                and len(message_data["body"]["syncPushPackage"]["data"]) > 0
            )
        except Exception:
            return False

    def is_typing_status(self, message):
        """判断是否为用户正在输入状态消息"""
        try:
            return (
                isinstance(message, dict)
                and "1" in message
                and isinstance(message["1"], list)
                and len(message["1"]) > 0
                and isinstance(message["1"][0], dict)
                and "1" in message["1"][0]
                and isinstance(message["1"][0]["1"], str)
                and "@goofish" in message["1"][0]["1"]
            )
        except Exception:
            return False

    async def handle_message(self, message_data, websocket):
        """处理所有类型的消息"""
        try:
            try:
                message = message_data
                ack = {
                    "code": 200,
                    "headers": {
                        "mid": message["headers"]["mid"] if "mid" in message["headers"] else generate_mid(),
                        "sid": message["headers"]["sid"] if "sid" in message["headers"] else '',
                    }
                }
                if 'app-key' in message["headers"]:
                    ack["headers"]["app-key"] = message["headers"]["app-key"]
                if 'ua' in message["headers"]:
                    ack["headers"]["ua"] = message["headers"]["ua"]
                if 'dt' in message["headers"]:
                    ack["headers"]["dt"] = message["headers"]["dt"]
                await websocket.send(json.dumps(ack))
            except Exception as e:
                pass

            # 如果不是同步包消息，直接返回
            if not self.is_sync_package(message_data):
                return

            # 获取并解密数据
            sync_data = message_data["body"]["syncPushPackage"]["data"][0]
            
            # 检查是否有必要的字段
            if "data" not in sync_data:
                logger.debug("同步包中无data字段")
                return

            # 解密数据
            try:
                data = sync_data["data"]
                try:
                    data = base64.b64decode(data).decode("utf-8")
                    data = json.loads(data)
                    # logger.info(f"无需解密 message: {data}")
                    return
                except Exception as e:
                    # logger.info(f'加密数据: {data}')
                    decrypted_data = decrypt(data)
                    message = json.loads(decrypted_data)
            except Exception as e:
                logger.error(f"消息解密失败: {e}")
                return

            try:
                # 判断是否为订单消息,需要自行编写付款后的逻辑
                if message['3']['redReminder'] == '等待买家付款':
                    user_id = message['1'].split('@')[0]
                    user_url = f'https://www.goofish.com/personal?userId={user_id}'
                    logger.info(f'等待买家 {user_url} 付款')
                    return
                elif message['3']['redReminder'] == '交易关闭':
                    user_id = message['1'].split('@')[0]
                    user_url = f'https://www.goofish.com/personal?userId={user_id}'
                    logger.info(f'卖家 {user_url} 交易关闭')
                    return
                elif message['3']['redReminder'] == '等待卖家发货':
                    user_id = message['1'].split('@')[0]
                    user_url = f'https://www.goofish.com/personal?userId={user_id}'
                    logger.info(f'交易成功 {user_url} 等待卖家发货') 
                    return

            except:
                pass

            # 判断消息类型
            if self.is_typing_status(message):
                logger.debug("用户正在输入")
                return
            elif not self.is_chat_message(message):
                logger.debug("其他非聊天消息")
                logger.debug(f"原始消息: {message}")
                return

            # 处理聊天消息
            create_time = int(message["1"]["5"])
            send_user_name = message["1"]["10"]["reminderTitle"]
            send_user_id = message["1"]["10"]["senderUserId"]
            send_message = message["1"]["10"]["reminderContent"]  
            talk_id = message["1"]["2"].split('@')[0] 
            message_baseinfo = json.loads(message["1"]["6"]["3"]["5"])
            print(message) 

            # 时效性验证（过滤5分钟前消息）
            if (time.time() * 1000 - create_time) > 300000:
                logger.debug("过期消息丢弃")
                return

            if send_user_id == self.myid:
                logger.debug("过滤自身消息") 

                # 插入暗号 
                if send_message == "[送花][送花][送花][送花]": 
                    # 关闭此用户Ai 回复 
                    logger.debug(f"{talk_id} 加入到忽略名单") 
                    self.ignore_user_ids += [talk_id] 
                    print(self.ignore_user_ids)

                elif send_message == "[比心][比心][比心][比心]": 
                    # 打开此用户 
                    try: 
                        self.ignore_user_ids.remove(talk_id) 
                    except: 
                        pass 
                elif send_message == "[微笑][微笑][微笑][微笑]": 
                    # 拉黑用户
                    self.black_user_ids += [talk_id]

                return
            
            if message_baseinfo['contentType'] > 2: 
                logger.debug("卡片信息") 
                if send_message.count('[我已付款，等待你发货]'): 
                    await self.send_info(websocket, message) 
                return

            if send_message.count('[卡片消息]') or send_message.count('[我已拍下，待付款]'): 
                return  
            
            if talk_id in self.ignore_user_ids: 
                logger.info("AI忽略此用户消息") 
                return
            elif talk_id in self.black_user_ids:
                logger.info("黑名单用户重点关心")
                send_message = f'退款用户：{send_message}' 

            url_info = message["1"]["10"]["reminderUrl"]
            item_id = url_info.split("itemId=")[1].split("&")[0] if "itemId=" in url_info else None
            
            if not item_id:
                logger.warning("无法获取商品ID")
                return
                
            item_info = self.xianyu.get_item_info(self.cookies, item_id)['data']['itemDO']
            
            cur_time = time.strftime("%Y-%m-%d %H:%M", time.localtime()) 
            item_description = f"{item_info['desc']};当前商品售卖价格为:{str(item_info['soldPrice'])};当前时间为 {cur_time}" 
            
            logger.info(f"user: {send_user_name}, 发送消息: {send_message}")
            
            # 添加用户消息到上下文
            self.context_manager.add_message(send_user_id, item_id, "user", send_message)
            
            # 获取完整的对话上下文
            context = self.context_manager.get_context(send_user_id, item_id)
            
            # 生成回复
            bot_reply = bot.generate_reply(
                send_message,
                item_description,
                context=context
            )
            
            # 检查是否为价格意图，如果是则增加议价次数
            if bot.last_intent == "price":
                self.context_manager.increment_bargain_count(send_user_id, item_id)
                bargain_count = self.context_manager.get_bargain_count(send_user_id, item_id)
                logger.info(f"用户 {send_user_name} 对商品 {item_id} 的议价次数: {bargain_count}")
            
            # 添加机器人回复到上下文
            self.context_manager.add_message(send_user_id, item_id, "assistant", bot_reply)
            
            logger.info(f"机器人回复: {bot_reply}")
            cid = message["1"]["2"].split('@')[0]
            await self.send_msg(websocket, cid, send_user_id, bot_reply)
            
        except Exception as e:
            logger.error(f"处理消息时发生错误: {str(e)}")
            logger.info(f"尝试更新cookie") 
            await self.update_cookie()
            logger.debug(f"原始消息: {message_data}")

    async def send_heartbeat(self, ws):
        """发送心跳包并等待响应"""
        try:
            heartbeat_mid = generate_mid()
            heartbeat_msg = {
                "lwp": "/!",
                "headers": {
                    "mid": heartbeat_mid
                }
            }
            await ws.send(json.dumps(heartbeat_msg))
            self.last_heartbeat_time = time.time()
            logger.debug("心跳包已发送")
            return heartbeat_mid
        except Exception as e:
            logger.error(f"发送心跳包失败: {e}")
            raise

    async def heartbeat_loop(self, ws):
        """心跳维护循环"""
        while True:
            try:
                current_time = time.time()
                
                # 检查是否需要发送心跳
                if current_time - self.last_heartbeat_time >= self.heartbeat_interval:
                    await self.send_heartbeat(ws)
                
                # 检查上次心跳响应时间，如果超时则认为连接已断开
                if (current_time - self.last_heartbeat_response) > (self.heartbeat_interval + self.heartbeat_timeout):
                    logger.warning("心跳响应超时，可能连接已断开")
                    break
                
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"心跳循环出错: {e}")
                break

    async def handle_heartbeat_response(self, message_data):
        """处理心跳响应"""
        try:
            if (
                isinstance(message_data, dict)
                and "headers" in message_data
                and "mid" in message_data["headers"]
                and "code" in message_data
                and message_data["code"] == 200
            ):
                self.last_heartbeat_response = time.time()
                logger.debug("收到心跳响应")
                return True
        except Exception as e:
            logger.error(f"处理心跳响应出错: {e}")
        return False

    async def main(self):
        if not self.update_task:
            self.update_task = asyncio.create_task(self.run_periodic_update())
    
        while True:
            is_valid = await self.check_cookie_valid()  
            if not is_valid: 
                # 更新cookie  
                await self.update_cookie() 

            try:
                headers = {
                    "Cookie": self.cookies_str,
                    "Host": "wss-goofish.dingtalk.com",
                    "Connection": "Upgrade",
                    "Pragma": "no-cache",
                    "Cache-Control": "no-cache",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                    "Origin": "https://www.goofish.com",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }

                async with websockets.connect(self.base_url, extra_headers=headers) as websocket:
                    self.ws = websocket
                    await self.init(websocket)
                    
                    # 初始化心跳时间
                    self.last_heartbeat_time = time.time()
                    self.last_heartbeat_response = time.time()
                    
                    # 启动心跳任务
                    self.heartbeat_task = asyncio.create_task(self.heartbeat_loop(websocket))
                    
                    async for message in websocket:
                        try:
                            message_data = json.loads(message)
                            
                            # 处理心跳响应
                            if await self.handle_heartbeat_response(message_data):
                                continue
                            
                            # 发送通用ACK响应
                            if "headers" in message_data and "mid" in message_data["headers"]:
                                ack = {
                                    "code": 200,
                                    "headers": {
                                        "mid": message_data["headers"]["mid"],
                                        "sid": message_data["headers"].get("sid", "")
                                    }
                                }
                                # 复制其他可能的header字段
                                for key in ["app-key", "ua", "dt"]:
                                    if key in message_data["headers"]:
                                        ack["headers"][key] = message_data["headers"][key]
                                await websocket.send(json.dumps(ack))
                            # 处理其他消息
                            await self.handle_message(message_data, websocket)
                                
                        except json.JSONDecodeError:
                            logger.error("消息解析失败")
                        except Exception as e:
                            logger.error(f"解析消息时发生错误: {str(e)}")
                            logger.info(f"尝试更新cookie") 
                            await self.update_cookie()
                            logger.debug(f"原始消息: {message}")

            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket连接已关闭")
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
                    try:
                        await self.heartbeat_task
                    except asyncio.CancelledError:
                        pass
                await asyncio.sleep(5)  # 等待5秒后重连
                
            except Exception as e:
                logger.error(f"连接发生错误: {e}")
                if self.heartbeat_task:
                    self.heartbeat_task.cancel()
                    try:
                        await self.heartbeat_task
                    except asyncio.CancelledError:
                        pass
                await asyncio.sleep(5)  # 等待5秒后重连


if __name__ == '__main__':
    #加载环境变量 cookie
    load_dotenv()
    bot = XianyuReplyBot()
    xianyuLive = XianyuLive(driver)
    # 常驻进程
    asyncio.run(xianyuLive.main())
