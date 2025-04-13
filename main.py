import copy
import logging

import yaml

from book_agent import BookAgent
from hustpass.login import login_hustpass


def load_settings():
    settings = []
    with open("booking.yaml", "r", encoding="UTF-8") as f:
        y = yaml.safe_load(f)
    if "username" not in y.keys() or "password" not in y.keys():
        raise Exception("请在 booking.yaml 中填写学号与密码")
    user = {"username": y["username"], "password": y["password"]}
    if "payment" not in y.keys():
        raise Exception("请在 booking.yaml 中填写支付方式")
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
    return user, settings


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    logger = logging.getLogger(__name__)
    # 1. load settings
    try:
        user, settings = load_settings()
    except Exception:
        logger.exception("读取 booking.yaml 失败")
        exit(-1)

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
        logger.critical("HustPass {} 次登录尝试均失败".format(trying_times))
        exit(-1)

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
