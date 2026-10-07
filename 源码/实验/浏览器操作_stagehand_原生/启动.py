from functools import partial as 偏函数
import os,tempfile,threading#配置目录、进程与端点
from ...基础设施.js特性 import PromiseEX as 期约#关闭与端点的异步结果
from ...子进程.子进程 import 擦洗父环境#擦洗环境
from ...工具.超时 import 等待中止#中止类已禁用

__all__=['启动chromium']#仅中文公开名

def 启动chromium(配置,信号):#拥有 Chromium
    '用擦洗环境与操作系统分配的调试端口启动 Chromium。返回期约，兑现值是含 endpoint 与 close 的 dict；close 返回期约'
    from puppeteer_browsers import Browser,ChromeReleaseChannel,CDP_WEBSOCKET_ENDPOINT_REGEX,computeSystemExecutablePath,launch#浏览器启动
    若已中止则抛出(信号)#调用前已中止则不启动
    if 'executablePath' not in 配置:#未指定可执行文件
        可执行=computeSystemExecutablePath({'browser':Browser.CHROME,'channel':ChromeReleaseChannel.STABLE})#系统稳定版
    else:#指定了可执行文件
        可执行=配置['executablePath']#使用指定路径
    配置目录=tempfile.mkdtemp(prefix='dsh-stagehand-chrome-')#本次浏览器独占的用户数据目录
    浏览器=None#启动成功后才有进程
    已关=None#子进程 close 事件的结果；启动失败时保持 None
    关闭中=None#共享的关闭结果，首次关闭时赋值
    def 删除配置目录(已关闭值=None):#删目录
        '子进程已关闭后，自底向上删除配置目录'
        for 根目录,目录表,文件表 in os.walk(配置目录,topdown=False):#自底向上遍历
            for 文件名 in 文件表:#该层文件
                os.remove(os.path.join(根目录,文件名))#删文件
            for 目录名 in 目录表:#该层子目录
                os.rmdir(os.path.join(根目录,目录名))#删已清空的子目录
        os.rmdir(配置目录)#最后删根目录
    def 关():#杀进程树
        '杀掉自有进程树、等子进程关闭并移除配置目录。返回共享的关闭结果'
        nonlocal 关闭中#共享关闭结果在此赋值
        if 关闭中 is not None:#已经在关闭
            return 关闭中#共享同一个结果
        if 浏览器 is not None:#进程已启动
            浏览器.kill()#杀掉进程树
        if 已关 is None:#进程没有启动成功，没有 close 事件可等
            等待关闭=期约()#直接视为已关闭
            等待关闭.解决(None)#没有进程可等
        else:#进程已启动
            等待关闭=已关#等 close 事件
        关闭中=等待关闭.然后(删除配置目录)#先等子进程关闭再删目录
        return 关闭中#共享关闭结果
    def 关闭后抛出(错误,已关闭值=None):#关完
        '进程与目录清理完成后抛出'
        若已中止则抛出(信号)#中止原因优先
        raise 错误#否则抛出原错误
    def 回滚失败(错误):#失败回滚
        '关闭自有进程后抛出原错误；信号已中止则抛出中止原因'
        return 关().然后(偏函数(关闭后抛出,错误))#先清理再抛出
    try:#启动并等待调试端点
        若已中止则抛出(信号)#启动前再确认一次
        参数=[#命令行参数
            '--remote-debugging-port=0','--enable-unsafe-extension-debugging','--remote-allow-origins=*',
            '--no-first-run','--no-default-browser-check',f'--user-data-dir={配置目录}',
        ]#参数
        if 配置.get('headless'):#要求无窗口
            参数.append('--headless=new')#无窗口
        参数.append('about:blank')#初始空白页
        浏览器=launch({#启动
            'executablePath':可执行,#可执行文件
            'args':参数,#命令行参数
            'env':擦洗父环境(),#擦洗后的环境
            'handleSIGINT':False,'handleSIGTERM':False,'handleSIGHUP':False,#不接管信号
        })#启动结束
        子进程=浏览器.nodeProcess#底层子进程
        已关=期约()#子进程 close 时兑现
        def 子进程已关闭():#close 事件
            '子进程关闭事件：兑现已关'
            已关.解决(None)#关闭流程可以继续
        子进程.once('close',子进程已关闭)#失败的启动也会触发 close
        if 信号 is not None:#调用方给了信号
            def 监视():#等中止
                '信号置位后关闭自有浏览器'
                等待中止(信号)#阻塞到信号置位
                关()#杀进程并清理
            threading.Thread(target=监视,daemon=True).start()#后台监视中止
        端点结果=期约()#调试端点出现时兑现
        def 等行():#等 CDP
            '阻塞等到调试端点输出，结算端点结果'
            try:#等端点
                端点结果.解决(浏览器.waitForLineOutput(CDP_WEBSOCKET_ENDPOINT_REGEX,配置['operationTimeoutMs']))#超时由配置给定
            except Exception as 错误:#等待失败或超时
                端点结果.拒绝(错误)#交给启动结果
        threading.Thread(target=等行,daemon=True).start()#后台等端点
    except Exception as 错误:#启动阶段同步失败
        return 回滚失败(错误)#清理后抛出
    def 交出自有浏览器(端点):#端点就绪
        '确认未中止后交出自有浏览器'
        若已中止则抛出(信号)#等待端点期间被取消
        return {'endpoint':端点,'close':关}#自有浏览器
    return 端点结果.然后(交出自有浏览器).捕获(回滚失败)#端点失败或被取消都回滚
