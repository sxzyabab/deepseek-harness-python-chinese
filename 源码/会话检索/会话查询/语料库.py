"""会话检索用的活/已持久逻辑语料解析。对齐上游 `session-query/src/corpus.ts`。"""
import threading#并发持久检查工人
from ....模型后端.llm import 结构化克隆#拆离克隆
from ....会话.会话持久化 import 会话持久化损坏错误#持久化损坏
from .配置 import 会话查询错误#检索错误
from .来源 import 断言会话头兼容#头兼容断言

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否thenable(值):#判定可等待对象
    """判定值是否可等待。"""
    if 值 is None:#空不是
        return False#不是
    return callable(getattr(值,'wait',None)) or callable(getattr(值,'等待',None))#Future或thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        if callable(getattr(值,'wait',None)):#Future风格
            return 值.wait()#等待
        return 值.等待()#thenable
    return 值#同步值

def 信号已中止(信号):#信号是否已中止
    """信号是否已中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return getattr(信号,'aborted',False) is True or getattr(信号,'已中止',False) is True#中英旗标

def 信号抛出若已中止(信号):#已取消则抛出
    """已取消则抛出 SESSION_QUERY_ABORTED。"""
    if 信号已中止(信号):#已中止
        raise 会话查询错误('session-search aborted','SESSION_QUERY_ABORTED')#取消

class 会话语料库:#按此刻挂上的持久化服务解析优先活会话语料
    """按此刻挂上的持久化服务解析优先活会话的语料。"""
    def __init__(自身,上下文,持久检查并发):#构造语料库
        """可选注入 sessionPersistence，并记下持久检查并发。"""
        自身._上下文=上下文#Cordis上下文
        自身._持久化=None#当前可选持久化服务
        自身._持久检查并发=持久检查并发#并发上限
        def 持久化安装(子上下文):#注入持久化
            """记下当前持久化服务并在拆除时清绑定。"""
            服务=子上下文.sessionPersistence#取出服务
            自身._持久化=服务#换上
            def 摘掉():#拆除回调
                """过期 disposer 不能清掉替换绑定。"""
                if 自身._持久化 is 服务:#仍是本服务
                    自身._持久化=None#清空
            子上下文.effect(摘掉,'sessionQuery.persistenceBinding')#effect名
        纤程=上下文.inject(['sessionPersistence'],持久化安装)#可选注入
        上下文.effect(lambda:纤程.dispose(),'sessionQuery.optionalPersistence')#拆除fiber

    def 列出会话(自身,信号=None):#列出会话记录
        """列出完整逻辑语料，活会话优先，头已克隆。"""
        信号抛出若已中止(信号)#入口检查取消
        持久化=自身._持久化#快照当前持久化
        持久头们=[] if 持久化 is None else 列出持久(持久化,信号)#列出持久头
        信号抛出若已中止(信号)#列出后检查取消
        记录表={}#按id收记录
        for 头 in 持久头们:#先放持久记录
            记录表[取字段(头,'id')]={'header':结构化克隆(头),'live':False,'persisted':True}#克隆头
        for 会话 in 自身._上下文.sessions.list():#再覆盖活会话
            标识=取字段(取字段(会话,'header'),'id')#会话id
            耐久=记录表.get(标识)#对应持久记录
            if 耐久 is not None:#同时持久
                断言会话头兼容(取字段(会话,'header'),取字段(耐久,'header'))#头必须兼容
            记录表[标识]={'header':结构化克隆(取字段(会话,'header')),'live':True,'persisted':耐久 is not None}#活覆盖
        return sorted(记录表.values(),key=比较会话)#最新优先排序

    def 加载(自身,会话号,信号=None):#加载一条逻辑会话
        """加载一条逻辑源，优先脱离的活快照。"""
        信号抛出若已中止(信号)#入口检查取消
        活=自身._上下文.sessions.get(会话号)#先查活会话
        if 活 is not None:#活会话存在
            快照=拍活快照(活)#拍脱离快照
            信号抛出若已中止(信号)#快照后检查取消
            return 快照#返回活快照
        持久化=自身._持久化#再查持久化
        if 持久化 is None:#无持久化
            raise 未找到(会话号)#未找到
        持久头们=列出持久(持久化,信号)#列出持久头
        信号抛出若已中止(信号)#列出后检查取消
        列出头=next((头 for 头 in 持久头们 if 取字段(头,'id')==会话号),None)#找该id
        if 列出头 is None:#列表没有
            raise 未找到(会话号)#未找到
        已加载=检查持久(持久化,会话号,信号)#读取完整日志
        信号抛出若已中止(信号)#inspect后检查取消
        挂上=自身._上下文.sessions.get(会话号)#inspect期间可能已挂上
        if 挂上 is not None:#已变成活会话
            快照=拍活快照(挂上)#改用活快照
            信号抛出若已中止(信号)#快照后检查取消
            return 快照#返回活快照
        断言会话头兼容(取字段(已加载,'meta'),列出头)#头必须兼容
        快照={'header':结构化克隆(取字段(已加载,'meta')),'events':[结构化克隆(事件) for 事件 in 取字段(已加载,'events')]}#脱离快照
        信号抛出若已中止(信号)#组装后检查取消
        return 快照#返回持久快照

    def 批量投影(自身,会话号们,投影器,信号=None):#批量投影逻辑源
        """从一次持久列出立刻投影去重后的逻辑源。"""
        标识们=list(dict.fromkeys(会话号们))#按首次出现去重
        信号抛出若已中止(信号)#入口检查取消
        已解析={}#已解析结果
        未解析=[]#需要持久解析的id
        for 标识 in 标识们:#先解析活会话
            会话=自身._上下文.sessions.get(标识)#查活
            if 会话 is None:#不是活会话
                未解析.append(标识)#留给持久路径
            else:#是活会话
                已解析[标识]=投影源(标识,源活(会话),投影器,信号)#当场投影
        if len(未解析)==0:#全是活会话
            return 有序结果(标识们,已解析)#按输入顺序返回
        持久化=自身._持久化#取出持久化
        if 持久化 is None:#没有持久化后端
            for 标识 in 未解析:#剩下的都未找到
                已解析[标识]={'sessionId':标识,'status':'rejected','reason':未找到(标识)}#记未找到
            return 有序结果(标识们,已解析)#返回
        try:#列出持久会话
            持久头们=列出持久(持久化,信号)#列出
            信号抛出若已中止(信号)#列出后检查取消
        except Exception as 错误:#列出失败
            if 信号已中止(信号):#取消优先
                信号抛出若已中止(信号)#抛出取消
            for 标识 in 未解析:#整批记失败
                已解析[标识]={'sessionId':标识,'status':'rejected','reason':错误}#记下原因
            return 有序结果(标识们,已解析)#返回
        持久索引={取字段(头,'id'):头 for 头 in 持久头们}#按id索引
        锁=threading.Lock()#保护已解析表
        def 解析持久(标识):#解析一条持久会话
            """解析一条持久会话并投影。"""
            列出头=持久索引.get(标识)#列表里的头
            if 列出头 is None:#持久列表没有
                挂上=自身._上下文.sessions.get(标识)#列出后可能已挂上
                结果=投影源(标识,源活(挂上),投影器,信号) if 挂上 is not None else {'sessionId':标识,'status':'rejected','reason':未找到(标识)}#投影或未找到
                with 锁:#写入
                    已解析[标识]=结果#记下
                return#本条结束
            try:#inspect并投影
                信号抛出若已中止(信号)#inspect前检查取消
                已加载=检查持久(持久化,标识,信号)#读取完整日志
                信号抛出若已中止(信号)#inspect后检查取消
                挂上=自身._上下文.sessions.get(标识)#inspect期间可能已挂上
                if 挂上 is not None:#已变成活会话
                    结果=投影源(标识,源活(挂上),投影器,信号)#改用活源
                else:#仍是持久
                    断言会话头兼容(取字段(已加载,'meta'),列出头)#头必须兼容
                    结果=投影源(标识,{'header':取字段(已加载,'meta'),'events':取字段(已加载,'events')},投影器,信号)#投影持久源
                with 锁:#写入
                    已解析[标识]=结果#记下
            except Exception as 错误:#本条失败
                if 信号已中止(信号):#取消优先
                    信号抛出若已中止(信号)#抛出取消
                with 锁:#写入
                    已解析[标识]={'sessionId':标识,'status':'rejected','reason':错误}#记下原因
        游标={'值':0}#共享游标
        def 工人():#持久检查工人
            """领任务直到没有更多。"""
            while True:#领完为止
                信号抛出若已中止(信号)#领任务前检查取消
                with 锁:#领取
                    if 游标['值']>=len(未解析):#没有更多
                        return#结束
                    标识=未解析[游标['值']]#领取
                    游标['值']+=1#推进
                解析持久(标识)#解析
        工人数=min(自身._持久检查并发,len(未解析))#工人数
        if 工人数>0:#有工人
            线程们=[threading.Thread(target=工人) for _ in range(工人数)]#启动工人
            for 线程 in 线程们:#等待
                线程.start()#启动
            for 线程 in 线程们:#汇合
                线程.join()#等待
        信号抛出若已中止(信号)#返回前再检查取消
        return 有序结果(标识们,已解析)#按输入顺序返回

def 投影源(会话号,源,投影器,信号=None):#同步投影一条源
    """同步投影一条借用源。"""
    try:#跑投影器
        信号抛出若已中止(信号)#投影前检查取消
        值=投影器(源)#同步折叠
        信号抛出若已中止(信号)#投影后检查取消
        return {'sessionId':会话号,'status':'fulfilled','value':值}#兑现
    except Exception as 原因:#投影失败
        if 信号已中止(信号):#取消优先
            信号抛出若已中止(信号)#抛出取消
        return {'sessionId':会话号,'status':'rejected','reason':原因}#拒绝

def 源活(会话):#把活会话收成借用源
    """直接借用活对象的头与事件。"""
    return {'header':取字段(会话,'header'),'events':取字段(会话,'events')}#借用源

def 有序结果(标识们,已解析):#按输入id顺序取出结果
    """按输入 id 顺序取出投影结果。"""
    return [已解析[标识] for 标识 in 标识们]#有序列表

def 列出持久(持久化,信号=None):#列出持久会话头
    """列出持久会话头。"""
    try:#列出
        return 解开(持久化.列出(信号))#委托持久化
    except Exception as 错误:#列出失败
        if 信号已中止(信号):#取消优先
            信号抛出若已中止(信号)#抛出取消
        raise 会话查询错误(f'session persistence listing failed: {错误消息(错误)}','SESSION_QUERY_PERSISTENCE_FAILED',{'cause':错误})#打出失败

def 检查持久(持久化,会话号,信号=None):#读取一条持久会话
    """inspect 一条持久会话。"""
    try:#inspect
        return 解开(持久化.检查(会话号,信号))#委托持久化
    except Exception as 错误:#inspect失败
        if 信号已中止(信号):#取消优先
            信号抛出若已中止(信号)#抛出取消
        if isinstance(错误,会话持久化损坏错误):#存储损坏
            raise 会话查询错误(f'stored session "{会话号}" is corrupt: {错误消息(错误)}','SESSION_QUERY_CORRUPT_SESSION',{'cause':错误})#损坏
        raise 会话查询错误(f'failed to inspect session "{会话号}": {错误消息(错误)}','SESSION_QUERY_PERSISTENCE_FAILED',{'cause':错误})#持久失败

def 拍活快照(会话):#拍活会话脱离快照
    """克隆活会话的头与事件。"""
    return {'header':结构化克隆(取字段(会话,'header')),'events':[结构化克隆(事件) for 事件 in 取字段(会话,'events')]}#脱离快照

def 比较会话(甲,乙):#最新优先，其次按id
    """最新优先排序键。"""
    甲头=取字段(甲,'header')#甲头
    乙头=取字段(乙,'header')#乙头
    if 取字段(乙头,'createdAt')!=取字段(甲头,'createdAt'):#时间不同
        return (取字段(乙头,'createdAt')>取字段(甲头,'createdAt'))-(取字段(乙头,'createdAt')<取字段(甲头,'createdAt'))#时间倒序
    if 取字段(甲头,'id')==取字段(乙头,'id'):#同id
        return 0#相等
    return -1 if 取字段(甲头,'id')<取字段(乙头,'id') else 1#id升序

def 未找到(会话号):#包装会话未找到
    """包装会话未找到错误。"""
    return 会话查询错误(f'session "{会话号}" not found','SESSION_QUERY_SESSION_NOT_FOUND')#未找到

def 错误消息(错误):#取出可打印消息
    """取出可打印错误消息。"""
    return 取字段(错误,'message',str(错误)) if isinstance(错误,BaseException) else 'unknown error'#消息
