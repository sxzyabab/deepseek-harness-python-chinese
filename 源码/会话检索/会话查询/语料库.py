"""会话检索用的活/已持久逻辑语料解析。"""
import threading#并发持久检查工作线程
from ....模型后端.llm import 结构化克隆#拆离克隆
from ....会话.会话持久化 import 会话持久化损坏错误#持久化损坏
from .配置 import 会话查询错误,已中止,若已中止则抛出#检索错误与中止
from .来源 import 校验会话头兼容#头兼容断言
from .冷读 import 读冷会话日志#句柄冷读 + 中断闭合

class 会话语料库:
    """按此刻挂上的持久化服务解析优先活会话的语料。"""
    def __init__(自身,上下文,持久检查并发):
        """可选依赖 sessionPersistence，并记下持久检查并发。"""
        自身._上下文=上下文#框架上下文
        自身._持久化=None#当前可选持久化服务
        自身._持久检查并发=持久检查并发#并发上限
        def 持久化安装(子上下文):
            """记下当前持久化服务并在拆除时清绑定。"""
            服务=子上下文.sessionPersistence#取出服务
            自身._持久化=服务#换上
            def 摘掉():
                """过期 disposer 不能清掉替换绑定。"""
                if 自身._持久化 is 服务:#仍是本服务
                    自身._持久化=None#清空
            子上下文.副作用(摘掉,'sessionQuery.persistenceBinding')#effect名
        纤程=上下文.依赖启动(['sessionPersistence'],持久化安装)#可选依赖
        def 拆除纤程():
            """拆除可选持久化 fiber。"""
            纤程.dispose()#拆除
        上下文.副作用(拆除纤程,'sessionQuery.optionalPersistence')#拆除fiber

    def 列出会话(自身,信号=None):
        """列出完整逻辑语料，活会话优先，头已克隆。"""
        若已中止则抛出(信号)#入口检查取消
        持久化=自身._持久化#快照当前持久化
        持久头列表=[] if 持久化 is None else 列出持久(持久化,信号)#列出持久头
        若已中止则抛出(信号)#列出后检查取消
        记录表={}#按id收记录
        for 头 in 持久头列表:#先放持久记录
            记录表[头['id']]={'header':结构化克隆(头),'live':False,'persisted':True}#克隆头
        for 会话 in 自身._上下文.sessions.list():#再覆盖活会话
            标识=会话.header['id']#会话id
            耐久=记录表[标识] if 标识 in 记录表 else None#对应持久记录
            if 耐久 is not None:#同时持久
                校验会话头兼容(会话.header,耐久['header'])#头必须兼容
            记录表[标识]={'header':结构化克隆(会话.header),'live':True,'persisted':耐久 is not None}#活覆盖
        return sorted(记录表.values(),key=会话排序键)#最新优先排序

    def 加载(自身,会话号,信号=None):
        """加载一条逻辑源，优先脱离的活快照。"""
        若已中止则抛出(信号)#入口检查取消
        活=自身._上下文.sessions.get(会话号)#先查活会话
        if 活 is not None:#活会话存在
            快照=拍活快照(活)#拍脱离快照
            若已中止则抛出(信号)#快照后检查取消
            return 快照#返回活快照
        持久化=自身._持久化#再查持久化
        if 持久化 is None:#无持久化
            raise 未找到(会话号)#未找到
        持久头列表=列出持久(持久化,信号)#列出持久头
        若已中止则抛出(信号)#列出后检查取消
        列出头=None#该id头
        for 头 in 持久头列表:#找该id
            if 头['id']==会话号:#命中
                列出头=头#记下
                break#停
        if 列出头 is None:#列表没有
            raise 未找到(会话号)#未找到
        已加载=检查持久(持久化,会话号,信号)#读取完整日志
        若已中止则抛出(信号)#inspect后检查取消
        挂上=自身._上下文.sessions.get(会话号)#inspect期间可能已挂上
        if 挂上 is not None:#已变成活会话
            快照=拍活快照(挂上)#改用活快照
            若已中止则抛出(信号)#快照后检查取消
            return 快照#返回活快照
        校验会话头兼容(已加载['meta'],列出头)#头必须兼容
        快照={#脱离快照
            'header':结构化克隆(已加载['meta']),#克隆头
            'inheritedEventCount':已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,#继承切口
            'events':[结构化克隆(事件) for 事件 in 已加载['events']],#克隆事件
        }#快照结束
        若已中止则抛出(信号)#组装后检查取消
        return 快照#返回持久快照

    def 批量投影(自身,会话号列表,投影器,信号=None):
        """从一次持久列出立刻投影去重后的逻辑源。"""
        标识列表=list(dict.fromkeys(会话号列表))#按首次出现去重
        若已中止则抛出(信号)#入口检查取消
        已解析={}#已解析结果
        未解析=[]#需要持久解析的id
        for 标识 in 标识列表:#先解析活会话
            会话=自身._上下文.sessions.get(标识)#查活
            if 会话 is None:#不是活会话
                未解析.append(标识)#留给持久路径
            else:#是活会话
                已解析[标识]=投影源(标识,源活(会话),投影器,信号)#当场投影
        if len(未解析)==0:#全是活会话
            return 有序结果(标识列表,已解析)#按输入顺序返回
        持久化=自身._持久化#取出持久化
        if 持久化 is None:#没有持久化后端
            for 标识 in 未解析:#剩下的都未找到
                已解析[标识]={'sessionId':标识,'status':'rejected','reason':未找到(标识)}#记未找到
            return 有序结果(标识列表,已解析)#返回
        try:#列出持久会话
            持久头列表=列出持久(持久化,信号)#列出
            若已中止则抛出(信号)#列出后检查取消
        except Exception as 错误:#列出失败收成整批 rejected；取消优先
            if 已中止(信号):#取消优先
                若已中止则抛出(信号)#抛出取消
            for 标识 in 未解析:#整批记失败
                已解析[标识]={'sessionId':标识,'status':'rejected','reason':错误}#记下原因
            return 有序结果(标识列表,已解析)#返回
        持久索引={头['id']:头 for 头 in 持久头列表}#按id索引
        锁=threading.Lock()#保护已解析表
        def 解析持久(标识):
            """解析一条持久会话并投影。"""
            if 标识 not in 持久索引:#持久列表没有
                挂上=自身._上下文.sessions.get(标识)#列出后可能已挂上
                结果=投影源(标识,源活(挂上),投影器,信号) if 挂上 is not None else {'sessionId':标识,'status':'rejected','reason':未找到(标识)}#投影或未找到
                with 锁:#写入
                    已解析[标识]=结果#记下
                return#本条结束
            列出头=持久索引[标识]#列表里的头
            try:#inspect并投影
                若已中止则抛出(信号)#inspect前检查取消
                已加载=检查持久(持久化,标识,信号)#读取完整日志
                若已中止则抛出(信号)#inspect后检查取消
                挂上=自身._上下文.sessions.get(标识)#inspect期间可能已挂上
                if 挂上 is not None:#已变成活会话
                    结果=投影源(标识,源活(挂上),投影器,信号)#改用活源
                else:#仍是持久
                    校验会话头兼容(已加载['meta'],列出头)#头必须兼容
                    结果=投影源(标识,{'header':已加载['meta'],'inheritedEventCount':已加载['inheritedEventCount'] if 'inheritedEventCount' in 已加载 else 0,'events':已加载['events']},投影器,信号)#投影持久源
                with 锁:#写入
                    已解析[标识]=结果#记下
            except Exception as 错误:#本条失败收成 rejected；取消优先
                if 已中止(信号):#取消优先
                    若已中止则抛出(信号)#抛出取消
                with 锁:#写入
                    已解析[标识]={'sessionId':标识,'status':'rejected','reason':错误}#记下原因
        游标={'值':0}#共享游标
        def 工作线程体():
            """领任务直到没有更多。"""
            while True:#领完为止
                若已中止则抛出(信号)#领任务前检查取消
                with 锁:#领取
                    if 游标['值']>=len(未解析):#没有更多
                        return
                    标识=未解析[游标['值']]#领取
                    游标['值']+=1#推进
                解析持久(标识)#解析
        工作线程数=min(自身._持久检查并发,len(未解析))#工作线程数
        if 工作线程数>0:#有工作线程
            线程表=[threading.Thread(target=工作线程体) for _ in range(工作线程数)]#启动工作线程
            for 线程 in 线程表:#等待
                线程.start()
            for 线程 in 线程表:#汇合
                线程.join()#等待
        若已中止则抛出(信号)#返回前再检查取消
        return 有序结果(标识列表,已解析)#按输入顺序返回

def 投影源(会话号,源,投影器,信号=None):
    """同步投影一条借用源。"""
    try:#跑投影器
        若已中止则抛出(信号)#投影前检查取消
        值=投影器(源)#同步折叠
        若已中止则抛出(信号)#投影后检查取消
        return {'sessionId':会话号,'status':'fulfilled','value':值}#兑现
    except Exception as 原因:#投影失败收成 rejected；取消优先
        if 已中止(信号):#取消优先
            若已中止则抛出(信号)#抛出取消
        return {'sessionId':会话号,'status':'rejected','reason':原因}#拒绝

def 源活(会话):
    """直接借用活对象的头、继承切口与事件。"""
    return {'header':会话.header,'inheritedEventCount':getattr(会话,'inheritedEventCount',0),'events':会话.events}#借用源

def 有序结果(标识列表,已解析):
    """按输入 id 顺序取出投影结果。"""
    return [已解析[标识] for 标识 in 标识列表]#有序列表

def 列出持久(持久化,信号=None):
    """列出持久会话头。"""
    try:#列出
        return 持久化.列出(信号)#委托持久化
    except Exception as 错误:#列出失败收成 PERSISTENCE_FAILED；取消优先
        if 已中止(信号):#取消优先
            若已中止则抛出(信号)#抛出取消
        raise 会话查询错误('session persistence listing failed: '+错误消息(错误),'SESSION_QUERY_PERSISTENCE_FAILED',{'cause':错误})#打出失败

def 检查持久(持久化,会话号,信号=None):
    """冷读一条持久会话（已存 + 中断末回合内存闭合），映射查询错误。"""
    try:#冷读
        冷=读冷会话日志(持久化,会话号,信号)#句柄冷读
        return {
            'meta':冷['header'],#头（语料沿用 meta 键）
            'inheritedEventCount':冷['inheritedEventCount'] if 'inheritedEventCount' in 冷 else 0,#继承
            'events':list(冷['events']) if 冷.get('events') is not None else [],#平衡事件
            'eventState':冷['eventState'] if 'eventState' in 冷 else None,#别名状态
        }#持久快照
    except Exception as 错误:#冷读失败；损坏单独分类
        if 已中止(信号):#取消优先
            若已中止则抛出(信号)#抛出取消
        if isinstance(错误,会话持久化损坏错误):#存储损坏
            raise 会话查询错误('stored session "'+str(会话号)+'" is corrupt: '+错误消息(错误),'SESSION_QUERY_CORRUPT_SESSION',{'cause':错误})#损坏
        raise 会话查询错误('failed to read stored session "'+str(会话号)+'": '+错误消息(错误),'SESSION_QUERY_PERSISTENCE_FAILED',{'cause':错误})#持久失败

def 拍活快照(会话):
    """克隆活会话的头、继承切口与事件。"""
    return {'header':结构化克隆(会话.header),'inheritedEventCount':getattr(会话,'inheritedEventCount',0),'events':[结构化克隆(事件) for 事件 in 会话.events]}#脱离快照

def 会话排序键(记录):
    """最新优先，其次按 id。"""
    头=记录['header']#头
    return (-头['createdAt'],头['id'])#时间倒序再 id

def 未找到(会话号):
    """包装会话未找到错误。"""
    return 会话查询错误('session "'+str(会话号)+'" not found','SESSION_QUERY_SESSION_NOT_FOUND')#未找到

def 错误消息(错误):
    """取出可打印错误消息。"""
    return str(错误) if isinstance(错误,BaseException) else 'unknown error'#消息
