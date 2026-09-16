from urllib.parse import urlparse#拆端点
import threading#中止监视
from ...依赖.schemastery import 复合类型字段,常量字段,布尔字段,字符串字段,数字字段#配置字段
from ...浏览器操作.浏览器操作.标识构造 import 浏览器操作提供方名#提供方名
from ...mcp import mcp客户端#MCP 客户端插件
from ...内核.作用域 import 创建作用域#铸造作用域
from ...工具.超时 import 若已中止则抛出#中止
from . import 会话资源,浏览器操作运行时错误#资源表与异常

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
    """附着模式须为合法 HTTP(S)/WS(S) URL。配置是 dict。"""
    if 配置['mode']!='attach':#启动
        return#过
    端点=配置['endpoint']#原文
    解析=urlparse(端点)#解析
    if 解析.scheme not in ('http','https','ws','wss') or ' ' in 端点 or '\t' in 端点:#非法
        raise 浏览器操作运行时错误('browser endpoint must be a valid HTTP(S) or WS(S) URL without whitespace')#失败

def 挂会话mcp(上下文,选项):#每 Session 一台 MCP
    """等未来智能体创建时接入一台 MCP 客户端。选项是 dict。"""
    箱={'资源':None}#延迟赋值
    客户={}#智能体 → 状态
    工具前缀='mcp__'+选项['name']+'__'#工具前缀
    资源工具={'list_mcp_resources','list_mcp_resource_templates','read_mcp_resource'}#共享资源工具
    旗={'停止中':False,'刷新中':False}#卸载与刷新

    def 刷新阻塞掩码():#挡住继承工具
        """忙附着时去掉本提供方工具。"""
        if 旗['停止中'] or 旗['刷新中']:#重入
            return#停
        旗['刷新中']=True#进
        try:#扫
            for 智能体,状态 in list(客户.items()):#逐个
                if 状态['status']!='blocked':#非阻塞
                    continue#下
                继承=[]#本前缀
                for 工具 in 上下文.tools.schemas(智能体):#schemas
                    if 工具['name'].startswith(工具前缀):#本提供方
                        继承.append(工具)#记下
                if len(继承)==0:#无
                    continue#下
                if 状态.get('mask') is None:#尚未铸造
                    状态['mask']=创建作用域(上下文,智能体)#铸造
                状态['mask'].上下文.tools.restrict({'deny':[工具['name'] for 工具 in 继承]})#拒绝
        finally:#出
            旗['刷新中']=False#出

    def 打开(智能体,信号):#获取作用域
        """在智能体作用域挂 MCP 客户端。"""
        已铸=创建作用域(上下文,智能体)#铸造
        已取消=False#信号是否已拆
        def 取消时():#信号
            """拆除作用域。"""
            nonlocal 已取消#改
            已取消=True#记下
            已铸.原始拆除()#拆除
        def 监视():#等中止
            """置位后取消。"""
            if hasattr(信号,'wait'):#Event
                信号.wait()#等待
                取消时()#拆
        if 信号 is not None:#有信号
            threading.Thread(target=监视).start()#监视
        try:#挂客户端
            若已中止则抛出(信号)#中止
            def 执行守卫(执行,下一):#tools/execute
                """工具必须属于本 Session。"""
                if not 执行['name'].startswith(工具前缀):#外
                    return 下一()#过
                if 执行.get('agent') is not 智能体:#他者
                    if 上下文.tools.get(执行['name'],执行.get('agent')) is not 上下文.tools.get(执行['name'],智能体):#不同定义
                        return 下一()#过
                    raise 浏览器操作运行时错误(选项['name']+': browser tool belongs to another Session')#他者
                return 下一()#本
            已铸.上下文.on('tools/execute',执行守卫)#守卫
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
            已铸.上下文.启动插件(mcp客户端,连接)#挂客户端
            若已中止则抛出(信号)#中止
            def 关():#关作用域
                """摘客户表。"""
                if 智能体 in 客户:#有
                    del 客户[智能体]#摘
                return 已铸.原始拆除()#拆除
            return {'value':已铸,'close':关}#资源
        except Exception as 错误:#失败
            if not 已取消:#尚未拆
                已铸.原始拆除()#回滚
            raise 错误#原样

    def 会话寿命():#登记提供方与资源
        """卸载先关服务器再放登记。"""
        撤销=上下文.browserUse.登记(浏览器操作提供方名(选项['name']))#占用
        箱['资源']=会话资源(上下文,{#资源表
            'label':选项['name'],#诊断名
            'exclusive':选项['exclusive'],#独占
            'open':打开,#获取
        })#表
        def 卸():#卸载
            """先关服务器。"""
            旗['停止中']=True#停
            箱['资源'].拆除()#拆
            客户.clear()#清
            撤销()#放登记
        return 卸#拆除器
    上下文.副作用(会话寿命,选项['name']+'.sessions')#会话寿命

    def 智能体已创建(载荷):#agent/created
        """prepend：忙则挡，否则获取。"""
        智能体=载荷['agent']#智能体
        信号=载荷['signal'] if 'signal' in 载荷 else None#信号
        状态={'status':'ready' if 箱['资源'].可用(智能体) else 'blocked'}#状态
        def 激活拆除():#作用域拆除
            """摘客户并拆掩码。"""
            def 卸():#卸
                """dispose mask。"""
                if 智能体 in 客户:#有
                    del 客户[智能体]#摘
                掩=状态.get('mask')#掩码
                if 掩 is not None:#有
                    掩.拆除()#拆
            return 卸#拆除器
        智能体.ctx.副作用(激活拆除,选项['name']+'.activation')#激活
        if 状态['status']=='blocked':#忙
            客户[智能体]=状态#记下
            刷新阻塞掩码()#掩码
            return#停
        箱['资源'].取(智能体,信号)#获取
        客户[智能体]=状态#记下
    上下文.on('agent/created',智能体已创建,{'prepend':True})#创建
    上下文.on('tools/change',刷新阻塞掩码)#工具变更

    def 执行包装(执行,下一):#tools/execute
        """本前缀或本服务器资源工具走资源队列。"""
        参数=执行['arguments'] if 'arguments' in 执行 else None#参数
        本资源=执行['name'] in 资源工具 and isinstance(参数,dict) and 参数.get('server')==选项['name']#资源工具
        if not 执行['name'].startswith(工具前缀) and not 本资源:#无关
            return 下一()#过
        智能体=执行.get('agent')#调用方
        if 智能体 is None or 智能体 not in 客户 or 客户[智能体]['status']!='ready':#非本
            raise 浏览器操作运行时错误(选项['name']+': browser tool belongs to another Session')#他者
        def 操作(_作用域,合成):#队列内
            """换 signal 再 next。"""
            原=执行.get('signal')#原信号
            执行['signal']=合成#合成
            try:#下一
                return 下一()#下一
            finally:#还原
                执行['signal']=原#还原
        return 箱['资源'].运行(智能体,执行['signal'],操作)#队列
    上下文.on('tools/execute',执行包装)#包装

    def 组装提示(_组装,选项包,下一):#system-prompt/assemble
        """非 ready 去掉 mcp: 段。"""
        结果=下一()#下游
        智能体=选项包.get('agent') if isinstance(选项包,dict) else None#智能体
        if 智能体 is None or (智能体 in 客户 and 客户[智能体]['status']=='ready'):#可见
            return 结果#原样
        段表=[]#过滤
        for 段 in 结果['sections']:#逐段
            if 段['name']!='mcp:'+选项['name']:#保留
                段表.append(段)#收下
        拷=dict(结果)#拷
        拷['sections']=段表#新段
        return 拷#组装
    上下文.on('system-prompt/assemble',组装提示)#组装
