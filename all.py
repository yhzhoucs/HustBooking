import copy
import logging
import re

import yaml
from requests import Session

from click_word_crack import crack_captcha
from hustpass.login import login_hustpass

common_headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
}


def load_settings():
    settings = []
    with open("booking.yaml", "r") as f:
        y = yaml.safe_load(f)
    if "username" not in y.keys() or "password" not in y.keys():
        raise Exception("Please specify username and password in booking.yaml")
    user = {"username": y["username"], "password": y["password"]}
    items_needed = [
        "date",
        "starttime",
        "endtime",
        "changdibh",
        "choosetime",
        "partnerCardtype",
    ]
    default = y["default"]
    for key in items_needed:
        if key not in default.keys():
            raise Exception("booking.yaml is not complete!")
    settings.append(default)
    for variant in sorted(
        filter(lambda x: x != "default" and x.startswith("option"), y.keys())
    ):
        cloned = copy.deepcopy(default)
        for k, v in y[variant].items():
            cloned[k] = v
        settings.append(cloned)
    return user, settings


def login_booking_page(cookies: dict, base_url: str, params: dict):
    s = Session()
    s.headers.update(common_headers)
    s.cookies.update(cookies)

    resp = s.get(base_url, params=params)
    if resp.status_code != 200:
        raise Exception(
            f"Login to booking pages failed, code {resp.status_code}"
        )

    text = resp.text
    p1 = re.compile(r"""value=\\"(.+?)\\"\s*>""")
    p2 = re.compile(r"""name="cg_csrf_token" value="(.+?)"\s*/>""")

    try:
        match = p1.search(text, re.S)
        token = match.group(1)
        match = p2.search(text)
        cg_csrf_token = match.group(1)
    except Exception:
        raise Exception("extract token from login page failed")

    return token, cg_csrf_token, s


def parse_step3_data(html):
    p = re.compile(r"""<input name="data" value="(.+?)" type="hidden" />""")
    match = p.search(html)
    try:
        step3_data = match.group(1)
    except Exception:
        raise Exception("Extract step3 data failed")

    return step3_data


def send_step3_post(s: Session, payload=dict):
    # s.headers = {
    #     "Host": "pecg.hust.edu.cn",
    #     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
    #     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    #     "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    #     "Accept-Encoding": "gzip, deflate",
    #     "Content-Type": "application/x-www-form-urlencoded",
    #     "Origin": "http://pecg.hust.edu.cn",
    #     "Connection": "keep-alive",
    #     "Referer": "http://pecg.hust.edu.cn/cggl/front/step2",
    #     "Upgrade-Insecure-Requests": "1",
    #     "Priority": "u=0, i",
    # }
    url = "http://pecg.hust.edu.cn/cggl/front/step3"
    resp = s.post(url, data=payload)


def book(setting, cookies):
    # 1. fetch token on the booking page
    url = "http://pecg.hust.edu.cn/cggl/front/syqk"
    params = {
        "cdhb": setting["changdibh"],
        "date": setting["date"],
        "starttime": setting["starttime"],
        "endtime": setting["endtime"],
    }
    try:
        token, cg_csrf_token, s = login_booking_page(cookies, url, params)
    except Exception:
        raise Exception("login to booking page failed")

    # 2. send book request
    url = "http://pecg.hust.edu.cn/cggl/front/step2"
    payload = {
        "starttime": setting["starttime"],
        "endtime": setting["endtime"],
        "partnerCardtype": setting["partnerCardtype"],
        "choosetime": setting["choosetime"],
        "changdibh": setting["changdibh"],
        "date": setting["date"],
        "cg_csrf_token": cg_csrf_token,
        "token": [token, token],
    }
    # s.headers.update(
    #     {
    #         "Host": "pecg.hust.edu.cn",
    #         "Content-Type": "application/x-www-form-urlencoded",
    #         "Origin": "http://pecg.hust.edu.cn",
    #         "Sec-GPC": "1",
    #         "Priority": "u=0,i",
    #         "Upgrade-Insecure-Requests": "1",
    #         "Referer": "http://pecg.hust.edu.cn/cggl/front/syqk?cdbh=122&date=2025-04-13&starttime=08:00:00&endtime=09:00:00",
    #     }
    # )
    resp = s.post(url, data=payload)
    if resp.status_code != 200:
        raise Exception("Book failed")

    print(resp.text)
    try:
        step3_data = parse_step3_data(resp.text)
    except Exception as e:
        raise Exception("Book failed", e)

    # 3. decaptcha
    try:
        captcha_token = crack_captcha(s)
    except Exception as e:
        raise Exception("Decaptcha failed", e)

    # 4. send payment request
    payload = {
        "captchatoken": captcha_token,
        "data": step3_data,
        "id": "",
        "select_pay_type": "-1",
        "cg_csrf_token": cg_csrf_token,
        "token": [
            token,
            token,
        ],
    }
    try:
        send_step3_post(s, payload)
    except Exception:
        raise Exception("Payment post failed")


def main():
    # 1. load settings
    try:
        user, settings = load_settings()
    except Exception as e:
        print("Error when loading settings", e)
        exit(-1)

    # 2. login to hustpass
    target_url = "http://pecg.hust.edu.cn/cggl/index1"
    try:
        cookies = login_hustpass(user["username"], user["password"], target_url)
    except Exception as e:
        print("Error when login hustpass", e)
        exit(-1)

    # 3. booking alongside settings
    for setting in settings:
        try:
            book(setting, cookies)
        except Exception as e:
            print("Book failed: ", setting)
            print(e)
            print("Try next...")
        else:
            break
        finally:
            break


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    main()
