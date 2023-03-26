import json

import pytest
import requests

from test_litemall.test_litemall.logs_utils import logger


class TestLitemall():

    # 获取登录token
    def setup_class(self):
        # 1.管理端登录接口
        url = "https://litemall.hogwarts.ceshiren.com/admin/auth/login"
        user_data = {"username": "manage", "password": "manage123", "code": ""}
        r = requests.post(url=url, json=user_data)
        self.token = r.json()["data"]["token"]
        # 问题：只执行test_add_goods，未执行test_get_admin_token，所以self.token就不会被声明就会报错
        # 解决方案：self.token的声明一定要在test_add_goods方法执行之前完成，可使用setup_class提前完成变量的声明

        # 2.用户端登录接口
        url = "https://litemall.hogwarts.ceshiren.com/wx/auth/login"
        client_data = {"username": "user123", "password": "user123"}
        r = requests.post(url=url, json=client_data)
        self.client_token = r.json()["data"]["token"]

    # 清理脏数据
    def teardown(self):
        delete_url = "https://litemall.hogwarts.ceshiren.com/admin/goods/delete"
        r = requests.post(url=delete_url, json={"id": self.goods_id}, headers={"x-litemall-admin-token": self.token})
        logger.debug(f"删除商品接口的响应信息为{json.dumps(r.json(), indent=2, ensure_ascii=False)}")

    # 上架商品接口调试
    @pytest.mark.parametrize("goods_name", ["星河入梦2", "星河入梦3"])
    def test_add_goods(self, goods_name):
        # 3.上架商品接口
        url = "https://litemall.hogwarts.ceshiren.com/admin/goods/create"
        # goods_name = "星河入梦1"
        goods_data = {
            "goods": {"picUrl": "", "gallery": [], "isHot": False, "isNew": True, "isOnSale": True, "goodsSn": "001",
                      "name": f"{goods_name}"},
            "specifications": [{"specification": "规格", "value": "标准", "picUrl": ""}],
            "products": [{"id": 0, "specifications": ["标准"], "price": "18", "number": "18", "url": ""}],
            "attributes": []}
        header = {"x-litemall-admin-token": self.token}
        # 问题：token是手动复制的，一旦发生变化，还需要再次修改
        # 解决方案：token需要自动完成获取，并且赋值
        r = requests.post(url=url, json=goods_data, headers=header)
        # 打印响应体内容
        # print(r.json())
        # logger.debug(f"上架商品接口的响应信息为{r.json()}")
        logger.debug(f"上架商品接口的响应信息为{json.dumps(r.json(), indent=2, ensure_ascii=False)}")
        # 4.获取商品列表接口（获取goodsId）
        goods_list_url = "http://litemall.hogwarts.ceshiren.com/admin/goods/list"
        goods_data = {
            "name": f"{goods_name}",
            "order": "desc",
            "sort": "add_time"
        }
        # 是一个get请求，参数需要通过params也就是url传递
        r = requests.get(url=goods_list_url, params=goods_data, headers=header)
        self.goods_id = r.json()["data"]["list"][0]["id"]

        logger.debug(f"获取商品列表接口的响应信息为{json.dumps(r.json(), indent=2, ensure_ascii=False)}")

        # 5.获取商品详情接口（获取productId）
        goods_detail_url = "http://litemall.hogwarts.ceshiren.com/admin/goods/detail"
        r = requests.get(url=goods_detail_url, params={"id": self.goods_id}, headers=header)
        product_id = r.json()["data"]["products"][0]["id"]
        logger.debug(f"获取商品详情接口的响应信息为{json.dumps(r.json(), indent=2, ensure_ascii=False)}")
        # 6.添加购物车接口
        url = "https://litemall.hogwarts.ceshiren.com/wx/cart/add"
        # 问题：goodsId和productId已经被写死，没有完成变量传递
        # 解决方案：goodsId和productId从其他接口获取，并传递给添加购物车接口
        cart_data = {"goodsId": self.goods_id, "number": 1, "productId": product_id}
        r = requests.post(url=url, json=cart_data, headers={"x-litemall-token": self.client_token})
        res = r.json()
        logger.info(f"添加购物车接口的响应信息为{json.dumps(r.json(), indent=2, ensure_ascii=False)}")
        # =================问题一：缺少断言
        # =================解决方案：添加断言
        assert res["errmsg"] == "成功"

        # =================问题二：goods_name不能重复，所以需要添加参数化
        # =================解决方案：添加参数化

        # =================问题三：缺少日志信息
        # =================解决方案：添加日志

        # =================问题四：执行完用例后出现脏数据
        # =================解决方案：在teardown中调用删除接口
