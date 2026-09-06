"""仅宿主侧、从已提交 Session 事件增量投影的 Team 状态。

对齐上游 `agent-team/src/projection.ts`。公开面仅中文名。
Python 侧不做 zod；校验函数对齐上游 schema 语义。
"""
import re#数字任务 id
from .类型 import 团队标识,团队消息标识,团队任务标识#身份构造
from .任务图 import 断言任务图候选#图校验
from .错误 import 团队错误#领域错误

__all__=[#仅中文公开名
    '空团队状态','是否团队事件','团队投影定义',
]#公开面结束

核心内容块类型=frozenset(['text','reasoning','image','tool-call','tool-result'])#核心块
数字任务标识模式=re.compile(r'^task-([0-9]+)\Z')#数字任务 id
安全整数上限=9007199254740991#外来 JSON 校验上限

def 空团队状态(根标识):#空状态
    """为一个 Team 身份构造空状态。"""
    return {#可变空状态
        'id':团队标识(根标识),#团队 id
        'members':[],#无成员
        'tasks':[],#无任务
        'messages':[],#无消息
        'delivered':[],#无投递
        'nextTaskNumber':1,#从 1 起
    }#结束

def 是否团队事件(事件):#是否 Team 事件
    """测试一条 Session 事件是否属于 Team 域。"""
    if 事件 is None or 'type' not in 事件:#无类型
        return False#否
    return 事件['type'] in (#Team 域类型
        'team/member','team/task','team/message/queued','team/message/delivered',
    )#联合结束

def 解析持久(类型,解析器,值):#解析持久载荷
    """解码一个持久 Team 值，并把失败保留为 cause。"""
    try:#试解析
        return 解析器(值)#解析
    except Exception as 错误:#解析器可能抛 TypeError/KeyError/团队错误，契约未定所以收不窄
        包装=团队错误('persisted Agent Teams '+类型+' payload is invalid','TEAM_INVALID_ARGUMENT')#包装
        包装.__cause__=错误#挂 cause
        raise 包装#抛出

def 校验会话标识(值):#SessionId
    """非空字符串 SessionId。"""
    if not isinstance(值,str) or len(值)<1:#非法
        raise 团队错误('invalid session id','TEAM_INVALID_ARGUMENT')#拒绝
    return 值#通过

def 校验团队标识(值):#TeamId
    """非空字符串 TeamId。"""
    return 团队标识(校验会话标识(值))#烙印

def 校验任务标识(值):#TeamTaskId
    """任务 id；数字后缀须安全整数。"""
    if not isinstance(值,str) or len(值)<1:#非法
        raise 团队错误('invalid task id','TEAM_INVALID_ARGUMENT')#拒绝
    匹配=数字任务标识模式.match(值)#匹配后缀
    if 匹配 is not None:#有数字后缀
        号=int(匹配.group(1))#后缀
        if isinstance(号,bool) or 号<0 or 号>安全整数上限:#后缀非法
            raise 团队错误('numeric task id suffix must be a safe integer','TEAM_INVALID_ARGUMENT')#拒绝
    return 团队任务标识(值)#烙印

def 校验消息标识(值):#TeamMessageId
    """非空消息 id。"""
    return 团队消息标识(校验会话标识(值))#烙印

def 校验内容块(块):#内容块
    """校验一个内容块；核心变体精确，其它保留 type 标签。"""
    if not isinstance(块,dict):#须映射
        raise 团队错误('content block must be object','TEAM_INVALID_ARGUMENT')#拒绝
    if 'type' not in 块:#缺类型
        raise 团队错误('content block type required','TEAM_INVALID_ARGUMENT')#拒绝
    类型=块['type']#类型标签
    if not isinstance(类型,str) or len(类型)<1:#非法类型
        raise 团队错误('content block type required','TEAM_INVALID_ARGUMENT')#拒绝
    if 类型=='text' or 类型=='reasoning':#文本类
        if set(块.keys())-{'type','text'}:#多余键
            raise 团队错误('strict content block','TEAM_INVALID_ARGUMENT')#拒绝
        if 'text' not in 块 or not isinstance(块['text'],str):#须字符串
            raise 团队错误('text required','TEAM_INVALID_ARGUMENT')#拒绝
        return dict(块)#通过
    if 类型=='image':#图片
        if 'attachment' not in 块 or not isinstance(块['attachment'],dict):#须对象
            raise 团队错误('image attachment required','TEAM_INVALID_ARGUMENT')#拒绝
        return {'type':'image','attachment':dict(块['attachment'])}#通过
    if 类型=='tool-call':#工具调用
        return dict(块)#保留
    if 类型=='tool-result':#工具结果
        if 'content' not in 块 or not isinstance(块['content'],list):#须数组
            raise 团队错误('tool-result content required','TEAM_INVALID_ARGUMENT')#拒绝
        结果={#规范化
            'type':'tool-result',#类型
            'toolCallId':块['toolCallId'] if 'toolCallId' in 块 else None,#调用 id
            'content':[校验内容块(子) for 子 in 块['content']],#递归
        }#骨架
        if 'isError' in 块:#可选错误
            结果['isError']=块['isError']#写入
        return 结果#结束
    if 类型 in 核心内容块类型:#已知类型字段不对
        raise 团队错误('known content block types must match their declared fields','TEAM_INVALID_ARGUMENT')#拒绝
    return dict(块)#插件扩展块

def 校验成员快照(值):#成员快照
    """校验成员快照。"""
    if not isinstance(值,dict):#须映射
        raise 团队错误('member snapshot required','TEAM_INVALID_ARGUMENT')#拒绝
    结果={#规范化
        'id':校验会话标识(值['id'] if 'id' in 值 else None),#成员 Session
        'name':值['name'] if 'name' in 值 else None,#名字
        'description':值['description'] if 'description' in 值 else None,#描述
        'provider':值['provider'] if 'provider' in 值 else None,#provider
        'context':值['context'] if 'context' in 值 else None,#上下文
        'phase':值['phase'] if 'phase' in 值 else None,#阶段
    }#骨架
    if 结果['context'] not in ('fresh','fork'):#非法上下文
        raise 团队错误('invalid member context','TEAM_INVALID_ARGUMENT')#拒绝
    if 结果['phase'] not in ('provisioning','active','failed'):#非法阶段
        raise 团队错误('invalid member phase','TEAM_INVALID_ARGUMENT')#拒绝
    if 'error' in 值:#可选错误
        结果['error']=值['error']#写入
    return 结果#通过

def 校验任务快照(值):#任务快照
    """校验任务快照。"""
    if not isinstance(值,dict):#须映射
        raise 团队错误('task snapshot required','TEAM_INVALID_ARGUMENT')#拒绝
    if 'revision' not in 值:#缺版本
        raise 团队错误('invalid task revision','TEAM_INVALID_ARGUMENT')#拒绝
    修订=值['revision']#版本
    if (not isinstance(修订,int) or isinstance(修订,bool) or 修订<1
            or 修订>安全整数上限):#须正安全整数
        raise 团队错误('invalid task revision','TEAM_INVALID_ARGUMENT')#拒绝
    结果={#规范化
        'id':校验任务标识(值['id'] if 'id' in 值 else None),#任务 id
        'revision':int(修订),#版本
        'subject':值['subject'] if 'subject' in 值 else None,#标题
        'description':值['description'] if 'description' in 值 else None,#详情
        'status':值['status'] if 'status' in 值 else None,#状态
        'blockedBy':[校验任务标识(项) for 项 in (值['blockedBy'] if 'blockedBy' in 值 else [])],#依赖
        'writeScopes':list(值['writeScopes'] if 'writeScopes' in 值 else []),#写范围
    }#骨架
    if 结果['status'] not in ('pending','in_progress','completed','deleted'):#非法状态
        raise 团队错误('invalid task status','TEAM_INVALID_ARGUMENT')#拒绝
    if 'ownerId' in 值 and 值['ownerId'] is not None:#可选 owner
        结果['ownerId']=校验会话标识(值['ownerId'])#写入
    return 结果#通过

def 校验消息快照(值):#消息快照
    """校验消息快照。"""
    if not isinstance(值,dict):#须映射
        raise 团队错误('message snapshot required','TEAM_INVALID_ARGUMENT')#拒绝
    return {#规范化
        'id':校验消息标识(值['id'] if 'id' in 值 else None),#消息 id
        'senderId':校验会话标识(值['senderId'] if 'senderId' in 值 else None),#发送方
        'senderName':值['senderName'] if 'senderName' in 值 else None,#发送方名
        'targetId':校验会话标识(值['targetId'] if 'targetId' in 值 else None),#目标
        'content':[校验内容块(块) for 块 in (值['content'] if 'content' in 值 else [])],#内容
    }#结束

def 校验成员事件(数据):#成员事件
    """version=2 成员事件。"""
    if 'version' not in 数据 or 数据['version']!=2:#版本
        raise 团队错误('unsupported member event version','TEAM_INVALID_ARGUMENT')#拒绝
    return {#规范化
        'version':2,#版本
        'teamId':校验团队标识(数据['teamId']),#团队
        'member':校验成员快照(数据['member']),#成员
    }#结束

def 校验任务事件(数据):#任务事件
    """version=2 任务事件。"""
    if 'version' not in 数据 or 数据['version']!=2:#版本
        raise 团队错误('unsupported task event version','TEAM_INVALID_ARGUMENT')#拒绝
    return {#规范化
        'version':2,#版本
        'teamId':校验团队标识(数据['teamId']),#团队
        'task':校验任务快照(数据['task']),#任务
    }#结束

def 校验入队事件(数据):#入队事件
    """version=2 入队事件。"""
    if 'version' not in 数据 or 数据['version']!=2:#版本
        raise 团队错误('unsupported queued event version','TEAM_INVALID_ARGUMENT')#拒绝
    return {#规范化
        'version':2,#版本
        'teamId':校验团队标识(数据['teamId']),#团队
        'message':校验消息快照(数据['message']),#消息
    }#结束

def 校验投递事件(数据):#投递事件
    """version=2 投递事件。"""
    if 'version' not in 数据 or 数据['version']!=2:#版本
        raise 团队错误('unsupported delivered event version','TEAM_INVALID_ARGUMENT')#拒绝
    return {#规范化
        'version':2,#版本
        'teamId':校验团队标识(数据['teamId']),#团队
        'messageId':校验消息标识(数据['messageId']),#消息
        'targetId':校验会话标识(数据['targetId']),#目标
    }#结束

def 解析当前团队事件(事件):#解码当前事件
    """按 Team 事件类型解码完整当前版本载荷。"""
    类型=事件['type']#类型
    数据=事件['data']#载荷
    if 类型=='team/member':#成员
        return {**_事件壳(事件),'data':解析持久(类型,校验成员事件,数据)}#成员
    if 类型=='team/task':#任务
        return {**_事件壳(事件),'data':解析持久(类型,校验任务事件,数据)}#任务
    if 类型=='team/message/queued':#入队
        return {**_事件壳(事件),'data':解析持久(类型,校验入队事件,数据)}#入队
    if 类型=='team/message/delivered':#投递
        return {**_事件壳(事件),'data':解析持久(类型,校验投递事件,数据)}#投递
    return 事件#穷尽兜底

def _事件壳(事件):#事件浅壳
    """保留事件元字段。"""
    return dict(事件)#拷贝

def 应用投影事件(状态,事件):#应用投影事件
    """增量应用一条 Session 事件。"""
    if 'failure' in 状态:#已失败则停
        return#停
    if not 是否团队事件(事件):#非 Team 事件
        return#停
    try:#试应用
        选择器=解析持久(事件['type'],_校验选择器,事件['data'])#选团队
        if 选择器['teamId']!=状态['id']:#非本团队
            return#跳过
        if 选择器['version']!=2:#版本拒
            raise 团队错误('unsupported Agent Teams event version '+str(选择器['version']),'TEAM_INVALID_ARGUMENT')#版本拒
        应用当前团队事件(状态,解析当前团队事件(事件))#应用
    except Exception as 错误:#应用团队事件可能抛团队错误/校验错误，契约未定所以收不窄
        状态['failure']=str(错误)#记失败

def _校验选择器(数据):#事件选择器
    """version+teamId 选择器。"""
    版本=数据['version'] if 'version' in 数据 else None#版本
    if (not isinstance(版本,int) or isinstance(版本,bool) or 版本<0
            or 版本>安全整数上限):#非法
        raise 团队错误('invalid event version','TEAM_INVALID_ARGUMENT')#拒绝
    return {'version':int(版本),'teamId':校验团队标识(数据['teamId'])}#通过

def 应用当前团队事件(状态,事件):#应用当前事件
    """应用已解码的当前版本 Team 事件。"""
    类型=事件['type']#类型
    数据=事件['data']#载荷
    if 类型=='team/member':#成员
        _应用成员(状态,数据['member'])#成员
        return#结束
    if 类型=='team/task':#任务
        _应用任务(状态,数据['task'])#任务
        return#结束
    if 类型=='team/message/queued':#入队
        _应用入队(状态,数据['message'])#入队
        return#结束
    if 类型=='team/message/delivered':#投递
        _应用投递(状态,数据)#投递
        return#结束

def _应用成员(状态,成员):#应用成员边
    """成员生命周期边。"""
    成员列表=状态['members']#成员表
    下标=下一索引(成员列表,成员['id'])#按 id 找
    先前=成员列表[下标] if 下标>=0 else None#先前
    同名=None#按名找
    for 候选 in 成员列表:#扫同名
        if 候选['name']==成员['name']:#命中
            同名=候选#记下
            break#结束
    if 同名 is not None and 同名['id']!=成员['id']:#名复用
        raise 团队错误('teammate name "'+成员['name']+'" is reused by another member','TEAM_INVALID_ARGUMENT')#名复用
    if 先前 is None:#新建
        if 成员['phase']!='provisioning':#须从供应起
            raise 团队错误('teammate "'+成员['name']+'" must begin provisioning','TEAM_INVALID_ARGUMENT')#须供应
    else:#替换
        if 先前['name']!=成员['name'] or 先前['provider']!=成员['provider'] or 先前['context']!=成员['context']:#不可变
            raise 团队错误('teammate "'+成员['id']+'" changed immutable identity fields','TEAM_INVALID_ARGUMENT')#不可变
        if 先前['phase']!='provisioning' or 成员['phase']=='provisioning':#非法转换
            raise 团队错误(#非法转换
                'teammate "'+成员['name']+'" has an invalid '+先前['phase']+' -> '+成员['phase']+' transition',#文案
                'TEAM_INVALID_ARGUMENT',#码
            )#抛出
    if 下标<0:#新建
        成员列表.append(成员)#追加
    else:#替换
        成员列表[下标]=成员#替换

def _应用任务(状态,任务):#应用任务边
    """任务快照边。"""
    任务列表=状态['tasks']#任务表
    下标=下一索引(任务列表,任务['id'])#按 id 找
    先前=任务列表[下标] if 下标>=0 else None#先前
    if 先前 is None and 任务['revision']!=1:#首版须 1
        raise 团队错误('team task "'+任务['id']+'" must begin at revision 1','TEAM_INVALID_ARGUMENT')#首版
    if 先前 is not None and 任务['revision']!=先前['revision']+1:#版本须连续
        raise 团队错误('team task "'+任务['id']+'" revision is not contiguous','TEAM_INVALID_ARGUMENT')#连续
    断言任务图候选(任务列表,任务)#图校验
    匹配=数字任务标识模式.match(任务['id'])#解析序号
    if 匹配 is not None:#有数字后缀
        号=int(匹配.group(1))#任务号
        状态['nextTaskNumber']=max(状态['nextTaskNumber'],号+1)#推进
    if 下标<0:#新建
        任务列表.append(任务)#追加
    else:#替换
        任务列表[下标]=任务#替换

def _应用入队(状态,消息):#应用入队
    """邮箱入队边。"""
    for 候选 in 状态['messages']:#查重
        if 候选['id']==消息['id']:#重复
            raise 团队错误('team message "'+消息['id']+'" was queued twice','TEAM_INVALID_ARGUMENT')#重复
    状态['messages'].append(消息)#追加

def _应用投递(状态,数据):#应用投递
    """邮箱投递确认边。"""
    消息标识=数据['messageId']#消息 id
    目标标识=数据['targetId']#目标
    已入队=None#找入队
    for 消息 in 状态['messages']:#扫
        if 消息['id']==消息标识:#命中
            已入队=消息#记下
            break#结束
    if 已入队 is None:#未入队
        raise 团队错误('team message "'+str(消息标识)+'" was delivered before queueing','TEAM_INVALID_ARGUMENT')#未入队
    if 已入队['targetId']!=目标标识:#目标变
        raise 团队错误('team message "'+str(消息标识)+'" target changed','TEAM_INVALID_ARGUMENT')#目标变
    if 消息标识 in 状态['delivered']:#重复投递
        raise 团队错误('team message "'+str(消息标识)+'" was delivered twice','TEAM_INVALID_ARGUMENT')#重复
    状态['delivered'].append(消息标识)#记投递

def 下一索引(表,标识):#按 id 找下标
    """在快照表中按 id 找下标。"""
    for 下标,项 in enumerate(表):#扫
        if 项['id']==标识:#命中
            return 下标#下标
    return -1#未找到

def 应用投影(状态,事件):#投影 apply
    """投影定义的 apply 入口。"""
    应用投影事件(状态,事件)#增量应用
    return 状态#返回同对象

def 初始化投影(头):#投影 init
    """按会话头初始化。"""
    return 空团队状态(头['id'])#空状态

团队投影定义={#投影定义
    'key':'agentTeam',#投影键
    'stateVersion':3,#状态版本
    'stateSchema':None,#Python 侧不做 zod
    'init':初始化投影,#按头初始化
    'apply':应用投影,#增量应用
}#定义结束
