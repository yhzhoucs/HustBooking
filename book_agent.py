import logging
import re

from requests import Session

from click_word_decaptcha import ClickWordDecaptcha

logger = logging.getLogger(__name__)


class BookAgent:
    def __init__(self, setting: dict, cookies):
        self.setting = setting
        self.session = Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0"
            }
        )
        self.session.cookies.update(cookies)
        self.cg_csrf_token = ""
        self.token = ""
        self.step3_data = ""
        self.captcha_token = ""

    def book(self):
        self.login_booking_page()
        self.send_booking_request()
        self.captcha_token = ClickWordDecaptcha(self.session).decaptcha()
        self.send_step3_post()

    def login_booking_page(self):
        logger.info("登陆预订页面")
        url = "http://pecg.hust.edu.cn/cggl/front/syqk"
        params = {
            "cdhb": self.setting["changdibh"],
            "date": self.setting["date"],
            "starttime": self.setting["starttime"],
            "endtime": self.setting["endtime"],
        }
        resp = self.session.get(url, params=params)
        if resp.status_code != 200:
            raise Exception(f"登陆预订页面失败 {resp.status_code}")

        text = resp.text
        p1 = re.compile(r"""value=\\"(.+?)\\"\s*>""")
        p2 = re.compile(r"""name="cg_csrf_token" value="(.+?)"\s*/>""")

        try:
            match = p1.search(text, re.S)
            self.token = match.group(1)
            match = p2.search(text)
            self.cg_csrf_token = match.group(1)
        except Exception:
            raise Exception("从预订页面提取 token 失败")

        # !!IMPORTENT!! `Referer` is essential for the following requests
        referer = (
            url
            + "?"
            + "&".join([f"{key}={value}" for key, value in params.items()])
        )
        self.session.headers.update({"Referer": referer})

    def send_booking_request(self):
        logger.info("发送预订请求")
        url = "http://pecg.hust.edu.cn/cggl/front/step2"
        payload = {
            "starttime": self.setting["starttime"],
            "endtime": self.setting["endtime"],
            "partnerCardtype": str(self.setting["partnerCardtype"]),
            "choosetime": str(self.setting["choosetime"]),
            "changdibh": str(self.setting["changdibh"]),
            "date": self.setting["date"],
            "cg_csrf_token": self.cg_csrf_token,
            "token": [self.token, self.token],
        }
        resp = self.session.post(url, data=payload)
        if resp.status_code != 200:
            raise Exception(
                f"预订请求失败 {resp.status_code} （大概率已经被别人预订）"
            )

        try:
            self.step3_data = BookAgent.parse_step3_data(resp.text)
        except Exception as e:
            raise Exception("提取支付时需要的信息失败", e)

    def send_step3_post(self):
        logger.info("发送支付请求")
        url = "http://pecg.hust.edu.cn/cggl/front/step3"
        payload = {
            "captchatoken": self.captcha_token,
            "data": self.step3_data,
            "id": "",
            "select_pay_type": self.setting["payment"],
            "cg_csrf_token": self.cg_csrf_token,
            "token": [
                self.token,
                self.token,
            ],
        }
        resp = self.session.post(url, data=payload)
        if resp.status_code == 200:
            if "扣费失败" in resp.text:
                logger.info(
                    "预订成功，扣费失败，请在5分钟内去 个人中心 > 我的预约 中支付费用"
                )
            else:
                logger.info("预订成功，扣费成功")
        else:
            raise Exception(f"支付失败 {resp.status_code}")

    @staticmethod
    def parse_step3_data(html):
        p = re.compile(r"""<input name="data" value="(.+?)" type="hidden" />""")
        match = p.search(html)
        step3_data = match.group(1)
        return step3_data
