from ...依赖 import cordis
from ...模型后端.llm.永不 import 断言永不
from .修复 import 工具未启动
from ..作用域 import 弱身份表

包名='@deepseek-ai/dsh-session'
名称='session-invariant'
依赖=['invariants']

__all__=['包名','名称','依赖','安装','应用','空踪迹','校验事件','应用变迁']

def 要求打开步骤(踪迹,种类,轮次,步骤,失败):
    """断言步骤作用域事件点名的是当前打开的轮次与步骤。"""
    if 踪迹['openTurn']!=轮次 or 踪迹['openStep']!=步骤:
        失败(种类+' 点名轮次 '+str(轮次)+'/步骤 '+str(步骤)+'，但当前打开的是轮次 '+str(踪迹['openTurn'])+'/步骤 '+str(踪迹['openStep']))

def 校验事件(踪迹,事件,失败):
    """校验一条候选事件，不改已提交踪迹。"""
    序号=事件['seq']
    if 序号<=踪迹['lastSeq']:
        失败('seq 必须严格递增: 看到 '+str(序号)+' 发生在 '+str(踪迹['lastSeq'])+' 之后')
    打开轮次=踪迹['openTurn']
    打开步骤=踪迹['openStep']
    下一轮次=踪迹['nextTurn']
    下一步骤=踪迹['nextStep']
    待完成={'kind':'none'}
    种类=事件['type']
    数据=事件['data']
    if 种类=='turn/start':
        轮次=数据['turn']
        if 踪迹['openTurn'] is not None:
            失败('turn/start '+str(轮次)+' 时轮次 '+str(踪迹['openTurn'])+' 仍打开')
        if 轮次!=踪迹['nextTurn']:
            失败('turn/start 期望轮次 '+str(踪迹['nextTurn'])+'，实际为 '+str(轮次))
        打开轮次=轮次
        下一步骤=1#步骤从 1 起
    elif 种类=='turn/end':
        轮次=数据['turn']
        if 踪迹['openTurn']!=轮次:
            失败('turn/end '+str(轮次)+' 与打开轮次 '+str(踪迹['openTurn'])+' 不匹配')
        if 踪迹['openStep'] is not None:
            失败('turn/end '+str(轮次)+' 时步骤 '+str(踪迹['openStep'])+' 仍打开')
        打开轮次=None
        下一轮次=下一轮次+1
    elif 种类=='step/start':
        轮次=数据['turn']
        步骤=数据['step']
        if 踪迹['openTurn']!=轮次:
            失败('step/start 在轮次 '+str(轮次)+'，但打开轮次是 '+str(踪迹['openTurn']))
        if 踪迹['openStep'] is not None:
            失败('step/start '+str(步骤)+' 时步骤 '+str(踪迹['openStep'])+' 仍打开')
        if 步骤!=踪迹['nextStep']:
            失败('step/start 期望轮次 '+str(轮次)+' 的步骤 '+str(踪迹['nextStep'])+'，实际为 '+str(步骤))
        打开步骤=步骤
    elif 种类=='step/end':
        要求打开步骤(踪迹,'step/end',数据['turn'],数据['step'],失败)
        待完成={'kind':'clear'}
        打开步骤=None
        下一步骤=下一步骤+1
    elif 种类=='assistant/attempt':
        要求打开步骤(踪迹,'assistant/attempt',数据['turn'],数据['step'],失败)
    elif 种类=='assistant/message':
        要求打开步骤(踪迹,'assistant/message',数据['turn'],数据['step'],失败)
    elif 种类=='tool/call':
        要求打开步骤(踪迹,'tool/call',数据['turn'],数据['step'],失败)
        待完成={'kind':'add','callId':数据['callId']}
    elif 种类=='tool/result':
        if 'surfaceOp' not in 事件 or 事件['surfaceOp']!='append':#表面替换而非追加
            if 踪迹['openTurn'] is None:
                失败('tool/result 表面替换追加在任何打开轮次之外')
        else:
            要求打开步骤(踪迹,'tool/result',数据['turn'],数据['step'],失败)
            消息=数据['message']
            来源=消息['source']
            调用号=来源['callId']
            内容=消息['content']
            块=内容[0]
            错误=数据['error'] if 'error' in 数据 else None
            合成未启动=('isError' in 块 and 块['isError'] is True) and (错误 is not None and 'code' in 错误 and 错误['code']==工具未启动)#合成的未启动错误
            if (调用号 not in 踪迹['pendingCalls']) and (not 合成未启动):
                失败('本步骤没有先前 tool/call 却出现了 '+str(调用号)+' 的 tool/result')
            待完成={'kind':'delete','callId':调用号}
    elif 种类=='system/message':
        要求打开步骤(踪迹,'system/message',数据['turn'],数据['step'],失败)
    elif 种类=='user/message':
        pass
    elif 种类=='session/end-seed':
        pass
    elif 种类=='request/header' or 种类=='request/context':
        if 踪迹['openTurn'] is None:
            失败(种类+' 追加在任何打开轮次之外（核心执行事件必须包在轮次内）')
    else:
        pass#可合并扩展的事件关系归其拥有插件
    return {
        'scalars':{
            'lastSeq':序号,
            'openTurn':打开轮次,
            'openStep':打开步骤,
            'nextTurn':下一轮次,
            'nextStep':下一步骤,
        },
        'pendingCalls':待完成,
    }

def 应用变迁(踪迹,变迁):
    """在事件提交后应用一条已校验变迁。"""
    标量=变迁['scalars']
    踪迹['lastSeq']=标量['lastSeq']
    踪迹['openTurn']=标量['openTurn']
    踪迹['openStep']=标量['openStep']
    踪迹['nextTurn']=标量['nextTurn']
    踪迹['nextStep']=标量['nextStep']
    变更=变迁['pendingCalls']
    种=变更['kind']
    if 种=='none':
        pass
    elif 种=='add':
        踪迹['pendingCalls'].add(变更['callId'])
    elif 种=='delete':
        踪迹['pendingCalls'].discard(变更['callId'])
    elif 种=='clear':
        踪迹['pendingCalls'].clear()
    else:
        断言永不(变更,'会话踪迹待完成调用变迁')

def 空踪迹():
    """每个会话用于关系日志检查的空账本。"""
    return {
        'lastSeq':-1,#尚无序号
        'openTurn':None,
        'openStep':None,
        'nextTurn':1,#下一轮从 1
        'nextStep':1,
        'pendingCalls':set(),
    }

def 安装(上下文,失败):
    """把会话贡献安装进其子注册纤程。"""
    踪迹表=弱身份表()
    暂存表=弱身份表()
    def 播种会话(会话):
        """从已有日志播种。"""
        踪迹=空踪迹()
        踪迹表.设(会话,踪迹)
        for 事件 in 会话.events:
            应用变迁(踪迹,校验事件(踪迹,事件,失败))
        return 踪迹
    def 取踪迹(会话):
        """取踪迹，缺则播种。"""
        已有=踪迹表.取(会话)
        if 已有 is None:
            return 播种会话(会话)
        return 已有
    for 会话 in 上下文.sessions.列出():
        播种会话(会话)
    def 新会话(载体,会话,*位置参数):
        """新会话播种。派发 this 是载体。"""
        播种会话(会话)
    上下文.监听('session/created',新会话,{'全局':True})
    def 提交事件(载体,会话,事件,*位置参数):
        """事件发表后提交变迁。派发 this 是载体。"""
        暂存=暂存表.取(事件)
        if 暂存 is None or 暂存['session'] is not 会话:
            return 失败('session/event 到达发表时没有匹配的提交前校验')
        暂存表.设(事件,None)
        应用变迁(暂存['trace'],暂存['transition'])
    上下文.监听('session/event',提交事件,{'全局':True})
    def 派发钩子(_模式,事件名,参数,*其余):
        """派发时先纯校验。"""
        if 事件名!='session/event':
            return
        会话=参数[0]
        事件=参数[1]
        踪迹=取踪迹(会话)
        变迁=校验事件(踪迹,事件,失败)
        暂存表.设(事件,{'session':会话,'trace':踪迹,'transition':变迁})
    上下文.监听('internal/dispatch',派发钩子,{'全局':True})

安装.inject=['sessions']#安装时还要 sessions（Cordis 安装器协议槽）

def 应用(上下文):
    """注册会话不变量配套。"""
    return 上下文.invariants.register(包名,安装)

name=名称
inject=依赖
apply=应用
