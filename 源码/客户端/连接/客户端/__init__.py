'浏览器连线：远程传输和连接代际'
from ...模块.客户端.通告 import 取握手窗口
from pywebbridge import undefined as 未定义#页面上没有该值
from ..回环主机名 import 是否回环主机名#页面权威是不是回环
from ..恢复流程配置 import 解析连接配置#页面注入的恢复时序
from ..异常 import 连接错误#重复登记或重复启动
from .套接字 import 打开连接套接字#物理套接字
from .接口 import Rpc标识,传输错误#再导出
from .连接 import 连接控制器#重连循环
from .rpc import 创建网页连接rpc,进程内调用#一元调用。没有壳载体时走本进程
from . import (
    套接字,#套接字
    接口,#协议辅助
    连接,#恢复循环
    rpc,#一元调用
)#同目录模块。导入时执行它们的顶层

__all__=[#同目录模块，以及客户端入口再导出的值
    '依赖','应用','安装连接',
    '套接字','接口','连接','rpc',
    'Rpc标识','传输错误',
]#公开名

依赖=[]#连线自己就是传输根
RpcId=Rpc标识#与上游导出名相同
transportError=传输错误#与上游导出名相同


def 取字段(对象,键):
    '字典用键。页面对象用属性。没有或未定义则为空'
    if 对象 is None:#没有对象
        return None#空
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else None#有这个键才取
    值=getattr(对象,键,None)#属性
    if 值 is 未定义 or 值 is Ellipsis:#页面上没有
        return None#空
    return 值#值


class 世代源:
    'getSnapshot 与 subscribe'
    def __init__(自身,取快照,订阅):
        '记下两个函数'
        自身.getSnapshot=取快照#当前值
        自身.subscribe=订阅#订阅

class 连接句柄:
    'ctx.connection：交互、回环、代际、状态、RPC 和套接字'
    def __init__(自身,交互,是否回环,世代,状态,逻辑,重连,登记,启动,打开):
        '这些名字保持上游原文，别的包按这个调用'
        自身.interactions=交互#answer 或 none
        自身.isLoopback=是否回环#特权面是否可达
        自身.generation=世代#当前代际
        自身.state=状态#恢复状态
        自身.rpc=逻辑#一元调用
        自身.reconnect=重连#立即重连
        自身.registerGenerationSource=登记#登记代际源
        自身.start=启动#启动循环
        自身.openWebSocket=打开#打开套接字

class 停止句柄:
    '循环的唯一拥有者拿着它来停止'
    def __init__(自身,停止函数):
        '记下停止函数'
        自身._停止=停止函数#函数

    def stop(自身):
        '停止循环并收回当前代际'
        自身._停止()#执行


def 记录监听失败(前缀,错误):
    '订阅者抛错只打到控制台'
    取握手窗口().console.error(前缀,错误)#诊断


def 安装连接(上下文,选项=None):
    '按显式组合输入安装一份上下文拥有的连接服务'
    if 选项 is None:#没传
        选项={}#空
    页面=取字段(选项,'location')#页面位置
    传输=取字段(选项,'transport')#物理载体
    恢复=取字段(选项,'recovery')#时序覆盖
    if 恢复 is None:#没写
        恢复={}#控制器里再补默认
    交互=取字段(选项,'interactions')#参与方式
    if 交互 is None:#没写
        交互='none' if 页面 is None else 'answer'#没有页面则不参与
    已有逻辑=取字段(传输,'rpc')#已经解码的调用方
    if 已有逻辑 is not None:#调用方自己给了
        逻辑=已有逻辑#直接用
    else:#按 fetch 和流组装
        逻辑=创建网页连接rpc(取字段(传输,'fetch'),取字段(传输,'openStream'))#网页调用方
    世代源登记={'值':None}#唯一的源
    属主={'值':None}#当前循环
    世代号={'值':0}#递增
    世代={'值':None}#当前代际
    状态={'值':None}#当前状态
    世代监听=set()#代际订阅
    状态监听=set()#状态订阅
    套接字工厂=取字段(传输,'createWebSocket')#认证过的工厂
    流基址=取字段(传输,'streamBaseUrl')#桌面或 Node 的基址

    def 打开套接字(路径,工厂=套接字工厂,基址=流基址):
        '按安装时的工厂和基址打开。本进程调用不经过浏览器'
        if getattr(逻辑,'进程内',False):#宿主在本进程
            raise 连接错误('connection: 本进程不通过浏览器打开套接字')#拒绝
        return 打开连接套接字(路径,工厂,基址)#套接字

    def 发布世代(下一个):
        '同一个对象不重复通知'
        if 世代['值'] is 下一个:#同一引用
            return#跳过
        世代['值']=下一个#写下
        for 监听 in list(世代监听):#拷贝后再调
            try:#一个订阅者失败不影响其余
                监听()#通知
            except Exception as 错误:#抛了
                记录监听失败('[connection] generation listener threw:',错误)#诊断

    def 发布状态(下一个):
        '同一个状态不重复通知'
        if 状态['值']==下一个:#相同
            return#跳过
        状态['值']=下一个#写下
        for 监听 in list(状态监听):#拷贝后再调
            try:#一个订阅者失败不影响其余
                监听()#通知
            except Exception as 错误:#抛了
                记录监听失败('[connection] state listener threw:',错误)#诊断

    def 释放属主(当前):
        '仍是这一次才停'
        if 属主['值'] is not 当前:#已经换过
            return#忽略
        属主['值']=None#清掉
        当前['stopNetworkWatch']()#卸掉在线监听
        当前['controller'].停止()#停泵
        发布世代(None)#收回代际
        发布状态(None)#收回状态

    def 重连():
        '重置重试并立刻替换当前尝试'
        当前=属主['值']#属主
        if 当前 is not None:#有循环
            当前['controller'].重连()#立即

    def 登记世代源(源):
        '只能有一个源'
        if 世代源登记['值'] is not None:#已经有
            raise 连接错误('connection: a generation source is already registered')#拒绝
        世代源登记['值']=源#记下

        def 撤回():
            '仍是这个源才撤回，并停掉它的循环'
            if 世代源登记['值'] is not 源:#已经换过
                return#忽略
            世代源登记['值']=None#清掉
            当前=属主['值']#属主
            if 当前 is not None and 当前['source'] is 源:#循环用的就是它
                释放属主(当前)#停掉

        return 撤回#拆除器

    def 启动(汇,配置=None):
        '只能启动一次，并且必须已经登记代际源'
        if 属主['值'] is not None:#已经有人
            raise 连接错误('connection: the stream loop is already owned by another consumer')#拒绝
        源=世代源登记['值']#源
        if 源 is None:#还没有
            raise 连接错误('connection: no generation source is registered')#拒绝
        令牌=object()#这一次的身份

        def 仍属本代():
            '属主仍是这次启动'
            当前=属主['值']#属主
            return 当前 is not None and 当前['token'] is 令牌#同一令牌

        def 已连接(宿主):
            '先发布代际，再转给消费者'
            世代号['值']=世代号['值']+1#递增
            下一={'id':世代号['值'],'host':宿主}#这一代
            发布世代(下一)#发布
            if (not 仍属本代()) or (世代['值'] is not 下一):#已经收回
                return#不再转发
            回调=汇.get('onConnected') if isinstance(汇,dict) else getattr(汇,'onConnected',None)#消费者
            if 回调 is not None:#有
                回调(宿主)#转发

        def 状态变化(下一状态):
            '不是 connected 就收回代际'
            if 下一状态!='connected':#断开或正在连接
                发布世代(None)#收回
            if not 仍属本代():#过期
                return#不再转发
            发布状态(下一状态)#状态
            回调=汇.get('onStateChange') if isinstance(汇,dict) else getattr(汇,'onStateChange',None)#消费者
            if 回调 is not None:#有
                回调(下一状态)#转发

        包装汇={#包一层，再把原来的重开请求带上
            'onConnected':已连接,#覆盖
            'onStateChange':状态变化,#覆盖
            'onReconnectRequested':汇.get('onReconnectRequested') if isinstance(汇,dict) else getattr(汇,'onReconnectRequested',None),#原样
        }#汇结束
        合并=dict(恢复)#安装时的时序
        if 配置 is not None:#这次再覆盖
            if isinstance(配置,dict):#字典
                合并.update(配置)#叠上
            else:#对象
                for 键 in ('backoffBaseMs','backoffFactor','backoffMaxMs','generationReadyWarnMs','generationReadyTimeoutMs'):#五项
                    值=取字段(配置,键)#一项
                    if 值 is not None:#写了
                        合并[键]=值#覆盖
        控制器=连接控制器(源,包装汇,合并)#循环
        窗口=取握手窗口()#页面
        导航=窗口.navigator#导航
        初值=导航.onLine#是否在线
        if 初值 is 未定义 or 初值 is Ellipsis or not isinstance(初值,bool):#页面没报告

            def 停网络():
                '没有在线状态可听'
                return None#空

        else:#有在线状态
            def 上线():
                '网络回来了'
                控制器.设网络可用(True)#可重试

            def 下线():
                '网络没了'
                控制器.设网络可用(False)#挂起

            控制器.设网络可用(初值)#初值
            窗口.addEventListener('online',上线)#上线
            窗口.addEventListener('offline',下线)#下线

            def 停网络():
                '卸掉在线监听'
                窗口.removeEventListener('online',上线)#上线
                窗口.removeEventListener('offline',下线)#下线

        当前={'token':令牌,'source':源,'controller':控制器,'stopNetworkWatch':停网络}#这一次
        属主['值']=当前#占上
        控制器.启动()#开始泵

        def 停止():
            '释放这一次'
            释放属主(当前)#停

        return 停止句柄(停止)#交给拥有者

    def 取世代():
        '当前代际'
        return 世代['值']#值

    def 订世代(监听):
        '订阅代际建立、替换和丢失'
        世代监听.add(监听)#加入

        def 退订():
            '摘掉'
            世代监听.discard(监听)#摘掉

        return 退订#退订

    def 取状态():
        '当前恢复状态'
        return 状态['值']#值

    def 订状态(监听):
        '订阅状态变化'
        状态监听.add(监听)#加入

        def 退订():
            '摘掉'
            状态监听.discard(监听)#摘掉

        return 退订#退订

    拥有宿主=取字段(传输,'ownsHost') is True#页面自己持有宿主
    if 页面 is None:#不是浏览器
        回环=True#特权面可达
    else:#有页面
        主机名=取字段(页面,'hostname')#主机名
        回环=是否回环主机名(主机名 if isinstance(主机名,str) else '')#回环权威
    是否回环=拥有宿主 or 回环#三者之一
    句柄=连接句柄(#组装
        交互,#参与
        是否回环,#回环
        世代源(取世代,订世代),#代际
        世代源(取状态,订状态),#状态
        逻辑,#调用
        重连,#重连
        登记世代源,#登记
        启动,#启动
        打开套接字,#套接字
    )#句柄结束
    上下文.提供服务('connection',句柄)#提供


def 应用(上下文,配置值=None):
    '读页面上的载体和恢复时序，安装连接服务'
    窗口=取握手窗口()#页面全局
    传输=窗口['__DSH_TRANSPORT__']#壳可以自己持有载体
    if 传输 is 未定义 or 传输 is Ellipsis:#没有
        传输=None#没有壳载体，不走页面上的 HTTP 和 WebSocket
    恢复原=窗口['__DSH_CONNECTION_RECOVERY__']#索引注入的时序
    if 恢复原 is 未定义 or 恢复原 is Ellipsis:#没有
        恢复原=None#用默认
    页面=None#桥接页不是宿主。没有壳载体时不按页面源去开套接字
    if 传输 is not None:#壳给了宿主载体，才使用页面位置
        定位=窗口.location#页面位置
        主机名=定位.hostname#主机名
        if 主机名 is not 未定义 and 主机名 is not Ellipsis:#有页面
            页面=定位#位置
    选项={'recovery':解析连接配置(恢复原)}#先校验时序
    if 传输 is None:#没有壳载体。调用和事件留在本进程，连接仍是应答
        选项['interactions']='answer'#不是 none
        选项['transport']={'rpc':进程内调用()}#交给宿主网关
    else:#壳给了载体
        选项['transport']=传输#带上
    if 页面 is not None:#有位置
        选项['location']=页面#带上
    安装连接(上下文,选项)#安装


inject=依赖#框架槽
apply=应用#框架槽
