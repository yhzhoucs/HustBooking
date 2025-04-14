import base64
import json
import logging
import os
import random
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from requests import Session

from Captcha_Identifier.captcha_locator import CaptchaLocator

logger = logging.getLogger(__name__)

locator = None
def pre_init():
    global locator
    start_time = time.time()
    if os.name == "nt":
        # fix from https://stackoverflow.com/questions/57286486/i-cant-load-my-model-because-i-cant-put-a-posixpath
        import pathlib
        temp = pathlib.PosixPath
        pathlib.PosixPath = pathlib.WindowsPath
        locator = CaptchaLocator()
        pathlib.PosixPath = temp
    else:
        locator = CaptchaLocator()
    end_time = time.time()
    logger.info(
        f"模型加载成功，时间: {end_time - start_time:.4f} 秒")


def warmup():
    with open("./docs/warmup.png", "rb") as f:
        image = f.read()
    img_base64 = base64.b64encode(image).decode("ascii")
    locator.run(img_base64, ["何", "旧", "士"])


class ClickWordDecaptcha:
    def __init__(self, session: Session, trying_times: int = 3):
        self.session = session
        self.client_uid = ClickWordDecaptcha.gen_captcha_request_payload()
        self.trying_times = trying_times

    def decaptcha(self):
        for i in range(self.trying_times):
            logger.info(f"破解点击文字验证，尝试第 {i + 1} 次")
            captcha = self.get_captcha()
            if captcha is None:
                continue

            positions = ClickWordDecaptcha.capture_positions(
                captcha["base64_img"], captcha["word_list"]
            )
            points = ClickWordDecaptcha.cal_center_points(positions)
            points_str = json.dumps(points).replace(" ", "")
            encrypted = ClickWordDecaptcha.aes_encrypt(
                points_str, captcha["secret_key"]
            )
            j = self.send_verify_post(encrypted, captcha["token"])
            if j is None:
                continue

            if j["repCode"] == "0000":
                return ClickWordDecaptcha.aes_encrypt(
                    captcha["token"] + "---" + points_str, captcha["secret_key"]
                )

        raise Exception("破解点击文字验证失败")

    def get_captcha(self):
        url = "http://pecg.hust.edu.cn/cggl/api/open/captcha/get"
        payload = {
            "clientUid": self.client_uid,
            "captchaType": "clickWord",
            "ts": ClickWordDecaptcha.now(),
        }
        resp = self.session.post(url, json=payload)
        if resp.status_code != 200:
            return None

        j = resp.json()
        if j["repCode"] != "0000":
            return None

        return {
            "base64_img": j["repData"]["originalImageBase64"],
            "secret_key": j["repData"]["secretKey"],
            "word_list": j["repData"]["wordList"],
            "token": j["repData"]["token"],
        }

    def send_verify_post(self, pointJson, token):
        url = "http://pecg.hust.edu.cn/cggl/api/open/captcha/check"
        payload = {
            "captchaType": "clickWord",
            "pointJson": pointJson,
            "token": token,
            "clientUid": self.client_uid,
            "ts": ClickWordDecaptcha.now(),
        }
        resp = self.session.post(url, json=payload)
        if resp.status_code != 200:
            return None
        return resp.json()

    @staticmethod
    def gen_captcha_request_payload():
        s = []
        hex_digits = "0123456789abcdef"

        for i in range(36):
            rand_num = random.randint(0, 15)
            s.append(hex_digits[rand_num])

        s[14] = "4"
        original_num = int(s[19], 16)
        new_num = (original_num & 0x3) | 0x8
        s[19] = hex_digits[new_num]
        s[8] = s[13] = s[18] = s[23] = "-"
        uuid = "".join(s)
        return "point-" + uuid

    @staticmethod
    def now():
        return int(time.time() * 1000)

    @staticmethod
    def aes_encrypt(word, key_word):
        key = key_word.encode("utf-8")
        cipher = AES.new(key, AES.MODE_ECB)
        padded_data = pad(word.encode("utf-8"), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted_data).decode("utf-8")

    @staticmethod
    def capture_positions(base64_img, word_list):
        start_time = time.time()
        results = locator.run(base64_img, word_list)
        end_time = time.time()
        logger.info(
            f"文字位置识别完成，运行时间: {end_time - start_time:.4f} 秒"
        )
        return results

    @staticmethod
    def cal_center_points(positions):
        res = []
        for pos in positions:
            x = int(pos[0] + (pos[2] - pos[0]) / 2)
            y = int(pos[1] + (pos[3] - pos[1]) / 2)
            res.append({"x": x, "y": y})
        return res


if __name__ == "__main__":
    with open("./docs/input.png", "rb") as f:
        image = f.read()

    img_base64 = base64.b64encode(image).decode("ascii")

    import time

    start_time = time.time()
    results = locator.run(img_base64, ["何", "旧", "士"])
    end_time = time.time()

    print(f"运行时间: {end_time - start_time:.4f} 秒")

    print(results)
