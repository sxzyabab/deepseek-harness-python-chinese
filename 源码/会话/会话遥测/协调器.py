"""会话遥测捕获协调器（对齐 upstream session-telemetry/coordinator）。"""
import copy,time,weakref#克隆、时间、弱表
from ...模型后端.llm import 结构化克隆#深拷贝

交接游标=weakref.WeakKeyDictionary()#Session→最高已交接 seq

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#键
    return getattr(对象,键,缺省)#属性

def 严重度于(事件):#事件→严重度
    """把事件自身结果映射到 info/warn/error。"""
    类型=取字段(事件,'type')#类型
    数据=取字段(事件,'data',{})#载荷
    if 类型=='tool/result':#工具结果
        内容=取字段(取字段(数据,'message',{}),'content',[{}])#内容块
        if len(内容)>0 and 取字段(内容[0],'isError') is True:#错误
            return 'error'#错误
        return 'info'#正常
    if 类型=='turn/end':#回合结束
        原因=取字段(数据,'reason',{})#原因
        if 取字段(原因,'kind')=='error':#错误结束
            return 'error'#错误
        return 'info'#正常
    return 'info'#默认

def 身份于(会话,事件):#会话+事件→属性
    """最小身份属性。"""
    属性={'session.id':str(取字段(会话,'id')),'event.type':str(取字段(事件,'type')),'event.seq':取字段(事件,'seq')}#基础
    头=取字段(会话,'header',{})#头
    if 取字段(头,'cwd') is not None:#cwd
        属性['session.cwd']=取字段(头,'cwd')#cwd
    if 取字段(头,'parentSession') is not None:#父
        属性['session.parent_id']=str(取字段(头,'parentSession'))#父 id
    if 取字段(头,'seedLength') is not None:#种子长度
        属性['session.seed_length']=取字段(头,'seedLength')#种子
    return 属性#返回

def 关闭记录(会话):#shutdown ops 记录
    return {'channel':'ops','time':int(time.time()*1000),'severity':'info','attributes':{'telemetry.op':'shutdown','session.id':str(取字段(会话,'id'))},'body':{'op':'shutdown'}}#记录

def 错误细节(错误):#归一化错误
    if isinstance(错误,BaseException):#异常
        return {'name':type(错误).__name__,'message':str(错误)}#细节
    return {'name':'Error','message':str(错误)}#包装

class 会话遥测协调器:#捕获协调器
    """把会话火hose 投影为逻辑记录并交给后端。"""
    def __init__(自身,上下文,后端,捕获='live'):#构造
        自身._上下文=上下文#ctx
        自身._后端=后端#sink
        自身._已收养=set()#活会话
        自身._块见过=weakref.WeakKeyDictionary()#首块跟踪
        if 捕获=='live':#实时捕获
            上下文.on('session/created',lambda 会话:自身._收养(会话))#创建
            上下文.on('session/disposed',lambda 会话:自身._处置(会话))#处置
            上下文.on('session/event',lambda 会话,事件:自身._包含(lambda:自身._捕获事件(会话,事件)))#事件
            上下文.on('session/flush',lambda 会话:自身._包含(lambda:自身._提示冲刷(会话)))#冲刷提示
            上下文.on('agent/error',lambda 载荷:自身._包含(lambda:自身._转发智能体错误(载荷)))#错误
            for 会话 in 上下文.sessions.list():#热重载扫活会话
                自身._收养(会话)#收养
        def 拆除():#协调器拆除
            for 会话 in list(自身._已收养):#仍活
                自身._包含(lambda 会话=会话:自身._递交(会话,{'record':自身._脱敏(关闭记录(会话))}))#shutdown
            try:#后端关闭
                解开=后端.shutdown if hasattr(后端,'shutdown') else 后端.关闭#方法
                结果=解开()#调用
                if hasattr(结果,'__await__'):#协程
                    import asyncio#惰性导入
                    asyncio.get_event_loop().run_until_complete(结果)#等待
            except Exception as 错误:#失败
                上下文.logger.warn('telemetry: backend shutdown failed: '+str(错误))#警告
        上下文.effect(lambda:拆除,'telemetry capture')#effect

    def 捕获会话(自身,会话,至序号=None):#on-demand
        """按游标重放规范日志。"""
        游标=交接游标.get(会话,取字段(会话,'firstLiveSeq',0)-1)#起点
        for 事件 in 取字段(会话,'events',[]):#逐事件
            if 至序号 is not None and 取字段(事件,'seq')>至序号:#越界
                break#停
            自身._包含(lambda 事件=事件:(
                自身._跟踪(会话,事件) if 取字段(事件,'seq')<=游标 else 自身._捕获事件(会话,事件)
            ))#逐条

    captureSession=捕获会话#Cordis 槽

    def _收养(自身,会话):#adopt
        if 会话 in 自身._已收养:#重复
            return#跳过
        自身._已收养.add(会话)#登记
        自身.捕获会话(会话)#重放

    def _处置(自身,会话):#disposed
        if 会话 not in 自身._已收养:#未知
            return#跳过
        自身._已收养.discard(会话)#退役
        自身._递交(会话,{'record':自身._脱敏(关闭记录(会话))})#shutdown

    def _见过(自身,会话):#chunk seen set
        集合=自身._块见过.get(会话)#已有
        if 集合 is None:#首次
            集合=set()#新集合
            自身._块见过[会话]=集合#缓存
        return 集合#返回

    def _跟踪(自身,会话,事件):#只更新投影状态
        if 取字段(事件,'type')=='assistant/chunk':#块
            数据=取字段(事件,'data',{})#载荷
            自身._见过(会话).add(str(取字段(数据,'turn'))+':'+str(取字段(数据,'step')))#键

    def _捕获事件(自身,会话,事件):#单事件
        if 取字段(事件,'type')=='assistant/chunk':#块投影
            数据=取字段(事件,'data',{})#载荷
            键=str(取字段(数据,'turn'))+':'+str(取字段(数据,'step'))#键
            if 键 in 自身._见过(会话):#已见过
                return#跳过
            自身._见过(会话).add(键)#记下
        自身._递交(会话,{'record':自身._脱敏({
            'channel':'ledger','time':取字段(事件,'time'),'severity':严重度于(事件),
            'attributes':身份于(会话,事件),'body':结构化克隆(取字段(事件,'data')),
        }),'seq':取字段(事件,'seq')})#递交

    def _转发智能体错误(自身,载荷):#agent/error
        智能体=取字段(载荷,'agent')#智能体
        细节=错误细节(取字段(载荷,'error'))#错误
        自身._递交(取字段(智能体,'session'),{'record':自身._脱敏({
            'channel':'ops','time':int(time.time()*1000),'severity':'error',
            'attributes':{
                'telemetry.op':'agent-error','session.id':str(取字段(智能体.session,'id')),
                'agent.id':取字段(智能体,'id'),'error.name':细节['name'],
                'turn':取字段(载荷,'turn'),'step':取字段(载荷,'step'),
            },'body':细节,
        })})#递交

    def _提示冲刷(自身,会话):#flush hint
        if 会话 in 自身._已收养:#已收养
            冲刷=getattr(自身._后端,'flush',None) or getattr(自身._后端,'冲刷',None)#方法
            if callable(冲刷):#有
                冲刷()#调用

    def _脱敏(自身,记录):#waterfall
        return 自身._上下文.waterfall('session-telemetry/record',记录,lambda:记录)#瀑布

    def _递交(自身,会话,待定):#deliver
        发出=getattr(自身._后端,'emit',None) or getattr(自身._后端,'发出',None)#方法
        发出(待定['record'])#发出
        if 'seq' in 待定:#推进游标
            交接游标[会话]=待定['seq']#记下

    def _包含(自身,步骤):#contain
        try:#跑
            步骤()#执行
        except Exception as 错误:#吞掉
            自身._上下文.logger.warn('telemetry: capture step failed: '+str(错误))#警告

__all__=['会话遥测协调器']#公开面
