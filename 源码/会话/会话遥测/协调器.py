"""会话遥测捕获协调器（对齐 upstream session-telemetry/coordinator）。"""
import time,weakref#时间、弱表
from ...模型后端.llm import 结构化克隆#深拷贝

交接游标=weakref.WeakKeyDictionary()#Session→最高已交接 seq

def 严重度于(事件):
    """把事件自身结果映射到 info/warn/error。"""
    类型=事件['type']#类型
    数据=事件['data'] if 'data' in 事件 else {}#载荷
    if 类型=='tool/result':#工具结果
        消息=数据['message'] if 'message' in 数据 else {}#消息
        内容=消息['content'] if 'content' in 消息 else [{}]#内容块
        if len(内容)>0 and isinstance(内容[0],dict) and 'isError' in 内容[0] and 内容[0]['isError'] is True:#错误
            return 'error'#错误
        return 'info'#正常
    if 类型=='turn/end':#回合结束
        原因=数据['reason'] if 'reason' in 数据 else {}#原因
        if isinstance(原因,dict) and 'kind' in 原因 and 原因['kind']=='error':#错误结束
            return 'error'#错误
        return 'info'#正常
    return 'info'#默认

def 身份于(会话,事件):
    """最小身份属性。"""
    属性={'session.id':str(会话.id),'event.type':str(事件['type']),'event.seq':事件['seq']}#基础
    头=会话.header#头
    if 'cwd' in 头 and 头['cwd'] is not None:#cwd
        属性['session.cwd']=头['cwd']#cwd
    if 'parentSession' in 头 and 头['parentSession'] is not None:#父
        属性['session.parent_id']=str(头['parentSession'])#父 id
    if 头.get('isSeeded'):#已播种：线属性仍用 seed_length，值取 inheritedEventCount
        属性['session.seed_length']=getattr(会话,'inheritedEventCount',0)#种子长度
    return 属性#返回

def 关闭记录(会话):
    """拆除时的 ops 关闭记录。"""
    return {'channel':'ops','time':int(time.time()*1000),'severity':'info','attributes':{'telemetry.op':'shutdown','session.id':str(会话.id)},'body':{'op':'shutdown'}}#记录

def 错误细节(错误):
    """归一化错误细节。"""
    if isinstance(错误,BaseException):#异常
        return {'name':type(错误).__name__,'message':str(错误)}#细节
    return {'name':'Error','message':str(错误)}#包装

def 原样记录(记录):
    """瀑布缺席时的原记录。"""
    return 记录#原样

class 会话遥测协调器:
    """把会话火hose 投影为逻辑记录并交给后端。后端是含 发出/关闭 的 dict。"""
    def __init__(自身,上下文,后端,捕获='live'):
        """安装捕获路径。"""
        自身._上下文=上下文#ctx
        自身._后端=后端#sink dict
        自身._已收养=weakref.WeakKeyDictionary()#活会话身份
        if 捕获=='live':#实时捕获
            上下文.监听('session/created',自身._收养)#创建
            上下文.监听('session/disposed',自身._会话已拆除)#拆除
            上下文.监听('session/event',自身._事件入口)#事件
            上下文.监听('session/flush',自身._冲刷入口)#冲刷提示
            上下文.监听('agent/error',自身._错误入口)#错误
            for 会话 in 上下文.sessions.list():#热重载扫活会话
                自身._收养(会话)#收养
        def 拆除效果():
            """协调器拆除。"""
            return 自身._拆除#拆除器
        上下文.副作用(拆除效果,'telemetry capture')#effect

    def 捕获会话(自身,会话,至序号=None):
        """按游标重放规范日志。"""
        游标=交接游标[会话] if 会话 in 交接游标 else 会话.firstLiveSeq-1#起点
        for 事件 in 会话.events:#逐事件
            if 事件['seq']<=游标:#已交接
                continue#跳过
            if 至序号 is not None and 事件['seq']>至序号:#越界
                break#停
            自身._包含(自身._捕获事件,会话,事件)#捕获

    def _收养(自身,会话):
        """收养活会话。"""
        if 会话 in 自身._已收养:#重复
            return#跳过
        自身._已收养[会话]=True#登记
        自身.捕获会话(会话)#重放

    def _会话已拆除(自身,会话):
        """会话拆除。"""
        if 会话 not in 自身._已收养:#未知
            return#跳过
        del 自身._已收养[会话]#退役
        自身._递交(会话,{'record':自身._脱敏(关闭记录(会话))})#shutdown

    def _捕获事件(自身,会话,事件):
        """单事件捕获。"""
        自身._递交(会话,{'record':自身._脱敏({
            'channel':'ledger','time':事件['time'],'severity':严重度于(事件),
            'attributes':身份于(会话,事件),'body':结构化克隆(事件['data'] if 'data' in 事件 else None),
        }),'seq':事件['seq']})#递交

    def _转发智能体错误(自身,载荷):
        """转发 agent/error。"""
        智能体=载荷['agent']#智能体
        细节=错误细节(载荷['error'])#错误
        自身._递交(智能体.session,{'record':自身._脱敏({
            'channel':'ops','time':int(time.time()*1000),'severity':'error',
            'attributes':{
                'telemetry.op':'agent-error','session.id':str(智能体.session.id),
                'agent.id':智能体.id,'error.name':细节['name'],
                'turn':载荷['turn'] if 'turn' in 载荷 else None,'step':载荷['step'] if 'step' in 载荷 else None,
            },'body':细节,
        })})#递交

    def _提示冲刷(自身,会话):
        """flush 提示。"""
        if 会话 in 自身._已收养 and '冲刷' in 自身._后端:#已收养且有冲刷
            自身._后端['冲刷']()#调用

    def _脱敏(自身,记录):
        """瀑布脱敏。"""
        return 自身._上下文.链式拦截('session-telemetry/record',记录,原样记录)#瀑布

    def _递交(自身,会话,待定):
        """交给后端并推进游标。"""
        自身._后端['发出'](待定['record'])#发出
        if 'seq' in 待定:#推进游标
            交接游标[会话]=待定['seq']#记下

    def _包含(自身,步骤,*位置参数):
        """捕获步失败不得打断会话火hose。"""
        try:#跑
            步骤(*位置参数)#执行
        except Exception as 错误:#捕获步任意失败都 warn；上游 catch 未定更窄契约
            自身._上下文.日志.警告('telemetry: capture step failed: '+str(错误))#警告

    def _事件入口(自身,会话,事件):
        """session/event。"""
        自身._包含(自身._捕获事件,会话,事件)#包含

    def _冲刷入口(自身,会话):
        """session/flush。"""
        自身._包含(自身._提示冲刷,会话)#包含

    def _错误入口(自身,载荷):
        """agent/error。"""
        自身._包含(自身._转发智能体错误,载荷)#包含

    def _递交关闭(自身,会话):
        """拆除时递交 shutdown 记录。"""
        自身._递交(会话,{'record':自身._脱敏(关闭记录(会话))})#shutdown

    def _拆除(自身):
        """拆除时递交关闭并关后端。"""
        for 会话 in list(自身._已收养.keys()):#仍活
            自身._包含(自身._递交关闭,会话)#shutdown
        try:#后端关闭
            自身._后端['关闭']()#同步关闭
        except Exception as 错误:#失败
            自身._上下文.日志.警告('telemetry: backend shutdown failed: '+str(错误))#警告

__all__=['会话遥测协调器']#公开面
