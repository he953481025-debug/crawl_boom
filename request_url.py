import json
import logging
import random
import string
import time
from datetime import datetime
from functools import wraps, partial
from hashlib import md5

import jwt
import requests
from apscheduler.schedulers.blocking import BlockingScheduler

proxi_dict = {
    "HTTPS": "120.42.248.200:17548"
}

proxyAddr = "tunnel3.qg.net:17548"
authKey = "C1F3147D"
password = "EFDDFF2E0337"
# 账密模式
proxyUrl = "http://%(user)s:%(password)s@%(server)s" % {
    "user": authKey,
    "password": password,
    "server": proxyAddr,
}
proxies = {
    "http": proxyUrl,
    "https": proxyUrl,
}

logging.getLogger().setLevel(logging.INFO)
logging.basicConfig(filename="app.log", filemode="a", encoding="UTF-8",
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
common_header = {"Tenant-Id": "1688", "Bm-Area-Id": "1012", "Request-Source": "wxMini",
                 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 MicroMessenger/7.0.20.1781(0x6700143B) NetType/WIFI MiniProgramEnv/Windows WindowsWechat/WMPF XWEB/8391"}
bm_member_token = "BOOMeyJ0eXBlIjoiSldUIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJCT09NIiwiaWF0IjoxNjk1Nzc4NjQ0LCJwbGF0Zm9ybSI6MSwiYXZhdGFyIjoiaHR0cHM6Ly9maWxlLmNkbi50YW5jaGkuc2hvcC9wcm9kL3VzZXIvZGVmYXVsdF9hdmF0YXI0LnBuZyIsIkFDQ09VTlRfSUQiOjE3MDYyNDIxODAwNzY1Mzk5MDYsImlkIjoxNzA2MjQyMTgwMDU5NzYyNjg5LCJuYW1lIjoi5Lya5ZGY55So5oi3MDg5NSIsImV4cCI6MTY5ODM3MDY0NH0.Sqa-8jFSgy444dbd6eRUaymd1TmE4aQ05GiH_r88yHA"
common_header["Bm-Member-Token"] = bm_member_token
domain = "https://api.mall.tanchi.shop"

order_member_token_list = [
    "BOOMeyJ0eXBlIjoiSldUIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJCT09NIiwiaWF0IjoxNjk1Nzc4NjQ0LCJwbGF0Zm9ybSI6MSwiYXZhdGFyIjoiaHR0cHM6Ly9maWxlLmNkbi50YW5jaGkuc2hvcC9wcm9kL3VzZXIvZGVmYXVsdF9hdmF0YXI0LnBuZyIsIkFDQ09VTlRfSUQiOjE3MDYyNDIxODAwNzY1Mzk5MDYsImlkIjoxNzA2MjQyMTgwMDU5NzYyNjg5LCJuYW1lIjoi5Lya5ZGY55So5oi3MDg5NSIsImV4cCI6MTY5ODM3MDY0NH0.Sqa-8jFSgy444dbd6eRUaymd1TmE4aQ05GiH_r88yHA",
    "BOOMeyJ0eXBlIjoiSldUIiwiYWxnIjoiSFMyNTYifQ.eyJpc3MiOiJCT09NIiwiaWF0IjoxNjk1NjMxNDA0LCJwbGF0Zm9ybSI6MSwiYXZhdGFyIjoiaHR0cHM6Ly9maWxlLmNkbi50YW5jaGkuc2hvcC9wcm9kL3VzZXIvYXZhdGFyLzZmNzkxNjM0MTVhNmI5YzE1NGJlZWQ0YTQ4MGM4MjdlIiwiQUNDT1VOVF9JRCI6MTM1NjUyMjk0MDM1NDcwNzQ1NywiaWQiOjEzNTY1MjI5NDAzNTQ3MDc0NTcsIm5hbWUiOiI25Y-3IiwiZXhwIjoxNjk4MjIzNDA0fQ.HWA1V2peDcBl6gJeDUwZyeg7ehnZaVVilfZ6EZmjryY"
]


def retry(max_retries, delay_seconds):
    def decorator_retry(func):
        def wrapper_retry(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    result = func(*args, **kwargs)
                    if result.json()['code'] == 0:
                        return result
                    else:
                        time.sleep(delay_seconds)
                        retries += 1
                        continue
                except Exception as e:
                    logging.error("Exception:")
                    print(f"Exception: {str(e)}")
                    print(f"Retrying in {delay_seconds} seconds...")
                    time.sleep(delay_seconds)
                    retries += 1
            print(f"Function {func.__name__} reached max retries ({max_retries}).")
            return func(*args, **kwargs)

        return wrapper_retry

    return decorator_retry


def decode_jwt(jwt_token):
    try:
        # 解析JWT令牌并禁用签名验证
        decoded_token = jwt.decode(jwt_token, options={"verify_signature": False})
        return decoded_token
    except jwt.ExpiredSignatureError as e:
        print("JWT令牌已过期", e)
    except jwt.DecodeError as e:
        print("JWT解码失败", e)
    except jwt.InvalidTokenError as e:
        print("无效的JWT令牌", e)


def login_req(func):
    @wraps(func)
    def with_logging(*args, **kwargs):
        time.time()
        req = func(*args, **kwargs)
        logging.info(f"请求的header: {req.request.headers}")
        logging.info(f"请求的url: {req.request.url}")

        logging.info(f"请求的body: {req.request.body}")
        logging.info(f"响应码: {req.status_code}")
        logging.info(f"响应头: {req.headers}")
        logging.info(f"响应体: {json.dumps(req.json(), ensure_ascii=False)}")
        return req

    return with_logging


@retry(1, 0.5)
@login_req
def get_anonymous_token():
    param = {"plantformId": "1"}
    req = requests.request(method="GET", url=domain + "/boom-center-user-service/app/members/getAnonymousToken",
                           headers=common_header, params=param)
    return req


@retry(1, 0.5)
@login_req
def get_active_config(config_id: str):
    req = requests.request(method="GET", url=domain + "/boom-center-admin-service/app/active/config/" + config_id,
                           headers=common_header)
    return req


@retry(1, 0.5)
@login_req
def get_activity_detail(req_body):
    req = requests.request(method="POST",
                           url=domain + "/boom-center-product-service/app/limitedTimeSaleActivity/listByActivityIds",
                           headers=common_header, json=req_body)
    return req


@retry(1, 0.5)
@login_req
def find_product_list(req_body):
    req = requests.request(method="POST",
                           url=domain + "/boom-center-product-service/app/limitedTimeSaleActivity/findProductListV1",
                           headers=common_header, json=req_body)
    return req


@retry(1, 0.5)
@login_req
def product_relate_store(req_param):
    spec_header = dict(common_header)
    spec_header["Bm-Area-Id"] = "-1"
    req = requests.request(method="GET", url=domain + "/boom-center-search-service/store/search/product",
                           headers=spec_header, params=req_param)
    return req


@retry(5, 0.1)
@login_req
def limited_time_sale_order(req_body, member_token):
    payload = decode_jwt(member_token.removeprefix("BOOM"))
    req_body["secret"] = generate_random_string(10)

    secret = req_body["secret"]
    md5_str = secret + ":" + str(payload["id"])
    md5_encrypt = encrypt_md5(md5_str, str(payload["id"]))
    spec_header = dict(common_header)
    spec_header["Bm-Member-Token"] = member_token
    spec_header["p-random"] = md5_encrypt
    req_body["random"] = md5_encrypt
    print(spec_header)
    req = requests.request(method="POST", url=domain + "/boom-mix-biz-service/app/order/limitedTimeSaleOrder/insert",
                           headers=spec_header, json=req_body)
    return req


def generate_random_string(length):
    # 从大小写字母和数字中生成随机字符
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string


def encrypt_md5(s, salt):
    # 创建md5对象
    new_md5 = md5()
    # 这里必须用encode()函数对字符串进行编码，不然会报 TypeError: Unicode-objects must be encoded before hashing
    new_md5.update((salt + s).encode(encoding='utf-8'))
    # 加密
    return new_md5.hexdigest()


def rush_to_buy(active_config_id_str, scheduler: BlockingScheduler):
    # 获取活动列表
    get_active_config_req = get_active_config(active_config_id_str)
    active_config_body = get_active_config_req.json()
    if active_config_body['code'] != 0:
        raise Exception(f"访问get_active_config_req出错，错误信息{active_config_body['msg']}")
    # 获取活动详情，判断时间
    assoc_sec_kill_list = active_config_body['data']['assocSecKillList']
    activity_id_list = [secKill["id"] for secKill in assoc_sec_kill_list]
    get_activity_detail_req = get_activity_detail({"activityIds": activity_id_list})
    get_activity_detail_body = get_activity_detail_req.json()
    now_second = time.time()
    now_milliseconds = int(now_second * 1000)
    now_format = datetime.fromtimestamp(now_second).strftime('%Y-%m-%d %H:%M:%S')
    # 遍历活动列表
    for activity_detail_dict in get_activity_detail_body["data"]:
        start_time = activity_detail_dict['startTime']
        end_time = activity_detail_dict['endTime']
        activity_id = activity_detail_dict['id']
        start_time_format = datetime.fromtimestamp(start_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
        end_time_format = datetime.fromtimestamp(end_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
        logging.info(
            f"活动id:{activity_id}, 活动名称:{activity_detail_dict['name']},活动开始时间:{start_time_format}, 活动结束时间{end_time_format}")
        if now_milliseconds > end_time:
            logging.info(f"活动已结束，活动id:{activity_id}, 活动结束时间{end_time_format}，当前时间{now_format}")
            continue
        if now_milliseconds + 600000 < start_time:
            # 前两分钟就开始获取对应的商品信息
            logging.info(f"活动未开始，活动id:{activity_id}, 活动结束时间{end_time_format}，当前时间{now_format}")
            continue
        # 获取活动关联的商品列表
        active_product_dict = {"location": {
            "lon": 113.317412,
            "lat": 23.084003
        }, "activityId": activity_id}
        find_product_list_req = find_product_list(active_product_dict)
        activity_product_body = find_product_list_req.json()
        activity_product_list = activity_product_body['data']
        # 获取商品关联的门店列表
        for activity_product_dict in activity_product_list:
            product_id_str = activity_product_dict["productId"]
            product_sku_dict = activity_product_dict["productSkuLimitedSecKillRelationVOList"][0]
            product_sku_id = product_sku_dict["productSkuId"]
            sec_kill_price = product_sku_dict["secKillPrice"]
            product_relate_store_req = product_relate_store(
                {"productId": product_id_str, "lat": 23.084003, "lon": 113.317412, "page": 1, "size": 10})
            first_product_relate_store = product_relate_store_req.json()["data"]["list"][0]
            store_id_str = first_product_relate_store["id"]
            store_title_str = first_product_relate_store["storeTitle"]
            order_dict = {
                "order": {
                    "mobile": "17306990895",
                    "notes": "",
                    "showMoney": sec_kill_price,
                    "greedyLegumesDeductionMoney": 0,
                    "orderSceneEnum": 0
                },
                "skuList": [
                    {
                        "skuId": product_sku_id,
                        "skuNum": 1,
                        "storeId": store_id_str,
                        "storeName": store_title_str,
                        "limitedTimeSaleActivityId": activity_id
                    }
                ],
                "orderAreaId": 1012,
                "payChannel": 1,
                "tenantId": 1688
            }
            # 组装下单参数
            # 活动开始前500毫秒发起请求
            next_run_time = datetime.fromtimestamp((start_time - 500) / 1000.0)
            for member_token in order_member_token_list:
                limited_time_sale_order_func = partial(limited_time_sale_order, order_dict, member_token)
                scheduler.add_job(limited_time_sale_order_func, 'date', misfire_grace_time=10,
                                  next_run_time=next_run_time)
