import copy
import datetime
import logging
import time
from datetime import datetime, timedelta

import yaml

from book_agent import BookAgent
from click_word_decaptcha import pre_init, warmup
from hustpass.login import login_hustpass

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


def get_float_time(target_time, delta_minutes=0):
    t = datetime.strptime(target_time, "%H:%M:%S").time()
    t = datetime.combine(datetime.now().date(), t)
    if delta_minutes != 0:
        t += timedelta(minutes=delta_minutes)
    return t.timestamp()


def schedule_task(target, f):
    # high precision timer with multi-level waiting

    while True:
        current = datetime.now().timestamp()
        remaining = target - current
        if remaining <= 0:
            return f()

        if remaining > 1:
            time.sleep(remaining * 0.8)
        else:
            # busy wait at the last second
            while datetime.now().timestamp() < target:
                pass
            return f()


if __name__ == "__main__":
    # 0. pre-init captcha models
    pre_init()

    # 1. load settings
    try:
        user, settings, schedule_setting = load_settings()
    except Exception:
        logger.exception("读取 booking.yaml 失败")
        exit(-1)

    if (
        schedule_setting["enable"]
        and get_float_time(
            schedule_setting["time"], schedule_setting["login_delta"] - 1
        )
        > datetime.now().timestamp()
    ):
        logger.info("时间充裕，开始模型预热")
        warmup()

    login_float_time = get_float_time(
        schedule_setting["time"], schedule_setting["login_delta"]
    )
    book_float_time = get_float_time(schedule_setting["time"])

    if login_float_time > datetime.now().timestamp():
        logger.info(
            "距离登录还有 {} 秒".format(login_float_time - datetime.now().timestamp())
        )

    schedule_task(login_float_time, lambda: None)

    # 2. login to hustpass
    target_url = "http://pecg.hust.edu.cn/cggl/index1"
    trying_times = 3
    for _ in range(trying_times):
        try:
            cookies = login_hustpass(user["username"], user["password"], target_url)
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

    if book_float_time > datetime.now().timestamp():
        logger.info(
            "距离预约还有 {} 秒".format(book_float_time - datetime.now().timestamp())
        )

    schedule_task(book_float_time, lambda: None)

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
