# automated-redemption-for-nutaku-daily-rewards

nutaku金币活动自动签到脚本。

最近n站出了个金币签到活动，经过粗略计算，最多可获取到一百八十+的金币，看着很馋...

但就是每天得打开网站点击签到有点烦人，几乎要月全勤才能拿完所有的奖励，因此就想着写一个脚本程序来代替完成这项工作，也就是本程序的来由。

使用程序时，需要提供nutaku账号，并且要保证处于科学上网状态；程序包含了通知、重试机制，理论上只要启动之后，就无需再关注，金币会自动入账，但也保不准有时网络或者程序犯病（如断网、梯子大姨妈等导致的无法访问网站），因此最好时不时留意一下邮箱通知，以免出现漏签的情况。

## 配置信息
> src/config.txt
```text
# 账号相关（邮箱、密码）
# 本程序不会收集&存储任何与账号相关的数据
[account]
email=你的账号
password=你的密码

# 网络设置
[network]
# 代理&梯子（on=启用；off=关闭）
proxy=off

# 其他设置
[settings]
# 日志（on=启用；off=关闭）
log=on
# 调试模式（on=启用；off=关闭）
debug=on
# 邮箱通知；以当前账号为准（on=启用；off=关闭）
email_notification=on
# 邮件通知频次（day=每日；week=每周；month=每月）
# 在指定规则周期内的第一个时间点发送邮件通知，即是说，若规则为"week"，则会在周一进行通知；"month"在每月一号通知
# 除day外，其他参数配置会在签到全部完成时进行一次额外通知（实际上其内容是'上一次'签到的结果）
email_notification_strategy=week
# 签到重试次数；当由于网络或其他因素导致签到失败时，程序会自动进行重试
retrying=5
# 重试间隔（单位，分钟）
retrying_interval=10
# 执行时间（以24小时制为准，00:00-23:59；在指定的时间（如'9,20:30'，则为'9:30'和'20:30'两个时间点）执行任务，但不一定准确，比如由于电脑进入休眠/睡眠状态时，程序会停止运行，此时就会导致延迟执行）
# 如果在某个时间点已经完成签到，则其他时间点不会再次签到，多个时间点只是为了增加容错
execution_time=9,20:15
# 执行容错时间（单位，分钟）
misfire_grace_time=600
# 执行模式（1=默认，程序持续运行；2=执行完后退出程序）
# 模式1适用于电脑不关机的情况；模式2适用于电脑日常关机的情况，可配合'开机启动'使用
execution_mode=1
# 连接超时时间（单位，秒）
connection_timeout=30

# 接口路径
[api]
# 邮件通知接口
email_notification=http://g0wg60y8.shenzhuo.vip:29895/0/easyshop/portal/email/notification
```

## 运行

> python src/main.py

打包后再运行也ok，亦或是下载最新的[发布版](https://github.com/xxzhiwei/automated-redemption-for-nutaku-daily-rewards/releases)。

## 打包

将项目打包为可执行文件，以脱离python环境运行（指的是不需要安装python及其依赖）。

pyinstaller并非跨平台，需要在对应的系统上执行，如在mac上只能打包为mac的可执行文件。

> python -m PyInstaller main.spec

## 项目依赖

1、导出

> pip3 list --format=freeze > requirements.txt

2、导入

> pip3 install -r requirements.txt

## 其他注意事项

0. 环境为python3.9
1. 本项目的工作流是基于tag，新增tag时，将会触发构建
2. 此外，工作流需要使用到pat，请自行创建一个，并应用（Settings -> Secrets and variables -> Actions -> New repository secret，命名为PAT_FOR_WORKFLOWS）
3. 由于pyinstaller模块特性的缘故，只有在指定平台下运行才能输出相应的可执行程序，即它依赖于平台的软件、架构等，如果用户所在环境与预设（release）不一致，很可能会无法运行

## 更新日志

2025-04

1、将execution_mode为1时，由当月签到完成后退出程序，改为持续运行

2024-11

1、修复了因日期判断错误无法正常重试签到的问题

2024-10

1、新增了日志文件（避免界面信息过多）

2024-09

1、新增了按规则进行邮件通知的特性
2、修复了无法正常主动退出程序的问题（ctrl+c）
3、优化了邮件通知策略

2024-08

1. 新增了每月领取金币的统计
2. 签到接口更改为动态获取
3. 邮箱通知时机更改为签到完成后

2024-07

1. 修复了重试次数没有重置的问题

2024-05

1. 处理了请求时自动应用系统代理（导致SSLError）的问题
2. 配置文件移除了服务器代理地址（默认情况下，会自动读取系统代理）

2024-04

1. 处理了首次请求页面失败，进入重试流程时，时间判断不正确的问题

2024-02

1. 修复了windows系统下，无法正确读取文件的问题
2. 修复了无法进行最后一次签到的问题
3. 修复了签到领取物件时，非金币而导致读取数据错误的问题

***

*再次声明，本程序不会收集&存储任何与账号相关的数据。*
