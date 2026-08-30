"""fetch 载体客户端边界。对齐上游 `host/apiproxy/src/fetch/client.ts`。公开面仅中文名。"""
import json,uuid#JSON 与 rpcId
from .接口.rpc模式 import Rpc标识,服务端响应模式#信封模式

__all__=['抽象接口客户端','接口客户端协议','AbstractApiClient','IApiClient']#公开面

默认超时毫秒=30000#一元调用默认超时
内部基址='http://dsh.internal'#无 location.origin 时的内部基址

def _取字段(对象,键,缺省=None):#读映射或属性
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def _域面对象(**方法们):#造命名空间面
    """把可调用挂到简单面对象上。"""
    return type('域面',(),方法们)()#面

def _一元(客户端,方法键):#工厂：载荷直传闭包
    """返回调用 callUnary 的闭包。"""
    def 调用(载荷=None,信号=None):#IApiClient 形
        return 客户端.callUnary(方法键,载荷 or {},信号)#走协议
    return 调用#闭包

class 抽象接口客户端:#AbstractApiClient
    """协议不变量全在基类；平台差异只有 doFetch 与可覆盖的 openMux/openHost。"""

    def __init__(自身,超时毫秒=默认超时毫秒):#构造
        """登记超时与信封观察缓冲。"""
        自身.超时毫秒=超时毫秒#实例超时
        自身._信封批=[]#待冲刷批
        自身._已排冲刷=False#是否已排微任务
        自身._信封监听=set()#订阅者
        自身._挂域面(自身)#IApiClient 形命名空间

    def _挂域面(自身,客户端):#挂各域一元方法
        """按 RpcMethodMap 键机械更新。"""
        自身.sessions=_域面对象(**{#会话域
            'list':_一元(客户端,'session.list'),
            'search':_一元(客户端,'session.search'),
            'create':_一元(客户端,'session.create'),
            'history':_一元(客户端,'session.history'),
            'models':_一元(客户端,'session.models'),
            'selectModel':_一元(客户端,'session.selectModel'),
            'rename':_一元(客户端,'session.rename'),
            'fork':_一元(客户端,'session.fork'),
            'prompt':_一元(客户端,'session.prompt'),
            'attachment':_一元(客户端,'session.attachment'),
            'updateQueue':_一元(客户端,'session.updateQueue'),
            'cancel':_一元(客户端,'session.cancel'),
        })#结束 sessions
        自身.subagents=_域面对象(**{#子智能体域
            'list':_一元(客户端,'subagent.list'),
            'history':_一元(客户端,'subagent.history'),
            'prompt':_一元(客户端,'subagent.prompt'),
            'interrupt':_一元(客户端,'subagent.interrupt'),
        })#结束 subagents
        自身.host=_域面对象(**{#宿主域
            'describe':_一元(客户端,'host.describe'),
            'pickDirectory':_一元(客户端,'host.pickDirectory'),
            'listDirectory':_一元(客户端,'host.listDirectory'),
            'createDirectory':_一元(客户端,'host.createDirectory'),
            'openPath':_一元(客户端,'host.openPath'),
        })#结束 host
        自身.workspace=_域面对象(**{#工作区域
            'list':_一元(客户端,'workspace.list'),
            'create':_一元(客户端,'workspace.create'),
            'rename':_一元(客户端,'workspace.rename'),
            'delete':_一元(客户端,'workspace.delete'),
            'insertBefore':_一元(客户端,'workspace.insertBefore'),
            'insertSessionBefore':_一元(客户端,'workspace.insertSessionBefore'),
            'archiveSession':_一元(客户端,'workspace.archiveSession'),
        })#结束 workspace
        自身.skills=_域面对象(list=_一元(客户端,'skill.list'))#技能域
        自身.agentPresets=_域面对象(**{#预设域
            'list':_一元(客户端,'agentPreset.list'),
            'select':_一元(客户端,'agentPreset.select'),
            'read':_一元(客户端,'agentPreset.read'),
            'copy':_一元(客户端,'agentPreset.copy'),
            'openDocument':_一元(客户端,'agentPreset.openDocument'),
            'remove':_一元(客户端,'agentPreset.remove'),
        })#结束 agentPresets
        自身.goals=_域面对象(**{#目标域
            'create':_一元(客户端,'goal.create'),
            'edit':_一元(客户端,'goal.edit'),
            'pause':_一元(客户端,'goal.pause'),
            'resume':_一元(客户端,'goal.resume'),
            'complete':_一元(客户端,'goal.complete'),
            'clear':_一元(客户端,'goal.clear'),
        })#结束 goals
        自身.settings=_域面对象(**{#设置域
            'describe':_一元(客户端,'settings.describe'),
            'openDocument':_一元(客户端,'settings.openDocument'),
            'update':_一元(客户端,'settings.update'),
            'replace':_一元(客户端,'settings.replace'),
            'mutate':_一元(客户端,'settings.mutate'),
        })#结束 settings
        自身.credentials=_域面对象(**{#凭证域
            'describe':_一元(客户端,'credentials.describe'),
            'set':_一元(客户端,'credentials.set'),
            'unset':_一元(客户端,'credentials.unset'),
        })#结束 credentials
        自身.llm=_域面对象(**{#大模型域
            'providers':_一元(客户端,'llm.providers'),
            'models':_一元(客户端,'llm.models'),
            'discoverModels':_一元(客户端,'llm.discoverModels'),
        })#结束 llm
        自身.events=_域面对象(#事件流
            mux=lambda 载荷=None,信号=None,打开回调=None:客户端.openMux(载荷 or {},信号,打开回调),
            host=lambda 载荷=None,信号=None,打开回调=None:客户端.openHost(载荷 or {},信号,打开回调),
        )#结束 events

    def doFetch(自身,输入,初始化=None):#传输切面
        """子类必须实现。"""
        raise NotImplementedError('AbstractApiClient.doFetch must be implemented by platform subclass')#不可达

    def subscribeEnvelopes(自身,监听):#登记信封观察者
        """返回退订函数。"""
        自身._信封监听.add(监听)#加入
        def 退订():#退订
            自身._信封监听.discard(监听)#删
        return 退订#取消器

    def onEnvelope(自身,消息):#旁路观察
        """写入实例缓冲并按批通知。"""
        if not 自身._信封监听:#无人订阅
            return#跳过
        自身._信封批.append(消息)#入批
        if 自身._已排冲刷:#已有冲刷在路上
            return#跳过
        自身._已排冲刷=True#占位
        def 冲刷():#冲刷一批
            自身._已排冲刷=False#允许下次
            批=list(自身._信封批)#快照
            自身._信封批=[]#换新缓冲
            for 通知 in 自身._信封监听:#逐个
                try:#观察不得打断载体
                    通知(批)#投递
                except Exception as 错误:#隔离
                    print('[apiproxy] envelope listener threw:',错误)#诊断
        try:#优先微任务
            import threading#无 queueMicrotask 时用线程近似
            threading.Timer(0,冲刷).start()#下一拍冲刷
        except Exception:#兜底同步
            冲刷()#立刻

    def resolveBase(自身):#解析 POST/SSE 基址
        """有真 origin 用它，否则内部基址。"""
        try:#浏览器
            import builtins#全局
            定位=getattr(builtins,'location',None)#可能缺
            原点=getattr(定位,'origin',None) if 定位 is not None else None#origin
            if 原点 is not None and 原点!='null':#真 origin
                return 原点#用它
        except Exception:#非浏览器
            pass#落到内部基址
        return 内部基址#假权威

    def _铸造rpc标识(自身):#铸造 rpcId
        """每次调用新 id。"""
        return Rpc标识(str(uuid.uuid4()))#品牌包装

    def _post_json(自身,路径,正文,信号,超时策略):#POST JSON 腿
        """非 2xx 当传输失败抛。"""
        from urllib.parse import urljoin#拼 URL
        地址=urljoin(自身.resolveBase().rstrip('/')+'/',路径.lstrip('/'))#绝对 URL
        选项={'method':'POST','headers':{'content-type':'application/json'},'body':json.dumps(正文,ensure_ascii=False)}#选项
        if 信号 is not None:#有取消信号
            选项['signal']=信号#带上
        响应=自身.doFetch(地址,选项)#传输
        状态=_取字段(响应,'status',200)#HTTP 状态
        if 状态<200 or 状态>=300:#非 2xx
            raise Exception(f'transport failure for {路径}: HTTP {状态}')#传输失败
        读=_取字段(响应,'read',None)#urllib 形
        if callable(读):#有 read
            文本=读().decode('utf-8')#读正文
        else:#fetch 形
            文本=_取字段(响应,'text',None)#可能已是文本
            if callable(文本):#async text
                文本=文本()#调用
            if 文本 is None:#仍无
                正文块=_取字段(响应,'body',b'')#body
                文本=正文块.decode('utf-8') if isinstance(正文块,(bytes,bytearray)) else str(正文块)#解码
        return json.loads(文本)#解析 JSON

    def callUnary(自身,方法,载荷,信号=None,超时策略='default'):#一元协议路径
        """铸造 → tap → POST → 校验回显 → 窄形。"""
        rpc标识=自身._铸造rpc标识()#本请求 id
        消息={'type':'client-request','rpcId':rpc标识,'method':方法,'payload':载荷}#完整形
        自身.onEnvelope(消息)#旁路
        完整=服务端响应模式.parse(自身._post_json(f'/api/{方法}',消息,信号,超时策略))#校验响应
        自身.onEnvelope(完整)#旁路
        回显=完整['rpcId']#回声 id
        if 回显!=rpc标识:#必须对上
            raise Exception(f'rpcId mismatch for {方法}: sent {rpc标识}, got {回显}')#对不上
        return {'rpcId':回显,'result':完整['result']}#窄形

    def openMux(自身,载荷,信号,打开回调=None):#mux 流
        """默认未实现；浏览器/WebSocket 子类覆盖。"""
        raise NotImplementedError('openMux must be implemented by platform subclass')#平台实现

    def openHost(自身,载荷,信号,打开回调=None):#host 流
        """默认未实现；浏览器/WebSocket 子类覆盖。"""
        raise NotImplementedError('openHost must be implemented by platform subclass')#平台实现

    def respond(自身,消息,信号=None):#转发 client-response
        """POST /api/respond 并校验回执。"""
        自身.onEnvelope(消息)#旁路
        回执=自身._post_json('/api/respond',消息,信号,'default')#POST
        if not isinstance(回执,dict):#须为映射
            raise Exception('invalid rpc receipt')#拒绝
        if 回执.get('accepted') is True:#受理
            return {'accepted':True}#回执
        return {'accepted':False,'reason':回执.get('reason','bad-response')}#拒绝

接口客户端协议=抽象接口客户端#IApiClient 消费面类型锚
AbstractApiClient=抽象接口客户端#上游名
IApiClient=接口客户端协议#上游名
