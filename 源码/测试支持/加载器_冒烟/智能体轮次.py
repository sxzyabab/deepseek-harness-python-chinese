"""测试专用的直接智能体轮次驱动，供组装后的 Loader fixture 共享。

对齐上游 `loader-smoke/src/agent-turn.ts`。公开面仅中文名。
"""
from threading import Event as 事件#首次发布等待
from ...模型后端.llm import 创建用户消息#构造用户消息

__all__=['驱动夹具轮次','累加用量','助手文本']#仅中文公开名

def 累加用量(合计,步进):#累加 token 用量
    """把一步用量累加进合计。"""
    下一={#合计
        'inputTokens':(合计 or {}).get('inputTokens',0)+步进.get('inputTokens',0),#累加输入
        'outputTokens':(合计 or {}).get('outputTokens',0)+步进.get('outputTokens',0),#累加输出
    }#合计结束
    for 键 in ('cacheReadTokens','cacheWriteTokens','reasoningTokens'):#可选字段
        if (合计 or {}).get(键) is not None or 步进.get(键) is not None:#有任一
            下一[键]=(合计 or {}).get(键,0)+步进.get(键,0)#可选字段累加
    return 下一#返回合计用量

def 助手文本(事件):#提取助手文本
    """从 assistant/message 事件拼接文本块。"""
    数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',None)#事件数据
    消息=数据.get('message') if isinstance(数据,dict) else getattr(数据,'message',None)#消息
    内容=消息.get('content') if isinstance(消息,dict) else getattr(消息,'content',None)#内容
    if not isinstance(内容,list):#无内容
        return None#无文本
    块们=[块 for 块 in 内容 if (块.get('type') if isinstance(块,dict) else getattr(块,'type',None))=='text']#筛文本块
    if len(块们)==0:#无文本块
        return None#无文本
    return ''.join((块.get('text') if isinstance(块,dict) else 块.text) for 块 in 块们)#拼接文本

def 唯一根智能体(上下文):#取得唯一根智能体
    """要求恰好一个已配置根智能体。"""
    注册表=上下文.get('agents')#智能体注册表
    if 注册表 is None:#无注册表
        raise Error('fixture turn requires exactly one top-level agent, found 0')#无注册表
    根们=注册表.roots()#根智能体列表
    if len(根们)==0:#尚无根
        已发布=事件()#首次发布门闩
        def 已创建(_智能体):#创建回调
            """首次发布时放行。"""
            解除()#解除监听
            已发布.set()#放行
        解除=上下文.on('agent/created',已创建)#监听创建
        已发布.wait()#等待首次发布
        根们=注册表.roots()#再取根
    if len(根们)!=1:#数量不符
        raise Error(f'fixture turn requires exactly one top-level agent, found {len(根们)}')#数量不符
    return 根们[0]#返回唯一根智能体

def 驱动夹具轮次(上下文,选项):#驱动一轮
    """从持久收件箱回执驱动一次任务直至整智能体空闲。"""
    智能体=唯一根智能体(上下文)#取得唯一根智能体
    智能体.whenIdle()#等待空闲
    消息=创建用户消息({#构造用户消息
        'content':[{'type':'text','text':选项['task']}],#任务文本
        'source':{'kind':'user'},#用户来源
    })#构造用户消息
    已接纳=[False]#是否已见到收件箱接纳
    输出=['']#助手输出（可变盒）
    用量按步={}#按 turn/step 记用量
    def 监听会话事件(会话,事件):#监听会话事件
        """转发观察者并收集输出与用量。"""
        if 会话 is not 智能体.session:#非本会话
            return#忽略
        类型=事件.get('type') if isinstance(事件,dict) else getattr(事件,'type',None)#事件类型
        数据=事件.get('data') if isinstance(事件,dict) else getattr(事件,'data',None)#事件数据
        if not 已接纳[0]:#尚未接纳
            if 类型!='agent/inbox/spliced':#非收件箱拼接
                return#忽略
            插入=数据.get('inserted') if isinstance(数据,dict) else getattr(数据,'inserted',[])#插入列表
            消息标识=消息.get('id') if isinstance(消息,dict) else getattr(消息,'id',None)#消息 id
            if not any((项.get('id') if isinstance(项,dict) else getattr(项,'id',None))==消息标识 for 项 in 插入):#尚未接纳本消息
                return#忽略
            已接纳[0]=True#标记已接纳
        观察=选项.get('onEvent')#可选观察者
        if 观察 is not None:#有观察者
            观察(智能体.session.id,事件)#转发观察者
        if 类型=='assistant/chunk':#用量分片
            分片=数据.get('chunk') if isinstance(数据,dict) else getattr(数据,'chunk',None)#分片
            分片类型=分片.get('type') if isinstance(分片,dict) else getattr(分片,'type',None)#分片类型
            if 分片类型=='usage':#用量
                回合=数据.get('turn') if isinstance(数据,dict) else getattr(数据,'turn',None)#回合
                步进=数据.get('step') if isinstance(数据,dict) else getattr(数据,'step',None)#步进
                用量=分片.get('usage') if isinstance(分片,dict) else getattr(分片,'usage',None)#用量
                用量按步[f'{回合}/{步进}']=用量#记录分片用量
        if 类型=='assistant/message':#助手消息
            文本=助手文本(事件)#提取文本
            if 文本 is not None:#有文本
                输出[0]=文本#更新输出
            用量=数据.get('usage') if isinstance(数据,dict) else getattr(数据,'usage',None)#消息带用量
            if 用量 is not None:#有用量
                回合=数据.get('turn') if isinstance(数据,dict) else getattr(数据,'turn',None)#回合
                步进=数据.get('step') if isinstance(数据,dict) else getattr(数据,'step',None)#步进
                用量按步[f'{回合}/{步进}']=用量#记录消息用量
    解除监听=上下文.on('session/event',监听会话事件)#监听会话事件
    try:#驱动轮次
        智能体.followup(消息)#投递任务
        智能体.whenIdle()#等待完成
    finally:#无论成败
        解除监听()#拆除监听
    上下文.sessions.flush(智能体.session)#刷盘会话
    用量=None#合计用量
    for 步进用量 in 用量按步.values():#逐步进
        用量=累加用量(用量,步进用量)#合计
    结果={#结果信封
        'type':'result',#结果种类
        'sessionId':智能体.session.id,#会话 id
        'output':输出[0],#助手输出
    }#结果结束
    if 用量 is not None:#可选用量
        结果['usage']=用量#写入用量
    return 结果#返回结果信封

Error=Exception#错误别名
runFixtureTurn=驱动夹具轮次#上游名
