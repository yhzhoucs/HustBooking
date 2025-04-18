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
- PowerShell 7
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
conda create -n hustbooking python=3.10
conda activate hustbooking
# 安装依赖
pip3 install -r ./requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu
```

安装 Tesseract ：

**Arch Linux**

```shell
sudo pacman -Syu
sudo pacman -S tesseract tesseract-data-eng
```

**Gentoo**

```shell
# 激活 float32 推理与英文识别的 USE
sudo touch /etc/portage/package.use
echo -e "app-text/tesseract float32\napp-text/tessdata_fast l10n_en" | sudo tee -a /etc/portage/package.use
# 安装 tesseract
sudo emerge --ask app-text/tesseract
```

安装 at 并启动 atd 守护进程:

**Arch Linux**

```shell
sudo pacman -S at
sudo systemctl start atd
# 开机启动（可选）
sudo systemctl enable atd
```

**Gentoo** (OpenRC)

```shell
sudo emerge --ask sys-process/at
sudo rc-service atd start
# 开机启动（可选）
sudo rc-update add atd default
```

最后，准备 Captcha 识别库：

```shell
# 库的下载解压、补丁安装均已自动化
# 如果之前安装失败，先进行清理：make clean
make prepare
```

### Windows

确保所有代码均在 **PowerShell 7** 中运行。

你可以通过 `winget` 来 [安装 PowerShell 7](https://learn.microsoft.com/en-us/powershell/scripting/install/installing-powershell-on-windows?view=powershell-7.5)

```powershell
winget install --id Microsoft.PowerShell --source winget
```

启动 PowerShell 7 ，拉取代码：

```powershell
git clone https://github.com/yhzhoucs/HustBooking.git
cd HustBooking
```

然后参考 [UB Mannheim Wiki](https://github.com/UB-Mannheim/tesseract/wiki) 安装 Tesseract 。推荐使用默认的安装路径，这样就不需要更改后续的运行脚本。默认安装位置应当为：`C:\Program Files\Tesseract-OCR` 。

最后使用自动化脚本完成 Python 环境准备（这里使用的是便携版 Python3.10 ）和 Captcha 识别库的下载与配置：

```powershell
# 设置 PowerShell 的执行权限
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 如果之前安装失败，请先清理：./prepare.ps1 -Clean
# 你也可以查看帮助：Get-Help ./prepare.ps1
./prepare.ps1
```

## 编写预定配置

所有的预定配置均在 `booking.yaml` 文件中。主体配置项为：

| 配置名    | 说明         |
| --------- | ------------ |
| username  | 学号         |
| password  | 密码         |
| payment   | 支付方式     |
| schedule  | 定时任务配置 |
| default   | 默认预定配置 |
| option`N` | 可选预定配置 |

详细配置说明参见 [这里](./docs/details.md) 。

**注意1：** 这里的定时执行只能设置为 **当天** 的时间，如果想跨越多天（比如想设置在明天某个时间启动预定），请结合系统定时任务工具，参考 [启动预定](#启动预定) 。之所以采用这种方式有两个原因：

1. 脚本内的定时完全依赖计算出的秒数差，然后 sleep 特定秒数到预定时间，这样可能会造成时间误差
2. 长时间的定时任务交给操作系统是常用且专业的做法

**注意2：** option`N` 为默认配置预定失败后的备选项，N=1,2,3... ，预定脚本将逐个尝试。option`N` 下的配置项将替换 default 中的同名配置项，组成一个新的配置清单。因此，你可以**只写与 default 配置清单中不同的配置项** 。

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
/home/aozora/miniconda3/envs/hustbooking/bin/python ./main.py >my.log 2>&1
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
# 使用最高优先级运行（需要管理员权限）
./scripts/schedule.ps1 -ScheduleTime "2025-04-14 16:00" -Sudo
```

**注意1：** 如果你的 PowerShell 7 不在系统环境变量中，则需要修改 schedule.ps1 中的 `$pwsh` 变量。

**注意2：** 如果你的 Tesseract 并非安装在默认路径，则需要修改这两个 PowerShell 脚本中的 `$tesseractPath` 变量。

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
3. 确保 `booking.yaml` 中定时任务已启动，即 `schedule[enable]` 为 _true_
4. 保持登录为发送预定请求前1分钟不变，即 `schedule[login_deal]` 为 _-1_

这样脚本会在明天上午7点55分被系统启动，即刻进行模型预热，等待到7:59时进行帐号登陆，并在8点整执行预定操作。

## 致谢

- [scwang98/Captcha_Identifier](https://github.com/scwang98/Captcha_Identifier) 提供了破解点击文字验证码功能
- [MarvinTerry/HustLogin](https://github.com/MarvinTerry/HustLogin) 提供了登录 HustPass 的代码
- [rachpt/Booking-Assistant](https://github.com/rachpt/Booking-Assistant.git) 提供了登录验证思路

## 免责声明

本项目仅供学习交流使用，不得用于任何非法用途。开发本项目只是为了学习验证码识别思路、熟悉 Python 网络库的使用方法，使用本项目进行的任何预定操作均与项目作者无关，由此产生的任何后果由用户自行承担。

您下载本项目的代码即代表您已阅读并同意遵守上述免责声明。
