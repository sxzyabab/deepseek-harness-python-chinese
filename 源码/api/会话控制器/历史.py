"""冷会话历史分页与 live 事件源。"""
import threading#follow 等待
from ...工具.双端队列 import 双端队列#缓冲
from ...内核.会话.表面 import 是否追加表面事件#消息对齐分页
from .远程错误与并发 import 远程错误,已中止#远程错误与中止
from .助手流 import 会话助手流累加器#助手流累加器

__all__=['会话历史控制器']#仅中文公开名

默认最大消息数=50#默认页大小
消息类型=frozenset(['user/message','assistant/message'])#消息类型

class 会话历史控制器:
    """实现冷安全 history 操作。"""

    def __init__(自身,上下文,晋升):
        """保存晋升回调并订阅助手流。"""
        自身._上下文=上下文#Cordis
        自身._晋升=晋升#晋升
        自身._关闭关注者集合=set()#follow 关闭器
        自身._助手流表={}#会话 id → 累加器
        def 助手流帧(*参数):
            """订阅 agent/assistant-stream；作用域派发为 (载体, 载荷)。"""
            载荷=参数[-1] if 参数 else None#末参即载荷
            if not isinstance(载荷,dict):#非 dict
                return#忽略
            智能体=载荷['agent'] if 'agent' in 载荷 else None#智能体
            帧=载荷['frame'] if 'frame' in 载荷 else None#帧
            if 智能体 is None or 帧 is None:#缺字段
                return#忽略
            会话=智能体.session#会话
            标识=会话.id#id
            流=自身._助手流表[标识] if 标识 in 自身._助手流表 else None#累加器
            if 流 is None:#新建
                流=会话助手流累加器()#累加器
                自身._助手流表[标识]=流#登记
            流.接受(帧,下一序号前游标(会话.seq))#接受
        def 智能体拆除(*参数):
            """清理累加器；作用域派发为 (载体, 载荷)。"""
            载荷=参数[-1] if 参数 else None#末参
            if not isinstance(载荷,dict):#非 dict
                return#忽略
            智能体=载荷['agent'] if 'agent' in 载荷 else None#智能体
            if 智能体 is None:#缺
                return#忽略
            自身._助手流表.pop(智能体.session.id,None)#删除
        def 拆除历史():
            """拆除 follow。"""
            自身._拆除()#委托
        上下文.监听('agent/assistant-stream',助手流帧)#全局助手流
        上下文.监听('agent/disposed',智能体拆除)#拆除
        上下文.副作用(拆除历史,'session-controller.history')#拆除

    def _拆除(自身):
        """关闭全部 follower。"""
        for 关闭 in list(自身._关闭关注者集合):#逐个
            关闭()#关
        自身._关闭关注者集合.clear()#清空

    def page(自身,请求,信号):
        """读一页消息对齐历史。请求为 dict。"""
        校验分页请求(请求)#校验
        if 已中止(信号):#取消
            raise 远程错误('gateway/cancelled','session page was aborted',{})#取消
        含末=请求['throughSeq']#含末
        含末游标=-1 if 含末==-1 else 含末#归一
        向前=请求['beforeSeq'] if 'beforeSeq' in 请求 else None#向前
        源=自身._取源(请求['address'],信号,False)#观测
        try:
            if 已中止(信号):#取消
                raise 远程错误('gateway/cancelled','session page was aborted',{})#取消
            源日志=list(源.events)#事件前缀
            源游标=源日志[-1]['seq'] if len(源日志)>0 else -1#源游标
            if 含末游标>源游标:#越过
                raise 远程错误(
                    'gateway/bad-request',
                    'session page through seq '+str(含末游标)+' is past cursor '+str(源游标),
                    {},
                )#坏请求
            if 含末游标>=0 and (含末游标>=len(源日志) or 源日志[含末游标]['seq']!=含末游标):#缺口
                raise 远程错误('gateway/internal','session log does not contain through seq '+str(含末游标),{})#内部
            页=分页(
                源日志,
                向前,
                请求['maxMessages'] if 'maxMessages' in 请求 and 请求['maxMessages'] is not None else 默认最大消息数,
                含末游标,
            )#分页
            return {'records':页记录(页['events']),'hasMore':页['hasMore']}#页
        finally:
            源.close()#关观测

    def follow(自身,请求,信号):
        """跟随追加事件。请求为 dict。"""
        校验跟随请求(请求)#校验
        if 已中止(信号):#取消
            return#空
        地址=请求['address']#地址
        目标=地址标识(地址)#目标 id
        缓冲=双端队列()#缓冲
        快照游标=None#快照游标
        助手流序数=0#助手流序数
        唤醒=threading.Event()#等待
        关注者={'closed':False}#状态
        def 关闭():
            """关闭本 follower。"""
            关注者['closed']=True#关
            唤醒.set()#唤醒
        自身._关闭关注者集合.add(关闭)#登记
        def 会话事件(会话,事件):
            """缓冲匹配会话事件。"""
            if 会话.id!=目标:#非目标
                return#忽略
            缓冲.尾推({'type':'event','event':事件})#缓冲
            唤醒.set()#唤醒
        def 会话创建(会话):
            """构造期种子后缀。"""
            if 会话.id!=目标:#非目标
                return#忽略
            起点=会话.firstLiveSeq if 快照游标 is None else 快照游标+1#后缀起点
            后缀=list(会话.snapshotEvents(起点))#后缀
            for 下标 in range(len(后缀)-1,-1,-1):#逆序头推
                缓冲.头推({'type':'event','event':后缀[下标]})#头推
            唤醒.set()#唤醒
        def 助手流(*参数):
            """缓冲助手流帧；作用域派发为 (载体, 载荷)。"""
            nonlocal 助手流序数#序数
            载荷=参数[-1] if 参数 else None#末参
            if not isinstance(载荷,dict):#非 dict
                return#忽略
            智能体=载荷['agent'] if 'agent' in 载荷 else None#智能体
            帧=载荷['frame'] if 'frame' in 载荷 else None#帧
            if 智能体 is None or 帧 is None or 智能体.session.id!=目标:#非目标
                return#忽略
            助手流序数+=1#序数
            缓冲.尾推({
                'type':'assistant-stream',
                'frame':线上助手流帧(帧,下一序号前游标(智能体.session.seq)),
                'ordinal':助手流序数,
            })#缓冲
            唤醒.set()#唤醒
        卸事件=自身._上下文.监听('session/event',会话事件)#事件
        卸创建=自身._上下文.监听('session/created',会话创建)#创建
        卸助手=None#助手流监听
        if 请求.get('assistantStream') is True:#需要助手流
            卸助手=自身._上下文.监听('agent/assistant-stream',助手流)#挂
        try:
            源=自身._取源(地址,信号,True)#带投影观测
            try:
                事件列表=list(源.events)#事件
                if 已中止(信号):#取消
                    return#空
                游标=源.cursor#游标
                快照游标=游标#记下
                页=分页(
                    事件列表,
                    None,
                    请求['maxMessages'] if 'maxMessages' in 请求 and 请求['maxMessages'] is not None else 默认最大消息数,
                )#开场页
                助手基线=None#助手流基线
                if 请求.get('assistantStream') is True:#需要
                    累加=自身._助手流表[目标] if 目标 in 自身._助手流表 else None#累加器
                    助手基线=累加.快照() if 累加 is not None else {'revision':0}#基线
                助手流序数切=助手流序数#切点
                开场={
                    'type':'snapshot',
                    'header':dict(源.header),
                    'cursor':游标,
                    'records':页记录(页['events']),
                    'hasMore':页['hasMore'],
                    'projections':(
                        {'asOfSeq':游标,'values':{}}
                        if 源.projections is None
                        else 投影块(源.projections)
                    ),
                }#开场
                if 助手基线 is not None:#带助手流
                    开场['assistantStream']=助手基线#基线
                yield 开场#产出快照
                if 地址.get('kind')=='session' and 源.source=='prepared':#晋升
                    晋升=源.retain()#保留
                    try:
                        自身._晋升(晋升)#后台激活
                    except BaseException:
                        晋升.close()#失败则关
                        raise#抛
                下一偏移=游标+1#下一期望
                while (not 关注者['closed']) and (not 已中止(信号)):#活跃
                    项=缓冲.头弹()#取
                    if 项 is None:#空
                        唤醒.clear()#清
                        if 缓冲.大小>0 or 关注者['closed'] or 已中止(信号):#竞态
                            continue#重试
                        唤醒.wait(0.05)#短等
                        continue#再取
                    if 项['type']=='assistant-stream':#助手流
                        if 项['ordinal']>助手流序数切:#切点后
                            yield {'type':'assistant-stream','frame':项['frame']}#产出
                        continue#下一项
                    期望=下一偏移#期望序号
                    事件=项['event']#事件
                    if 事件['seq']<期望:#过旧
                        continue#跳过
                    if 事件['seq']!=期望:#缺口
                        raise 远程错误('gateway/internal','session event stream skipped seq '+str(期望),{})#缺口
                    下一偏移=下一偏移+1#推进
                    yield 条目于(事件)#产出
            finally:
                源.close()#关观测
        finally:
            自身._关闭关注者集合.discard(关闭)#移除
            卸创建()#卸
            卸事件()#卸
            if 卸助手 is not None:#有助手流
                卸助手()#卸

    def _取源(自身,地址,信号,带投影):
        """按地址取观测。"""
        会话标识=地址标识(地址)#id
        投影模式='all' if 带投影 or 地址.get('kind')=='subagent' else 'none'#投影
        try:
            观测=自身._上下文.sessionQuery.observeSession(会话标识,{
                'signal':信号,
                'projectionMode':投影模式,
            })#观测
        except BaseException as 错误:
            if getattr(错误,'code',None)=='SESSION_QUERY_SESSION_NOT_FOUND':#未找到
                拒绝未找到(地址)#映射
            raise#原样
        头=观测.header#头
        if 'cwd' not in 头 or 头['cwd'] is None:#无 cwd
            观测.close()#关
            拒绝未找到(地址)#未找到
        try:
            校验地址(
                地址,
                头,
                getattr(观测,'inheritedEventCount',0),
                观测.projections,
            )#校验
        except BaseException:
            观测.close()#关
            raise#抛
        return 观测#观测

def 下一序号前游标(下一序号):
    """下一序号前的游标。"""
    return -1 if 下一序号==0 else 下一序号-1#游标

def 线上助手流帧(帧,耐久游标):
    """助手流转线上。帧为 dict。"""
    if 帧['type']=='start':#开始
        结果=dict(帧)#拷
        结果['startedAfterSeq']=耐久游标#起始后序号
        return 结果#帧
    if 帧['type']=='end':
        return dict(帧)#原样
    结果=dict(帧)#分块
    结果['chunk']=帧['chunk']#载荷
    return 结果#帧

def 投影块(快照):
    """投影块。快照为 dict。"""
    return {'asOfSeq':快照['asOfSeq'],'values':快照['values']}#块

def 校验分页请求(请求):
    """校验分页请求。"""
    含末=请求['throughSeq'] if 'throughSeq' in 请求 else None#含末
    if not _是安全整数(含末) or 含末<-1 or (isinstance(含末,float) and 含末==0 and str(含末).startswith('-')):#非法
        raise 远程错误('gateway/bad-request','throughSeq must be an integer greater than or equal to -1',{})#坏请求
    向前=请求['beforeSeq'] if 'beforeSeq' in 请求 else None#向前
    if 向前 is not None and (not _是安全整数(向前) or 向前<0):#非法
        raise 远程错误('gateway/bad-request','beforeSeq must be a non-negative safe integer',{})#坏请求
    最大=请求['maxMessages'] if 'maxMessages' in 请求 else None#最大
    if 最大 is not None and (not _是安全整数(最大) or 最大<=0):#非法
        raise 远程错误('gateway/bad-request','maxMessages must be a positive safe integer',{})#坏请求

def 校验跟随请求(请求):
    """校验跟随请求。"""
    最大=请求['maxMessages'] if 'maxMessages' in 请求 else None#最大
    if 最大 is not None and (not _是安全整数(最大) or 最大<=0):#非法
        raise 远程错误('gateway/bad-request','maxMessages must be a positive safe integer',{})#坏请求

def 地址标识(地址):
    """地址到会话 id。"""
    return 地址['sessionId'] if 地址.get('kind')=='session' else 地址['childSessionId']#id

def 校验地址(地址,头,继承事件数,投影):
    """校验地址与头一致。"""
    if 地址.get('kind')=='session':#普通
        if 头.get('origin')=='subagent':#子智能体
            raise 远程错误('session/agent-busy','subagent Sessions require their durable parent address',{
                'reason':'use subagent delivery for this child session',
            })#忙
        return#通过
    if 头.get('origin')!='subagent' or 头.get('parentSession')!=地址.get('parentSessionId'):#归属
        raise 远程错误('subagent/unauthorized','subagent does not belong to the supplied parent',{
            'childSessionId':地址.get('childSessionId'),
        })#未授权
    身份=None#身份
    有子键=投影 is not None and 'values' in 投影 and 'subagent' in 投影['values']#是否声明
    if 有子键:#有键
        身份=投影['values']['subagent']#可取 null
    if 有子键 and 身份 is None:#corrupt 哨
        raise 远程错误('subagent/catalog-diagnostic','subagent descriptor is corrupt',{
            'parentSessionId':地址.get('parentSessionId'),
            'childSessionId':地址.get('childSessionId'),
            'reason':'corrupt',
        })#损坏
    if 身份 is None or 身份.get('seq',-1)<继承事件数:#不可用
        raise 远程错误('subagent/catalog-diagnostic','subagent descriptor is unavailable',{
            'parentSessionId':地址.get('parentSessionId'),
            'childSessionId':地址.get('childSessionId'),
            'reason':'unsupported',
        })#不可用
    if 身份.get('mode')!=地址.get('mode'):#模式
        raise 远程错误('subagent/unauthorized','subagent mode does not match the supplied address',{
            'childSessionId':地址.get('childSessionId'),
        })#未授权

def 拒绝未找到(地址):
    """未找到映射。"""
    if 地址.get('kind')=='session':#普通
        raise 远程错误('session/not-found','session "'+str(地址.get('sessionId'))+'" not found',{
            'sessionId':地址.get('sessionId'),
        })#未找到
    raise 远程错误('subagent/not-found','subagent is unavailable',{
        'parentSessionId':地址.get('parentSessionId'),
        'childSessionId':地址.get('childSessionId'),
    })#未找到

def 分页(事件列表,向前序号,最大消息数,含末游标=None):
    """消息对齐分页。"""
    if 含末游标 is None:#默认末
        含末游标=事件列表[-1]['seq'] if len(事件列表)>0 else -1#末
    终点=min(含末游标+1,向前序号 if 向前序号 is not None else 含末游标+1)#终点
    if 终点<0:#空
        终点=0#归零
    计数=0#消息计数
    切口=0#切点
    for 下标 in range(终点-1,-1,-1):#自后向前
        事件=事件列表[下标]#事件
        if 事件['type'] not in 消息类型 or not 是否追加表面事件(事件):#非消息追加
            continue#跳过
        计数+=1#计数
        组起点=事件['seq']#组起点
        来源列表=事件['sourceEventSeqs'] if 'sourceEventSeqs' in 事件 else None#来源
        if 来源列表 is not None:#有来源
            for 源 in 来源列表:#扫
                if 源<组起点:#更早
                    组起点=源#更新
        if 计数>=最大消息数:#满页
            切口=组起点#切
            break#停
    return {'events':事件列表[切口:终点],'hasMore':切口>0}#页

def 条目于(事件):
    """事件转条目。"""
    return {'type':'event','event':事件}#条目

def 页记录(事件列表):
    """编码一页有界逻辑页。"""
    return [条目于(事件) for 事件 in 事件列表]#记录

def _是安全整数(值):
    """是否安全整数（拒布尔）。"""
    if isinstance(值,bool):#布尔
        return False#拒
    if isinstance(值,int):#整数
        return abs(值)<=9007199254740991#安全
    return False#其它
