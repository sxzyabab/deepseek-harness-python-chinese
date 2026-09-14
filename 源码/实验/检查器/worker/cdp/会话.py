#对齐上游 worker/cdp/session.ts

from ...共享.json import 检查器错误#包内错误
from .协议 import 解析cdp请求,cdp错误#协议
from .目标 import cdp方法未处理,处理脚手架#脚手架
from .domains.runtime import Runtime域会话#Runtime
from .domains.debugger import Debugger域会话#Debugger
from .domains.dom import Cordis_Dom会话#DOM
from .domains.原生 import Host原生域会话#原生域
from .realm会话 import 检查器realm会话集#realm会话集

__all__=['Cdp会话']#仅中文公开名

class Cdp会话:#CDP会话
    """每连接一条的 CDP 分发器。"""
    def __init__(自身,传输,目标,源注册表,网络,realm注册表,dom后端,cordis树):#构造
        """装配各域会话。"""
        自身.传输=传输#传输
        自身.目标=目标#目标
        自身.源注册表=源注册表#源
        自身.网络=网络#网络
        自身.cordis树=cordis树#Cordis树
        自身._诊断启用=False#诊断是否启用
        自身.realms=检查器realm会话集(realm注册表)#会话集
        原生=自身.realms.host()['nativeDomains']#原生能力
        if 原生['state']=='unsupported':#不支持则抛
            raise 检查器错误(原生['reason'])#抛错
        自身.原生域=Host原生域会话(传输,原生['backend'])#原生会话
        自身.运行时=Runtime域会话(传输,自身.realms)#Runtime会话
        自身.调试器=Debugger域会话(传输,自身.realms,自身.运行时)#Debugger会话
        自身.dom=Cordis_Dom会话(传输,dom后端,自身.运行时)#DOM会话
        def 绑定对象(对象id,realm,引用,组):#对象观察者
            """把 Runtime 对象绑到 DOM 节点。"""
            自身.dom.绑定对象(对象id,realm,引用,组)#绑定
        自身.运行时.设对象观察者(绑定对象)#绑定DOM
        自身._取消源订阅=源注册表.订阅状态(自身._源状态变更)#源状态

    def _源状态变更(自身):#源状态
        """诊断启用时推送源列表。"""
        if 自身._诊断启用:#启用
            自身.发送事件('DSHInspector.sourcesChanged',{'sources':自身.源注册表.描述()})#推送

    def 接收(自身,值):#接收请求
        """解析并分发一条原始 CDP 请求。"""
        try:#解析
            请求=解析cdp请求(值)#解析请求
        except Exception:#解析cdp请求可能抛检查器错误/TypeError/KeyError，契约未定所以收不窄
            自身.传输.关闭()#关闭
            return#返回
        try:#分发
            if 请求['method']=='Runtime.releaseObject':#释放对象
                自身.dom.释放对象(请求['params'].get('objectId'))#释放
            if 请求['method']=='Runtime.releaseObjectGroup':#释放组
                自身.dom.释放对象组(请求['params'].get('objectGroup'))#释放
            if 自身.dom.处理(请求):#DOM已处理
                return#返回
            if 自身.运行时.处理(请求):#Runtime已处理
                return#返回
            if 自身.调试器.处理(请求):#Debugger已处理
                return#返回
            if 自身.原生域.拥有(请求['method']):#原生域
                改写={**请求,'params':自身.运行时.原生参数(请求['params'])}#改写参数
                自身.原生域.处理(改写)#处理
                return#返回
            方法=请求['method']#方法
            if 方法.startswith('Network.'):#Network
                结果=自身.网络.处理(方法,请求['params'],自身)#处理
            elif 方法=='DSHInspector.enable':#启用诊断
                自身._诊断启用=True#置位
                结果={'sources':自身.源注册表.描述()}#源列表
            elif 方法=='DSHInspector.disable':#禁用诊断
                自身._诊断启用=False#清位
                结果={}#空
            elif 方法=='DSHInspector.getSources':#取源
                结果={'sources':自身.源注册表.描述()}#源列表
            elif 方法=='DSHInspector.getCordisTree':#取树
                try:#成功
                    树=自身.cordis树()#树
                    自身.传输.发送({'id':请求['id'],'result':{'tree':树}})#成功
                except Exception as 错误:#cordis树收集可能抛检查器错误/属性错误，契约未定所以收不窄
                    自身.传输.发送(cdp错误(请求['id'],-32000,str(错误)))#错误
                return#返回
            else:#脚手架
                结果=处理脚手架(请求,自身.目标)#处理
                if 结果 is cdp方法未处理:#未处理
                    自身.传输.发送(cdp错误(请求['id'],-32601,f'Method not found: {方法}'))#方法未找到
                    return#返回
            自身.传输.发送({'id':请求['id'],'result':结果})#发送结果
        except Exception as 错误:#CDP 方法分发体什么都可能抛，契约未定所以收不窄
            自身.传输.发送(cdp错误(请求['id'],-32000,str(错误)))#错误

    def 发送事件(自身,方法,参数):#发送事件
        """推送一条 CDP 事件。"""
        自身.传输.发送({'method':方法,'params':参数})#投递

    def 关闭(自身):#关闭
        """拆除本连接拥有的全部 V8 与域资源。"""
        自身._取消源订阅()#取消源订阅
        自身.网络.分离(自身)#Network分离
        自身.dom.关闭()#关DOM
        自身.运行时.关闭()#关Runtime
        自身.调试器.关闭()#关Debugger
        自身.原生域.关闭()#关原生
        自身.realms.关闭()#关realm
