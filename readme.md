# automated-redemption-for-nutaku-daily-rewards

nutaku金币活动自动签到脚本。

最近n站出了个金币签到活动，经过粗略计算，最多可获取到一百八十+的金币，看着很馋...

但就是每天得打开网站点击签到有点烦人，几乎要月全勤才能拿完所有的奖励，因此就想着写一个脚本程序来代替完成这项工作，也就是本程序的来由。

使用程序时，需要提供nutaku账号，并且要保证处于科学上网状态；程序包含了通知、重试机制，理论上只要启动之后，就无需再关注，金币会自动入账，但也保不准有时网络或者程序犯病（如断网、梯子大姨妈等导致的无法访问网站），因此最好时不时留意一下邮箱通知，以免出现漏签的情况。

## 配置信息
> src/config.txt
```text
# 账号相关（邮箱、密码）
[account]
email=err0l@qq.com
password=12321

# 代理（梯子）
[network]
proxy=127.0.0.1:7890

# 其他设置
[settings]
# 邮箱通知；以当前账号为准（on=启用，off=关闭）
email_notification=on
# 签到重试次数；当由于网络或其他因素导致签到失败时，程序会自动进行重试
retrying=10
# 重试间隔（单位，分钟）
retrying_interval=10
# 执行时间（以24小时制为准，00:00-23:59）
execution_time=09:00
```

## 打包

将项目打包为可执行文件，以脱离python环境运行（指的是不需要安装python及其依赖）。

pyinstaller并非跨平台，需要在对应的系统上执行，如在mac上只能打包为mac的可执行文件，此外还要保证pyinstaller已经添加到系统路径中。

> pyinstaller main.spec

## 项目依赖

1、导出

> pip3 list --format=freeze > requirements.txt

2、导入

> pip3 install -r requirements.txt

*本程序不会收集任何与账号有关的信息，但会给账号邮箱发送消息（如果已开启了通知的话）。*
