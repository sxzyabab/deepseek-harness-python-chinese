"""MCP 客户端桥接插件：连接外部 MCP 服务器，并以服务器限定公开名注册其工具到 tools 服务。"""
import re,weakref
from ...依赖.schemastery import 字符串字段,整数字段,数字字段,布尔字段,列表字段,字典字段,常量字段,复合类型字段
from ...内核.作用域 import 获取作用域
from ...工具.超时 import 定时器延迟上限毫秒
from .连接 import 默认最大指令字节,重连默认值,解析重连策略,启动连接
from .工具桥接 import 公开工具名,同步工具,MCP结果,创建mcp工具定义
from .传输 import MCP错误
from .服务器上下文 import 登记服务器上下文

__all__=['名称','依赖','配置','应用','公开工具名','同步工具','MCP结果','创建mcp工具定义','重连默认值','解析重连策略','启动连接']

名称='mcp-client'
依赖=['tools']
默认工具调用超时毫秒=60000
服务器名模式=re.compile(r'^[A-Za-z0-9_-]{1,32}\Z',re.ASCII)
已占用服务器名=weakref.WeakKeyDictionary()#根上下文到已占用服务器名

重连模式={
    'enabled':布尔字段(默认值=重连默认值['enabled']),
    'initialDelayMs':数字字段(最小=1,最大=定时器延迟上限毫秒,默认值=重连默认值['initialDelayMs']),
    'maxDelayMs':数字字段(最小=1,最大=定时器延迟上限毫秒,默认值=重连默认值['maxDelayMs']),
        'maxAttempts':整数字段(最小=1,最大=9007199254740991,默认值=重连默认值['maxAttempts']),
}

配置=复合类型字段(
    {#stdio 分支
        'transport':常量字段('stdio'),
        'serverName':字符串字段(可空=False,格式=服务器名模式),
        'command':字符串字段(可空=False),
        'args':列表字段(字符串字段(),默认值=[]),
        'env':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),
        'cwd':字符串字段(默认值=''),
        'toolCallTimeoutMs':数字字段(默认值=默认工具调用超时毫秒),
        'failOnStartupError':布尔字段(默认值=False),
        'maxInstructionBytes':数字字段(最小=1,默认值=默认最大指令字节),
        'reconnect':重连模式,
    },
    {#streamable-http 分支
        'transport':常量字段('streamable-http'),
        'serverName':字符串字段(可空=False,格式=服务器名模式),
        'url':字符串字段(可空=False),
        'headers':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),
        'toolCallTimeoutMs':数字字段(默认值=默认工具调用超时毫秒),
        'failOnStartupError':布尔字段(默认值=False),
        'maxInstructionBytes':数字字段(最小=1,默认值=默认最大指令字节),
        'reconnect':重连模式,
    },
)

def 应用(上下文,配置值):
    """连接一台 MCP 服务器，并在激活前发布其初始工具世代。配置为 dict。"""
    服务器名=配置值['serverName']
    拥有者=获取作用域(上下文)
    if 拥有者 is None:
        拥有者=上下文.根
    重连=解析重连策略(配置值['reconnect'] if 'reconnect' in 配置值 else None,'mcp-client('+服务器名+'): reconnect')
    def 预留名():
        """重复的 serverName 在加载时让本实例失败。"""
        if 拥有者 not in 已占用服务器名:
            名称集=set()
            已占用服务器名[拥有者]=名称集
        else:
            名称集=已占用服务器名[拥有者]
        if 服务器名 in 名称集:
            raise MCP错误('mcp-client: serverName "'+服务器名+'" is already in use by another mcp-client instance — pick a unique serverName in cordis.yml')
        名称集.add(服务器名)
        def 释放():
            """释放本服务器名。"""
            名称集.discard(服务器名)
        return 释放
    上下文.副作用(预留名,'mcp-client.serverName')
    连接=启动连接(上下文,配置值,重连)
    登记服务器上下文(上下文,服务器名,连接)
    已拆除=False
    def 拆除():
        """拆除监督器；重复调用复用第一次。"""
        nonlocal 已拆除
        if 已拆除:
            return
        已拆除=True
        连接['dispose']()
    def 卸载时拆除(纤程对象):
        """Cordis 在未完成的 apply 之前宣布卸载时先关传输。"""
        if 纤程对象 is not 上下文.纤程 or 纤程对象.编号 is not None:
            return
        拆除()
    上下文.监听('internal/plugin',卸载时拆除,{'全局':True})
    def 装连接():
        """注册连接拆除。"""
        return 拆除
    上下文.副作用(装连接,'mcp-client.connection')
    结果=连接['ready'].等待()
    if 'error' in 结果 and 结果['error'] is not None and 配置值['failOnStartupError']:
        错误=MCP错误('mcp-client('+服务器名+'): initial connection or tool synchronization failed')
        raise 错误 from 结果['error']

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
