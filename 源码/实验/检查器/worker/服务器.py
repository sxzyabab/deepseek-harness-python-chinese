from ..共享.json import 在线程执行#后台执行
from .inspection.网络存储 import 网络存储#网络存储
from .cdp.domains.network.会话 import 网络域#Network域
from .inspection.cordis存储 import Cordis树存储#Cordis树存储
from .bridge.枢纽 import 检查器源注册表#源注册表
from .bridge.运行时rpc import Client运行时路由#Client Runtime路由
from .bridge.源rpc import Client源路由#Client源路由
from .inspection.realm存储 import 检查器realm注册表#realm注册表
from .realms.host import Host检查器realm#Host realm
from .cdp.domains.dom import Cordis_Dom后端#DOM后端
from .inspection.查询路由 import 检查器查询路由#查询路由
from .bridge.端点 import 检查器端点#端点

__all__=['启动检查器Worker']#仅中文公开名

def 启动检查器Worker(启动包):#启动Worker
    """装配并启动 Worker 拥有的源注册表、Runtime 路由、Network 域与端点。"""
    配置=启动包['config']#配置
    网络仓=网络存储({#网络存储
        'maxRetainedRequests':配置['maxRetainedRequests'],#保留请求上限
        'maxJournalBytes':配置['maxJournalBytes'],#日志字节上限
    })#networkStore结束
    网络=网络域(网络仓)#Network域
    cordis树=Cordis树存储({#Cordis树存储
        'maxNodes':配置['maxCordisNodes'],#节点上限
        'maxDisconnectedTrees':配置['maxDisconnectedCordisTrees'],#断开树上限
    })#cordisTrees结束
    源注册表=检查器源注册表(#源注册表
        [网络仓,cordis树],#消费者
        配置['maxSourceFrameBytes'],#帧字节上限
        配置['maxSourceRecordsPerFrame'],#每帧记录上限
    )#sources结束
    客户端运行时=Client运行时路由(源注册表,配置['clientRuntimeTimeoutMs'])#Client Runtime路由
    客户端源=Client源路由(#Client源路由
        源注册表,#源注册表
        配置['clientRuntimeTimeoutMs'],#超时
        配置['maxClientSourceBytes'],#Client源字节
        配置['maxSourceFrameBytes'],#帧字节
    )#clientSources结束
    realms=检查器realm注册表(Host检查器realm('Host'),客户端运行时,客户端源)#realm注册表
    cordisDom=Cordis_Dom后端(cordis树)#Cordis DOM后端
    def 读cordis树():#树读取器
        """读当前 Cordis 树。"""
        return cordis树.读树()#读树
    查询路由=检查器查询路由(读cordis树,配置['maxSourceFrameBytes'])#查询路由
    def 源事件(事件):#订阅源事件
        """关闭时断开查询。"""
        if 事件['type']=='closed':#关闭
            查询路由.断开(事件['source'])#断开查询
    取消查询订阅=源注册表.订阅事件(源事件)#unsubscribeQueries
    Host端口=启动包['hostSourcePort']#Host源端口
    def Host查询发送(帧):#查询通道发送
        """经 Host 端口投递查询帧。"""
        Host端口.postMessage(帧)#发送帧
    def Host查询关闭(*位置参数):#查询通道关闭
        """关闭 Host 端口。"""
        Host端口.close()#关闭端口
    Host查询=查询路由.打开({#打开Host查询通道
        'send':Host查询发送,#发送帧
        'close':Host查询关闭,#关闭端口
    })#hostQueries结束
    def Host发送(帧):#发往Host
        """投递并在接受后登记。"""
        Host端口.postMessage(帧)#投递帧
        if 帧.get('t')=='source/accepted':#接受后登记
            Host查询.接受(帧['sourceId'],帧['generation'])#登记
    def Host连接关闭(*位置参数):#源连接关闭
        """关闭 Host 端口。"""
        Host端口.close()#关闭端口
    Host连接={'kind':'host','send':Host发送,'close':Host连接关闭}#Host源连接
    def 收Host(值):#收到Host消息
        """查询未吃则交源。"""
        if not Host查询.接收(值):#查询未吃
            源注册表.接收(Host连接,值)#交源
    def Host关闭():#Host端口关闭
        """关闭查询并断源。"""
        Host查询.关闭()#关闭查询
        源注册表.断开(Host连接,'Host source disconnected')#断开源
    Host端口.on('message',收Host)#消息监听
    Host端口.on('close',Host关闭)#关闭监听
    Host端口.start()#启动端口
    端点主=检查器端点(配置,源注册表,网络,realms,cordisDom,读cordis树,查询路由)#端点所有者
    端点=端点主.启动()#启动端点
    已关闭=[None]#关闭任务盒
    def 关闭():#关闭
        """惰性单次关闭。"""
        if 已关闭[0] is not None:#已关
            return 已关闭[0].等待()#复用
        def 体():#关闭体
            """逆序拆除。"""
            端点主.关闭()#关端点
            网络.关闭()#关网络域
            网络仓.拆除()#拆除网络存储
            cordisDom.关闭()#关DOM
            realms.关闭()#关realm
            客户端运行时.关闭()#关Client Runtime
            客户端源.关闭()#关Client源
            Host查询.关闭()#关Host查询
            源注册表.关闭()#关源注册表
            取消查询订阅()#取消订阅
            查询路由.关闭()#关查询路由
            Host端口.close()#关Host端口
        已关闭[0]=在线程执行(体)#登记
        return 已关闭[0].等待()#返回
    return {'endpoint':端点,'close':关闭}#运行时
