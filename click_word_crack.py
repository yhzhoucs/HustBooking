import base64
import json
import random
import time

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from Captcha_Identifier.captcha_locator import CaptchaLocator


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
    point_client_uid = "point-" + uuid
    return {
        "clientUid": point_client_uid,
        "captchaType": "clickWord",
        "ts": int(time.time() * 1000),
    }


def crack_captcha(s):
    payload = gen_captcha_request_payload()
    captcha = get_captcha(s, payload)
    positions = capture_positions(captcha["base64_img"], captcha["word_list"])
    points = cal_center_points(positions)
    points_str = json.dumps(points).replace(" ", "")
    encrypted = aes_encrypt(points_str, captcha["secret_key"])
    j = send_verify_post(s, encrypted, captcha["token"], payload["clientUid"])
    if j["repCode" != "0000"]:
        raise Exception("Captcha 验证失败")
    # todo: try more times
    return aes_encrypt(
        captcha["token"] + "---" + points_str, captcha["secret_key"]
    )


def aes_encrypt(word, key_word):
    key = key_word.encode("utf-8")
    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = pad(word.encode("utf-8"), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)
    return base64.b64encode(encrypted_data).decode("utf-8")


def get_captcha(s, payload):
    # s.headers = {
    #     "Referer": "http://pecg.hust.edu.cn/cggl/front/step2",
    #     "Content-Type": "application/json;charset=UTF-8",
    #     "Accept-Encoding": "gzip, deflate",
    #     "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2",
    #     "Connection": "keep-alive",
    #     "Host": "pecg.hust.edu.cn",
    #     "Origin": "http://pecg.hust.edu.cn",
    #     "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0",
    #     "priority": "u=4",
    # }

    url = "http://pecg.hust.edu.cn/cggl/api/open/captcha/get"
    resp = s.post(url, json=payload)
    if resp.status_code != 200:
        raise Exception(f"Captcha 请求失败，状态码：{resp.status_code}")

    j = resp.json()
    if j["repCode"] != "0000":
        raise Exception("Captcha 请求失败，repCode != 0000")

    return {
        "base64_img": j["repData"]["originalImageBase64"],
        "secret_key": j["repData"]["secretKey"],
        "word_list": j["repData"]["wordList"],
        "token": j["repData"]["token"],
    }


def capture_positions(base64_img, word_list):
    locator = CaptchaLocator()
    start_time = time.time()
    results = locator.run(base64_img, word_list)
    end_time = time.time()
    print(f"Captcha 识别完成，运行时间: {end_time - start_time:.4f} 秒")
    return results


def cal_center_points(positions):
    res = []
    for pos in positions:
        x = int(pos[0] + (pos[2] - pos[0]) / 2)
        y = int(pos[1] + (pos[3] - pos[1]) / 2)
        res.append({"x": x, "y": y})
    return res


def send_verify_post(s, pointJson, token, clientUid):
    # s.headers.update({"Content-Length": "249"})
    url = "http://pecg.hust.edu.cn/cggl/api/open/captcha/check"
    payload = {
        "captchaType": "clickWord",
        "pointJson": pointJson,
        "token": token,
        "clientUid": clientUid,
        "ts": int(time.time() * 1000),
    }
    resp = s.post(url, json=payload)
    if resp.status_code != 200:
        raise Exception(f"Captcha 验证请求失败，状态码：{resp.status_code}")
    return resp.json()


if __name__ == "__main__":
    locator = CaptchaLocator()

    with open("input.png", "rb") as f:
        image = f.read()

    img_base64 = base64.b64encode(image).decode("ascii")

    import time

    start_time = time.time()
    results = locator.run(img_base64, ["何", "旧", "士"])
    end_time = time.time()

    print(f"运行时间: {end_time - start_time:.4f} 秒")

    print(results)
