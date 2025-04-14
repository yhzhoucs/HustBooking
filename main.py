import copy
import datetime
import logging
import time
import os
import base64
from datetime import datetime, timedelta

import yaml

from book_agent import BookAgent
from hustpass.login import login_hustpass
from Captcha_Identifier.captcha_locator import CaptchaLocator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def load_settings():
    settings = []
    with open("booking.yaml", "r", encoding="UTF-8") as f:
        y = yaml.safe_load(f)
    if "username" not in y.keys() or "password" not in y.keys():
        raise Exception("请在 booking.yaml 中填写学号与密码")
    user = {"username": y["username"], "password": y["password"]}
    if "payment" not in y.keys():
        raise Exception("请在 booking.yaml 中填写支付方式")
    schedule_setting = {"enable": False, "time": None, "login_delta": 0}
    if "schedule" in y.keys():
        schedule_setting.update(y["schedule"])
    payment = y["payment"]
    items_needed = [
        "date",
        "starttime",
        "endtime",
        "changdibh",
        "choosetime",
        "partnerCardtype",
    ]
    default = y["default"]
    default["payment"] = payment
    for key in items_needed:
        if key not in default.keys():
            raise Exception("booking.yaml 不完整")
    settings.append(default)
    for variant in sorted(
        filter(lambda x: x != "default" and x.startswith("option"), y.keys())
    ):
        cloned = copy.deepcopy(default)
        for k, v in y[variant].items():
            cloned[k] = v
        settings.append(cloned)
    return user, settings, schedule_setting


def get_time_countdown(target_time, delta_minutes=0):
    t = datetime.strptime(target_time, "%H:%M:%S").time()
    t = datetime.combine(datetime.now().date(), t)
    if delta_minutes != 0:
        t += timedelta(minutes=delta_minutes)
    if t < datetime.now():
        return 0
    return (t - datetime.now()).seconds


def warmup_captcha():
    # warmup captcha locator
    locator = None
    if os.name == "nt":
        # fix from https://stackoverflow.com/questions/57286486/i-cant-load-my-model-because-i-cant-put-a-posixpath
        import pathlib
        temp = pathlib.PosixPath
        pathlib.PosixPath = pathlib.WindowsPath
        locator = CaptchaLocator()
        pathlib.PosixPath = temp
    else:
        locator = CaptchaLocator()

    with open("images/warmup.png", "rb") as f:
        img = f.read()
    img_base64 = base64.b64encode(img).decode("ascii")
    locator.run(img_base64, ['者', '天', '治'])


if __name__ == "__main__":
    # 1. load settings
    try:
        user, settings, schedule_setting = load_settings()
    except Exception:
        logger.exception("读取 booking.yaml 失败")
        exit(-1)

    if schedule_setting["enable"] and get_time_countdown(schedule_setting["time"], schedule_setting["login_delta"] - 1) > 0:
        logger.info("剩余时间充裕，进行验证码识别热身")
        warmup_captcha()
        

    login_countdown = 0
    if schedule_setting["enable"]:
        login_countdown = get_time_countdown(
            schedule_setting["time"], schedule_setting["login_delta"]
        )

    if login_countdown > 0:
        logger.info("距离登录还有 {} 秒".format(login_countdown))
        time.sleep(login_countdown)

    # 2. login to hustpass
    target_url = "http://pecg.hust.edu.cn/cggl/index1"
    trying_times = 3
    for _ in range(trying_times):
        try:
            cookies = login_hustpass(
                user["username"], user["password"], target_url
            )
        except Exception:
            logger.exception("登录 HustPass 失败")
            logger.info("再次尝试")
        else:
            break
    else:
        logger.critical(
            "HustPass {} 次seperate requirements for Windows登录尝试均失败".format(
                trying_times
            )
        )
        exit(-1)

    booking_countdown = 0
    if schedule_setting["enable"]:
        booking_countdown = get_time_countdown(schedule_setting["time"])

    if booking_countdown > 0:
        logger.info("距离预约还有 {} 秒".format(booking_countdown))
        time.sleep(booking_countdown)

    # 3. booking alongside settings
    for setting in settings:
        try:
            BookAgent(setting, cookies).book()
        except Exception:
            logger.exception("预订失败")
            logger.info("尝试下一个配置")
        else:
            break
    else:
        logger.critical("所有配置均尝试失败")
        exit(-1)
