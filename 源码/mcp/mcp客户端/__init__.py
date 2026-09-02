"""MCP 客户端桥接插件：连接到外部 MCP 服务器，并以其服务器限定公开名（`mcp__<serverName>__<rawName>`）把工具注册到 `ctx.tools`。

对齐上游 `mcp-client/src/index.ts`。公开面仅中文名。配置键与诊断英文字面量保持上游。本包不提供默认导出。
"""
import re,weakref#服务器名模式与根上下文到已占用名
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,整数字段,数字字段,布尔字段,列表字段,字典字段,常量字段,复合类型字段#配置字段
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """可等待则等待，否则原样返回。"""
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#方法
    if callable(等待):#可等待
        return 等待()#等待
    return 值#同步值
from .连接 import 重连默认值,解析重连策略,启动连接#重连与监督
from .工具 import 公开工具名,同步工具,MCP结果#工具桥接再导出

__all__=['名称','注入','配置','应用','公开工具名','同步工具','MCP结果','重连默认值','解析重连策略','启动连接']#仅中文公开名

名称='mcp-client'#Cordis 插件名（字面量）
注入=['tools']#依赖 tools 服务
默认工具调用超时毫秒=60000#默认工具调用超时
服务器名模式=re.compile(r'^[A-Za-z0-9_-]{1,32}$')#服务器名模式
已占用服务器名=weakref.WeakKeyDictionary()#根上下文到已占用服务器名

重连模式={#重连配置模式
    'enabled':布尔字段(默认值=重连默认值['enabled']),#是否启用重连
    'initialDelayMs':数字字段(最小=1,最大=定时器延迟上限毫秒,默认值=重连默认值['initialDelayMs']),#初始延迟
    'maxDelayMs':数字字段(最小=1,最大=定时器延迟上限毫秒,默认值=重连默认值['maxDelayMs']),#延迟上限
    'maxAttempts':整数字段(最小=1,默认值=重连默认值['maxAttempts']),#最大尝试次数
}#重连模式结束

配置=复合类型字段(#插件配置模式
    {#stdio 分支
        'transport':常量字段('stdio'),#固定为 stdio
        'serverName':字符串字段(可空=False,格式=服务器名模式),#必填服务器名
        'command':字符串字段(可空=False),#必填命令
        'args':列表字段(字符串字段(),默认值=[]),#默认空参数
        'env':字典字段[字符串字段(),字符串字段()](默认值={}),#默认空环境
        'cwd':字符串字段(默认值=''),#默认空工作目录
        'toolCallTimeoutMs':数字字段(默认值=默认工具调用超时毫秒),#默认调用超时
        'failOnStartupError':布尔字段(默认值=False),#默认启动失败不致命
        'reconnect':重连模式,#重连子模式
    },#stdio 对象结束
    {#streamable-http 分支
        'transport':常量字段('streamable-http'),#固定为 HTTP
        'serverName':字符串字段(可空=False,格式=服务器名模式),#必填服务器名
        'url':字符串字段(可空=False),#必填 URL
        'headers':字典字段[字符串字段(),字符串字段()](默认值={}),#默认空头
        'toolCallTimeoutMs':数字字段(默认值=默认工具调用超时毫秒),#默认调用超时
        'failOnStartupError':布尔字段(默认值=False),#默认启动失败不致命
        'reconnect':重连模式,#重连子模式
    },#HTTP 对象结束
)#配置结束

def 应用(上下文,配置值):#安装 MCP 客户端插件
    """连接一台 MCP 服务器，并在激活前发布其初始工具世代。"""
    服务器名=取字段(配置值,'serverName')#服务器命名空间
    重连=解析重连策略(取字段(配置值,'reconnect'),'mcp-client('+服务器名+'): reconnect')#解析并校验重连策略
    def 预留名():#预留 serverName
        """重复的 serverName 在加载时让本实例失败。"""
        名称集=已占用服务器名.get(上下文.root)#取出本应用的已占用名
        if 名称集 is None:#尚无集合
            名称集=set()#新建占用集合
            已占用服务器名[上下文.root]=名称集#挂到根上下文
        if 服务器名 in 名称集:#命名空间已被占用
            raise Exception('mcp-client: serverName "'+服务器名+'" is already in use by another mcp-client instance — pick a unique serverName in cordis.yml')#配置错误
        名称集.add(服务器名)#占用本服务器名
        def 释放():#拆除时释放
            """释放本服务器名。"""
            名称集.discard(服务器名)#释放
        return 释放#拆除器
    上下文.effect(预留名,'mcp-client.serverName')#effect 标签
    连接=启动连接(上下文,配置值,重连)#启动连接监督
    def 装连接():#注册连接拆除
        """拆除监督器。"""
        def 拆连接():#拆除
            """拆除监督器。"""
            连接['dispose']()#拆除监督器
        return 拆连接#拆除器
    上下文.effect(装连接,'mcp-client.connection')#effect 标签
    结果=解开(连接['ready'])#等待初次尝试结算
    if 取字段(结果,'error') is not None and 取字段(配置值,'failOnStartupError'):#启动失败且配置为致命
        错误=Exception('mcp-client('+服务器名+'): initial connection or tool synchronization failed')#拒绝激活
        raise 错误 from 取字段(结果,'error')#挂上原因
