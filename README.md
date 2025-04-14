# HustBooking

一个用于预定华中科技大学大学体育场馆的自动化工具。

## 依赖项

### Linux

- Python 3.10
- GNU Make
- Tesseract
- at （用于系统定时任务）
- git, curl, unzip

### Windows

- Tesseract
- PowerShell
- git

## 环境准备

### Linux

首先，拉取代码：

```shell
git clone https://github.com/yhzhoucs/HustBooking.git
cd HustBooking
```

然后，准备 Python 环境：

```shell
# 这里使用 conda
conda create -n book python==3.10
conda activate book
# 安装 Python 依赖包
pip install -r ./requirements.txt
```

安装 Tesseract ：

```shell
# 这里只有 Arch Linux 上的安装示例
# 其他发行版请自行搜索安装
sudo pacman -Syu
sudo pacman -S tesseract tesseract-data-eng
```

最后，准备 Captcha 识别库：

```shell
# 库的下载解压、补丁安装均已自动化
# 如果之前安装失败，先进行清理：make clean
make prepare
```

### Windows

确保所有代码均在 **PowerShell** 中运行。

首先，拉取代码：

```powershell
git clone https://github.com/yhzhoucs/HustBooking.git
cd HustBooking
```

然后参考 [UB Mannheim Wiki](https://github.com/UB-Mannheim/tesseract/wiki) 安装 Tesseract 。推荐使用默认的安装路径，这样就不需要更改后续的运行脚本。默认安装位置应当为：`C:\Program Files\Tesseract-OCR` 。

最后使用自动化脚本完成 Python 环境准备（这里使用的是便携版 Python3.10 ）和 Captcha 识别库的下载与配置：

```powershell
# 如果之前安装失败，请先清理：./prepare.ps1 -Clean
# 你也可以查看帮助：Get-Help ./prepare.ps1
./prepare.ps1
```

## 编写预定配置

所有的预定配置均在 `booking.yaml` 文件中。下面对配置项进行说明。

| 配置名    | 说明         |
| --------- | ------------ |
| username  | 学号         |
| password  | 密码         |
| payment   | 支付方式     |
| schedule  | 定时任务配置 |
| default   | 默认预定配置 |
| option`N` | 可选预定配置 |

支持方式有两种选择

| 值  | 含义         |
| --- | ------------ |
| -1  | 电子账户支付 |
| -2  | 统一支付     |

schedule 为定时执行预定任务的相关配置，其下的配置项含义为：

| 配置名      | 说明                                           |
| ----------- | ---------------------------------------------- |
| enable      | 是否启用，值为 true 或 false                   |
| time        | 发起预定请求的时间，形如 "08:00:00"            |
| login_delta | 发起预定之前多长时间登录系统，-1 为提前 1 分钟 |

**注意：** 这里的定时执行只能设置为 **当天** 的时间，如果想跨越多天（比如想设置在明天某个时间启动预定），请结合系统定时任务工具。参考 [启动预定](#启动预定) 。之所以采用这种方式有两个原因：

1. 脚本内的定时完全依赖计算出的秒数差，然后 sleep 特定秒数到预定时间，这样可能会造成时间误差
2. 长时间的定时任务交给操作系统是常用且专业的做法

default 是预定体育场馆必要的配置单，其下的配置项含义为：

| 配置名          | 说明                 |
| --------------- | -------------------- |
| date            | 预定日期             |
| starttime       | 预定时间段的开始时间 |
| endtime         | 预定时间段的结束时间 |
| changdibh       | 场地编号             |
| choosetime      | 预定区域             |
| partnerCardtype | 同伴类型             |

场地编号可取的值与含义为：

| 值  | 含义                 |
| --- | -------------------- |
| 45  | 光谷体育馆羽毛球场   |
| 122 | 光谷体育馆乒乓球场   |
| 126 | 韵苑体育馆乒乓球场   |
| 74  | 东区操场韵苑网球场   |
| 73  | 中心区操场沁苑网球场 |
| 75  | 中心区操作沙地网球场 |
| 72  | 西区操场网球场       |
| 69  | 西边体育馆羽毛球     |
| 124 | 西边体育馆乒乓球     |
| 96  | 游泳馆游泳池         |
| 117 | 游泳馆二楼羽毛球     |

预定区域映射关系暂时没有发现规律，参考 [获取预定区域编号](#获取预定区域编号) 来获取。有更好想法的欢迎 Pull Request 。

同伴类型可取的值与含义为：

| 值  | 含义     |
| --- | -------- |
| 1   | 学生     |
| 2   | 教职工   |
| 3   | 校外人员 |

option`N` 为默认配置预定失败后的备选项，N=1,2,3... ，预定脚本将逐个尝试。option`N` 下的配置项将替换 default 中的同名配置项，组成一个新的配置清单。因此，你可以**只写与 default 配置清单中不同的配置项** 。

## 启动预定

### Linux

Linux 上即刻启动预定（确保配置文件中 `schedule[enable]` 为 false ）：

```shell
# 确保运行在正确的 Python 环境中
make book
# 或手动启动：python ./main.py
```

Linux 上定时启动，这里使用 at 工具：

```shell
man at # 查看 at 使用方法
at now + 5 minutes # 5 分钟后启动
at 16:00 04/14/2025 # 在2025年4月14日16时00分运行
```

在弹出的 prompt 中输入你想定时运行的命令，如：

```shell
cd /home/aozora/repos/HustBooking
/home/aozora/miniconda3/envs/book/bin/python ./main.py >my.log 2>&1
# 按 Ctrl+D 结束命令输入
```

**注意：** 确保运行时的工作目录为项目根目录，否则会出现路径问题。

之后你可以查看定时任务或删除定时任务：

```shell
atq # 查看
atrm [任务编号] # 删除
```

### Windows

Windows 上即刻启动（确保配置文件中 `schedule[enable]` 为 `false` ）：

```powershell
./scripts/directly_run.ps1
```

Windows 上的定时启动使用自带的任务计划程序来定时。具体的 PowerShell 代码已放置在 `scripts/schedule.ps1` 文件中。

使用方法：

```powershell
Get-Help ./scripts/schedule.ps1 # 获取帮助
./scripts/schedule.ps1 -ScheduleTime "2025-04-14 16:00" # 在2025年4月14日16时00分运行
```

**注意：** 如果你的 Tesseract 并非安装在默认路径，则需要修改这两个 PowerShell 脚本中的 `$tesseractPath` 变量。

### 定时任务的注意事项

当配置文件中 `schedule[enable]` 为 `true` 时，脚本执行的顺序为：

1. 脚本启动
2. （如果距离设定的登录时间多于1分钟）执行验证码识别模型的预热
3. 等待到设定的登录时间(`schedule[time]` - `schedule[login_delta]`)
4. 登录
5. 等待到设定的请求时间(`schedule[time]`)
6. 启动预定

如果你追求极致的速度，那么模型的预热是必要的。请确保启动脚本的时间至少比设定的登录时间早1分钟。

下面是一个推荐的方案：假设你设定的启动预定的时间为 _明天上午8点整_ ，那么：

1. 使用定时工具将脚本启动时间设定为提早5分钟，即 _明天上午7点55分_
2. 在 `booking.yaml` 中设定 `schedule[time]` 为 _08:00:00_
3. 确保 `booking.yaml` 中定时任务已启动，即 `schedule[enable]` 为 \*true\*\*
4. 保持登录为发送预定请求前1分钟不变，即 `schedule[login_deal]` 为 _-1_

这样脚本会在明天上午7点55分被系统启动，即刻进行模型预热，等待到7:59时进行帐号登陆，并在8点整执行预定操作。

## 获取预定区域编号

目前获取区域编号的方法是采用浏览器的开发者工具。

首先，进到区域选择页面，在你想预定的区域上右键-检查。

找到形如下面所示的 HTML 元素，其中的 `pian="XXX"` 即为预定区域的编号。

```html
<td
  class="getajax appointmented"
  title="光谷体育馆 主馆羽毛球场-普通区1(08:00:00-10:00:00)"
  pian="110"
></td>
```

## 致谢

- [scwang98/Captcha_Identifier](https://github.com/scwang98/Captcha_Identifier) 提供了破解点击文字验证码功能
- [MarvinTerry/HustLogin](https://github.com/MarvinTerry/HustLogin) 提供了登录 HustPass 的代码
- [rachpt/Booking-Assistant](https://github.com/rachpt/Booking-Assistant.git) 提供了登录验证思路

## 免责声明

本项目仅供学习交流使用，不得用于任何非法用途。开发本项目只是为了学习验证码识别思路、熟悉 Python 网络库的使用方法，使用本项目进行的任何预定操作均与项目作者无关，由此产生的任何后果由用户自行承担。
您下载本项目的代码即代表您已阅读并同意遵守上述免责声明。
