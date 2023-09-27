import logging
import time
from datetime import datetime

from request_url import get_active_config, get_activity_detail, find_product_list, product_relate_store, \
    order_member_token_list, limited_time_sale_order


def rush_to_buy(active_config_id_str):
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
        if "650d2741eb64f645cf9da616" != activity_id:
            continue
        start_time_format = datetime.fromtimestamp(start_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
        end_time_format = datetime.fromtimestamp(end_time / 1000.0).strftime('%Y-%m-%d %H:%M:%S')
        logging.info(
            f"活动id:{activity_id}, 活动名称:{activity_detail_dict['name']},活动开始时间:{start_time_format}, 活动结束时间{end_time_format}")
        if now_milliseconds > end_time:
            logging.info(f"活动已结束，活动id:{activity_id}, 活动结束时间{end_time_format}，当前时间{now_format}")
            continue
        # if now_milliseconds + 600000 < start_time:
        #     # 前两分钟就开始获取对应的商品信息
        #     logging.info(f"活动未开始，活动id:{activity_id}, 活动结束时间{end_time_format}，当前时间{now_format}")
        #     continue
        # 获取活动关联的商品列表
        active_product_dict = {"location": {
            "lon": 113.317412,
            "lat": 23.084003
        }, "activityId": activity_id}
        find_product_list_req = find_product_list(active_product_dict)
        activity_product_body = find_product_list_req.json()
        activity_product_list = activity_product_body['data']
        print(activity_product_list)
        # 获取商品关联的门店列表
        for activity_product_dict in activity_product_list:
            try:
                product_id_str = activity_product_dict["productId"]
                product_sku_dict = activity_product_dict["productSkuLimitedSecKillRelationVOList"][0]
                product_sku_id = product_sku_dict["productSkuId"]
                print(f"skuid:{product_sku_id}")
                sec_kill_price = product_sku_dict["secKillPrice"]
                product_relate_store_req = product_relate_store(
                    {"productId": product_id_str, "lat": 23.084003, "lon": 113.317412, "page": 1, "size": 10})
                first_product_relate_store = product_relate_store_req.json()["data"]["list"][0]
                store_id_str = first_product_relate_store["id"]
                store_title_str = first_product_relate_store["storeTitle"]
                order_dict = {
                    "order": {
                        "mobile": "17306990895",
                        "notes": "抢购",
                        "showMoney": sec_kill_price,
                        "orderSceneEnum": "WECHAT_MP"
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
                    "wxAppId": "wx8e4045e2189992f8",
                    "tenantId": 1688
                }
                # 组装下单参数
                # 活动开始前200毫秒发起请求
                for member_token in order_member_token_list:
                    limited_time_sale_order(order_dict, member_token)
            except Exception as e:
                print(e)


rush_to_buy("1704487985300381698")
