from functools import partial as 偏函数
from urllib.parse import urlparse#拆端点
import threading#中止监视
from ...依赖.schemastery import 复合类型字段,常量字段,布尔字段,字符串字段,数字字段#配置字段
from ...浏览器操作.浏览器操作.标识构造 import 浏览器操作提供方名#提供方名
from ...mcp import mcp客户端#MCP 客户端插件
from ...内核.作用域 import 创建作用域#铸造作用域
from .异常 import 浏览器操作运行时错误#异常
from . import 会话资源#资源表

__all__=['浏览器mcp配置','校验浏览器mcp配置','挂会话mcp']#仅中文公开名

浏览器mcp配置=复合类型字段(#launch 或 attach
    {#launch
        'mode':常量字段('launch'),#启动
        'headless':布尔字段(默认值=True),#无窗
        'executablePath':字符串字段(),#可执行
        'toolCallTimeoutMs':数字字段(最小=1),#超时
    },#launch 结束
    {#attach
        'mode':常量字段('attach'),#附着
        'endpoint':字符串字段(可空=False),#端点
        'toolCallTimeoutMs':数字字段(最小=1),#超时
    },#attach 结束
)#配置结束

def 校验浏览器mcp配置(配置):#激活前校验端点
    '附着模式须为合法 HTTP(S)/WS(S) URL。配置是 dict'
    if 配置['mode']!='attach':#启动
        return#过
    端点=配置['endpoint']#原文
    解析=urlparse(端点)#解析
    if 解析.scheme not in ('http','https','ws','wss') or ' ' in 端点 or '\t' in 端点:#非法
        raise 浏览器操作运行时错误('browser endpoint must be a valid HTTP(S) or WS(S) URL without whitespace')#失败

def 挂会话mcp(上下文,选项):#每 Session 一台 MCP
    '等未来智能体创建时接入一台 MCP 客户端。选项是 dict'
    箱={'资源':None}#延迟赋值
    客户={}#智能体 → 状态
    工具前缀='mcp__'+选项['name']+'__'#工具前缀
    资源工具={'list_mcp_resources','list_mcp_resource_templates','read_mcp_resource'}#共享资源工具
    停止与刷新标志={'停止中':False,'刷新中':False}#卸载与刷新

    def 刷新阻塞掩码():#挡住继承工具
        '忙附着时去掉本提供方工具'
        if 停止与刷新标志['停止中'] or 停止与刷新标志['刷新中']:#重入
            return#停
        停止与刷新标志['刷新中']=True#进
        try:#扫
            for 智能体,状态 in list(客户.items()):#逐个
                if 状态['status']!='blocked':#非阻塞
                    continue#下
                继承=[工具 for 工具 in 上下文.tools.schemas(智能体) if 工具['name'].startswith(工具前缀)]#本前缀，上游 filter 一行
                if len(继承)==0:#无
                    continue#下
                if 'mask' not in 状态:#尚未铸造
                    状态['mask']=创建作用域(上下文,智能体)#铸造
                状态['mask'].上下文.tools.restrict({'deny':[工具['name'] for 工具 in 继承]})#拒绝
        finally:#出
            停止与刷新标志['刷新中']=False#出

    def 抛出原错误(错误,已拆除值=None):#拆完
        '作用域拆除完成后抛出原错误'
        raise 错误#原样抛出
    def 取消打开(状态):#信号
        '拆除作用域，并记下拆除结果'
        状态['取消结果']=状态['已铸'].原始拆除()#拆除
    def 监视打开(状态,信号):#等中止
        '置位后取消'
        if hasattr(信号,'wait'):#Event
            信号.wait()#等待
            取消打开(状态)#拆
    def 回滚失败(状态,错误):#失败回滚
        '拆除作用域后抛出原错误；信号已先触发拆除则复用其结果'
        if 状态['取消结果'] is not None:#信号已触发拆除
            return 状态['取消结果'].然后(偏函数(抛出原错误,错误))#等它拆完
        return 状态['已铸'].原始拆除().然后(偏函数(抛出原错误,错误))#否则现在拆除
    def 执行守卫(智能体,执行,下一):#tools/execute
        '工具必须属于本 Session'
        if not 执行['name'].startswith(工具前缀):#外
            return 下一()#过
        if 执行.get('agent') is not 智能体:#他者
            if 上下文.tools.get(执行['name'],执行.get('agent')) is not 上下文.tools.get(执行['name'],智能体):#不同定义
                return 下一()#过
            raise 浏览器操作运行时错误(选项['name']+': browser tool belongs to another Session')#他者
        return 下一()#本
    def 关作用域(智能体,已铸):#关作用域
        '摘客户表，返回作用域拆除的期约'
        if 智能体 in 客户:#有
            del 客户[智能体]#摘
        return 已铸.原始拆除()#拆除
    def 交出资源(状态,信号,插件值):#MCP 客户端就绪
        '确认未中止后交出资源'
        若已中止则抛出(信号)#中止
        return {'value':状态['已铸'],'close':偏函数(关作用域,状态['智能体'],状态['已铸'])}#资源
    def 打开(智能体,信号):#获取作用域
        '在智能体作用域挂 MCP 客户端。返回期约，兑现值是含 value 与 close 的资源 dict；失败时已回滚'
        已铸=创建作用域(上下文,智能体)#铸造
        状态={'已铸':已铸,'取消结果':None,'智能体':智能体}#本次打开
        if 信号 is not None:#有信号
            threading.Thread(target=偏函数(监视打开,状态,信号),daemon=True).start()#监视
        try:#挂客户端
            若已中止则抛出(信号)#中止
            已铸.上下文.on('tools/execute',偏函数(执行守卫,智能体))#守卫
            连接={#MCP 配置
                'transport':'stdio',#stdio
                'serverName':选项['name'],#名
                'command':选项['command'],#命令
                'args':选项['args'],#参数
                'failOnStartupError':True,#启动失败致命
                'reconnect':{'enabled':False},#不重连
            }#配置
            if 选项.get('env') is not None:#环境
                连接['env']=选项['env']#覆盖
            头=智能体.session.header#会话头
            if 头.get('cwd') is not None:#工作目录
                连接['cwd']=头['cwd']#cwd
            if 选项.get('toolCallTimeoutMs') is not None:#超时
                连接['toolCallTimeoutMs']=选项['toolCallTimeoutMs']#超时
            客户插件=已铸.上下文.启动插件(mcp客户端,连接)#挂客户端
        except Exception as 错误:#启动阶段同步失败
            return 回滚失败(状态,错误)#回滚后抛出
        return 客户插件.等待().然后(偏函数(交出资源,状态,信号)).捕获(偏函数(回滚失败,状态))#等客户端启动完成，失败或中止都回滚

    def 拆除后清理(撤销,已拆除值=None):#资源拆完
        '全部服务器关闭后清客户表并放回登记'
        客户.clear()#清
        撤销()#放登记
    def 卸会话(撤销):#卸载
        '先关服务器。返回期约，登记在服务器全部关闭后才放回'
        停止与刷新标志['停止中']=True#停
        return 箱['资源'].拆除().然后(偏函数(拆除后清理,撤销))#拆
    def 会话寿命():#登记提供方与资源
        '卸载先关服务器再放登记'
        撤销=上下文.browserUse.登记(浏览器操作提供方名(选项['name']))#占用
        箱['资源']=会话资源(上下文,{#资源表
            'label':选项['name'],#诊断名
            'exclusive':选项['exclusive'],#独占
            'open':打开,#获取
        })#表
        return 偏函数(卸会话,撤销)#拆除器
    上下文.副作用(会话寿命,选项['name']+'.sessions')#会话寿命

    def 卸激活(智能体,状态):#卸
        '摘客户并拆掩码；有掩码时返回其拆除的期约'
        if 智能体 in 客户:#有
            del 客户[智能体]#摘
        掩码=状态.get('mask')#掩码
        if 掩码 is not None:#有
            return 掩码.拆除()#拆
    def 激活拆除(智能体,状态):#作用域拆除
        '摘客户并拆掩码'
        return 偏函数(卸激活,智能体,状态)#拆除器
    def 登记客户(智能体,状态,句柄):#获取完成
        '资源就绪后记下本智能体的客户状态'
        客户[智能体]=状态#记下
    def 智能体已创建(载荷):#agent/created
        'prepend：忙则挡，否则获取'
        智能体=载荷['agent']#智能体
        信号=载荷['signal'] if 'signal' in 载荷 else None#信号
        状态={'status':'ready' if 箱['资源'].可用(智能体) else 'blocked'}#状态
        智能体.ctx.副作用(偏函数(激活拆除,智能体,状态),选项['name']+'.activation')#激活
        if 状态['status']=='blocked':#忙
            客户[智能体]=状态#记下
            刷新阻塞掩码()#掩码
            return#停
        return 箱['资源'].取(智能体,信号).然后(偏函数(登记客户,智能体,状态))#等资源就绪
    上下文.on('agent/created',智能体已创建,{'prepend':True})#创建
    上下文.on('tools/change',刷新阻塞掩码)#工具变更

    def 还原执行信号(执行,原):#结算后
        '下一结算后还原原信号'
        执行['signal']=原#还原
    def 队列内执行(执行,下一,_作用域,合成):#队列内
        '换 signal 再 next'
        原=执行.get('signal')#原信号
        执行['signal']=合成#合成
        return 下一().最终(偏函数(还原执行信号,执行,原))#下一，无论成败都还原
    def 执行包装(执行,下一):#tools/execute
        '本前缀或本服务器资源工具走资源队列'
        参数=执行['arguments'] if 'arguments' in 执行 else None#参数
        本资源=执行['name'] in 资源工具 and isinstance(参数,dict) and 参数.get('server')==选项['name']#资源工具
        if not 执行['name'].startswith(工具前缀) and not 本资源:#无关
            return 下一()#过
        if 'agent' not in 执行 or 执行['agent'] not in 客户 or 客户[执行['agent']]['status']!='ready':#非本
            raise 浏览器操作运行时错误(选项['name']+': browser tool belongs to another Session')#他者
        智能体=执行['agent']#调用方
        return 箱['资源'].运行(智能体,执行['signal'],偏函数(队列内执行,执行,下一))#队列
    上下文.on('tools/execute',执行包装)#包装

    def 过滤段(智能体,结果):#下游组装完成
        '下游组装完成后，按本 Session 可见性过滤本提供方的段'
        if 智能体 is None or (智能体 in 客户 and 客户[智能体]['status']=='ready'):#可见
            return 结果#原样
        段表=[段 for 段 in 结果['sections'] if 段['name']!='mcp:'+选项['name']]#上游 filter 一行
        拷=dict(结果)#拷
        拷['sections']=段表#新段
        return 拷#组装
    def 组装提示(_组装,选项包,下一):#system-prompt/assemble
        '非 ready 去掉 mcp: 段'
        智能体=选项包.get('agent') if isinstance(选项包,dict) else None#智能体
        return 下一().然后(偏函数(过滤段,智能体))#等下游组装
    上下文.on('system-prompt/assemble',组装提示)#组装
