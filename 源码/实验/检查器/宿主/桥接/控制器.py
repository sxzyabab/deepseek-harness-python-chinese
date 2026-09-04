"""拥有 Inspector Worker 与 Host 观测源的 Host 控制器。

对齐上游 `host/bridge/controller.ts`。公开面仅中文名。
"""
import os,secrets,uuid#环境与随机
from ...共享.桥接.版本 import 检查器协议版本#协议版本
from ..检视.网络 import 网络主题,安装请求观察器#fetch采集
from .传输 import 宿主检查器源#Host源
from .生命周期 import 检查器工作者生命周期#Worker生命周期

__all__=[#仅中文公开名
    '检查器选项','检查器规格','检查器端点','检查器句柄',
    '解析检查器选项','启动检查器',
]#公开面结束

默认最大请求体字节=8*1024*1024#默认请求体上限
默认最大响应体字节=32*1024*1024#默认响应体上限
默认最大体分块字节=48*1024#默认分块上限
默认最大日志字节=256*1024*1024#默认日志总字节
默认最大保留请求=2000#默认保留请求数
默认最大源帧字节=128*1024#默认帧字节上限
默认最大每帧源记录=128#默认每帧记录数
默认最大排队记录=2048#默认队列记录上限
默认最大排队字节=16*1024*1024#默认队列字节上限
默认启动超时毫秒=10000#默认启动超时
默认停止超时毫秒=5000#默认停止超时
默认客户端重连基数毫秒=250#默认重连基数
默认客户端重连最大毫秒=5000#默认重连上限
默认客户端运行时超时毫秒=30000#默认Client运行时超时
默认查询超时毫秒=10000#默认查询超时
默认最大客户端运行时对象=10000#默认Client对象上限
默认最大客户端运行时属性=2000#默认属性上限
默认最大客户端源字节=8*1024*1024#默认源字节上限
默认最大cordis节点=2048#默认Cordis节点上限
默认最大断联cordis树=8#默认断联树上限

def 自然数(值,名,允许零=False):#校验自然数
    """校验自然数。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<(0 if 允许零 else 1):#非法
        raise Exception(f'inspector: {名} must be {"a non-negative" if 允许零 else "a positive"} safe integer')#拒绝
    return 值#返回

class 检查器选项:#检查器选项
    """面向用户的 Host 选项；每个内存与生命周期边界均可配置。"""
    def __init__(自身,**字段):#构造
        """保存部分配置。"""
        for 键,值 in 字段.items():#逐字段
            setattr(自身,键,值)#写入

class 检查器规格:#已解析规格
    """一次运行中的 Inspector 使用的完整已解析选项。"""
    def __init__(自身,**字段):#构造
        """保存完整配置。"""
        for 键,值 in 字段.items():#逐字段
            setattr(自身,键,值)#写入

class 检查器端点:#检查器端点
    """一个已绑定 Worker 的地址与浏览器 bootstrap。"""
    def __init__(自身,httpUrl,webSocketDebuggerUrl,devtoolsFrontendUrl,client):#构造
        """保存端点字段。"""
        自身.httpUrl=httpUrl#HTTP地址
        自身.webSocketDebuggerUrl=webSocketDebuggerUrl#调试WebSocket
        自身.devtoolsFrontendUrl=devtoolsFrontendUrl#DevTools前端
        自身.client=client#Client引导

class 检查器句柄:#检查器句柄
    """运行中的 Host 侧 Inspector 所有者。"""
    def __init__(自身,endpoint,source,关闭):#构造
        """保存端点、源与关闭器。"""
        自身.endpoint=endpoint#端点
        自身.source=source#观测连接
        自身.关闭=关闭#关闭函数

    def close(自身):#关闭
        """停止采集并等待 Worker 释放每个 socket 与 V8 session。"""
        return 自身.关闭()#关闭

def 解析检查器选项(选项=None):#解析选项
    """解析并校验全部随部署变化的 Inspector 选择。"""
    if 选项 is None:#缺省
        选项={}#空
    def 取(键,缺省):#取字段
        """取字段。"""
        if isinstance(选项,dict):#映射
            return 选项[键] if 键 in 选项 else 缺省#键
        return getattr(选项,键,缺省)#属性
    规格=检查器规格(#组装规格
        host=取('host','127.0.0.1'),#主机
        port=自然数(取('port',0),'port',True),#端口可零
        clientOrigins=list(取('clientOrigins',[])),#origin副本
        captureFetch=取('captureFetch',True),#默认采集
        maxRequestBodyBytes=自然数(取('maxRequestBodyBytes',默认最大请求体字节),'maxRequestBodyBytes'),#请求体
        maxResponseBodyBytes=自然数(取('maxResponseBodyBytes',默认最大响应体字节),'maxResponseBodyBytes'),#响应体
        maxBodyChunkBytes=自然数(取('maxBodyChunkBytes',默认最大体分块字节),'maxBodyChunkBytes'),#分块
        maxJournalBytes=自然数(取('maxJournalBytes',默认最大日志字节),'maxJournalBytes'),#日志
        maxRetainedRequests=自然数(取('maxRetainedRequests',默认最大保留请求),'maxRetainedRequests'),#保留数
        maxSourceFrameBytes=自然数(取('maxSourceFrameBytes',默认最大源帧字节),'maxSourceFrameBytes'),#帧字节
        maxSourceRecordsPerFrame=自然数(取('maxSourceRecordsPerFrame',默认最大每帧源记录),'maxSourceRecordsPerFrame'),#每帧记录
        maxQueuedRecords=自然数(取('maxQueuedRecords',默认最大排队记录),'maxQueuedRecords'),#队列记录
        maxQueuedBytes=自然数(取('maxQueuedBytes',默认最大排队字节),'maxQueuedBytes'),#队列字节
        startupTimeoutMs=自然数(取('startupTimeoutMs',默认启动超时毫秒),'startupTimeoutMs'),#启动超时
        stopTimeoutMs=自然数(取('stopTimeoutMs',默认停止超时毫秒),'stopTimeoutMs'),#停止超时
        clientReconnectBaseMs=自然数(取('clientReconnectBaseMs',默认客户端重连基数毫秒),'clientReconnectBaseMs'),#重连基数
        clientReconnectMaxMs=自然数(取('clientReconnectMaxMs',默认客户端重连最大毫秒),'clientReconnectMaxMs'),#重连上限
        clientRuntimeTimeoutMs=自然数(取('clientRuntimeTimeoutMs',默认客户端运行时超时毫秒),'clientRuntimeTimeoutMs'),#Client超时
        queryTimeoutMs=自然数(取('queryTimeoutMs',默认查询超时毫秒),'queryTimeoutMs'),#查询超时
        maxClientRuntimeObjects=自然数(取('maxClientRuntimeObjects',默认最大客户端运行时对象),'maxClientRuntimeObjects'),#对象上限
        maxClientRuntimeProperties=自然数(取('maxClientRuntimeProperties',默认最大客户端运行时属性),'maxClientRuntimeProperties'),#属性上限
        maxClientSourceBytes=自然数(取('maxClientSourceBytes',默认最大客户端源字节),'maxClientSourceBytes'),#源字节
        maxCordisNodes=自然数(取('maxCordisNodes',默认最大cordis节点),'maxCordisNodes'),#节点上限
        maxDisconnectedCordisTrees=自然数(取('maxDisconnectedCordisTrees',默认最大断联cordis树),'maxDisconnectedCordisTrees',True),#断联树
    )#规格结束
    if 规格.port>65535:#端口上界
        raise Exception('inspector: port must not exceed 65535')#拒绝
    最大编码分块=(规格.maxBodyChunkBytes+2)//3*4+4096#最大编码分块
    if 最大编码分块>规格.maxSourceFrameBytes:#帧装不下分块
        raise Exception('inspector: maxSourceFrameBytes cannot carry one base64 body chunk')#拒绝
    if 规格.clientReconnectMaxMs<规格.clientReconnectBaseMs:#重连区间非法
        raise Exception('inspector: clientReconnectMaxMs must be at least clientReconnectBaseMs')#拒绝
    from urllib.parse import urlparse#校验origin
    for 来源 in 规格.clientOrigins:#校验每个origin
        解析=urlparse(来源)#解析
        规范=f'{解析.scheme}://{解析.netloc}'#规范
        if 规范!=来源:#必须规范
            raise Exception(f'inspector: client origin must be canonical: {来源}')#拒绝
    return 规格#返回规格

def 派生工作者(引导):#派生Worker
    """派生 Worker；具体运行时由宿主环境提供 MessageChannel/Worker。"""
    raise Exception('inspector: Worker spawn binding is environment-specific')#需运行时绑定

def 关闭检查器(生命周期,源,请求观察,超时毫秒):#关闭检查器
    """关闭检查器。"""
    失败们=[]#失败收集
    try:#停止采集
        if 请求观察 is not None:#有观察器
            请求观察.停止()#停止
    except Exception as 错误:#失败
        失败们.append(错误)#收集
    try:#关闭源
        源.关闭()#关闭
    except Exception as 错误:#失败
        失败们.append(错误)#收集
    try:#停止生命周期
        生命周期.停止(超时毫秒)#停止
    except Exception as 错误:#失败
        失败们.append(错误)#收集
    if len(失败们)>0:#汇总抛出
        raise Exception('inspector: shutdown failed') from 失败们[0]#汇总

def 启动检查器(选项=None):#启动检查器
    """启动 Worker、创建 Host source，并默认安装完整 fetch 采集。"""
    规格=解析检查器选项(选项)#解析规格
    客户端协议=f'dsh-inspector-v{检查器协议版本}-{secrets.token_urlsafe(32)}'#鉴权子协议
    配置={#Worker配置
        'host':规格.host,#主机
        'startPort':规格.port,#起始端口
        'targetId':str(uuid.uuid4()),#目标id
        'clientToken':客户端协议,#Client令牌
        'clientOrigins':规格.clientOrigins,#额外origin
        'maxSourceFrameBytes':规格.maxSourceFrameBytes,#帧字节
        'maxSourceRecordsPerFrame':规格.maxSourceRecordsPerFrame,#每帧记录
        'maxRetainedRequests':规格.maxRetainedRequests,#保留请求
        'maxJournalBytes':规格.maxJournalBytes,#日志字节
        'clientRuntimeTimeoutMs':规格.clientRuntimeTimeoutMs,#Client超时
        'maxClientSourceBytes':规格.maxClientSourceBytes,#源字节
        'maxCordisNodes':规格.maxCordisNodes,#节点上限
        'maxDisconnectedCordisTrees':规格.maxDisconnectedCordisTrees,#断联树
    }#配置结束
    引导={'config':配置,'hostSourcePort':None}#引导载荷；端口由运行时填入
    工作者=派生工作者(引导)#派生Worker
    生命周期=检查器工作者生命周期(工作者)#生命周期
    源=宿主检查器源(引导['hostSourcePort'],type('选项',(),{#绑定port1
        'label':'Host','topics':('*',)+tuple(网络主题),#主题
        'maxQueuedRecords':规格.maxQueuedRecords,'maxQueuedBytes':规格.maxQueuedBytes,#队列
        'maxRecordsPerFrame':规格.maxSourceRecordsPerFrame,'maxFrameBytes':规格.maxSourceFrameBytes,#帧
        'queryTimeoutMs':规格.queryTimeoutMs,#查询超时
    })())#源构造结束
    就绪=生命周期.等待就绪(规格.startupTimeoutMs)#等待就绪
    权威=f'{就绪["host"]}:{就绪["port"]}'#权威主机端口
    端点=检查器端点(#端点
        httpUrl=f'http://{权威}/',#HTTP
        webSocketDebuggerUrl=f'ws://{权威}/devtools/page/{就绪["targetId"]}',#调试WS
        devtoolsFrontendUrl=f'devtools://devtools/bundled/devtools_app.html?ws={权威}/devtools/page/{就绪["targetId"]}&panel=elements&noJavaScriptCompletion=true',#前端
        client={#Client引导
            'endpoint':f'ws://{权威}/ingest',#ingest地址
            'protocol':客户端协议,#子协议
            'maxQueuedRecords':规格.maxQueuedRecords,#队列记录
            'maxQueuedBytes':规格.maxQueuedBytes,#队列字节
            'maxRecordsPerFrame':规格.maxSourceRecordsPerFrame,#每帧记录
            'maxFrameBytes':规格.maxSourceFrameBytes,#帧字节
            'reconnectBaseMs':规格.clientReconnectBaseMs,#重连基数
            'reconnectMaxMs':规格.clientReconnectMaxMs,#重连上限
            'queryTimeoutMs':规格.queryTimeoutMs,#查询超时
            'maxRuntimeObjectsPerSession':规格.maxClientRuntimeObjects,#对象上限
            'maxRuntimePropertiesPerResult':规格.maxClientRuntimeProperties,#属性上限
            'maxClientSourceBytes':规格.maxClientSourceBytes,#源字节
            'maxCordisNodes':规格.maxCordisNodes,#节点上限
        },#client结束
    )#端点结束
    请求观察=安装请求观察器(源,type('采',(),{'maxRequestBodyBytes':规格.maxRequestBodyBytes,'maxResponseBodyBytes':规格.maxResponseBodyBytes,'maxChunkBytes':规格.maxBodyChunkBytes})()) if 规格.captureFetch else None#安装采集
    def 意外(错误):#标记运行并挂钩意外停止
        """意外停止清理。"""
        try:#关闭源
            源.关闭()#尽力关闭
        except Exception as 关闭错误:#关闭失败
            print('dsh inspector: Host source cleanup after Worker failure failed',关闭错误)#记录
        if 请求观察 is not None:#停止采集
            try:#停止
                请求观察.停止()#停止
            except Exception as 停止错误:#失败
                print('dsh inspector: fetch cleanup after Worker failure failed',停止错误)#记录
        print('dsh inspector: Worker stopped unexpectedly',错误)#记录意外停止
    生命周期.标记运行(意外)#markRunning
    关闭中={'p':None}#关闭去重
    def 关闭():#关闭
        """关闭。"""
        if 关闭中['p'] is None:#首次关闭
            关闭中['p']=关闭检查器(生命周期,源,请求观察,规格.stopTimeoutMs)#首次关闭
        return 关闭中['p']#复用
    return 检查器句柄(端点,源,关闭)#句柄
