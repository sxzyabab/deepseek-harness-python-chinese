"""一次性直接智能体驱动。`--json` 时投影换行事件流，否则打印终局文本。"""
import os,uuid
from ...依赖 import cordis
from ...依赖.schemastery import 字符串字段,布尔字段
from ...内核.智能体 import 安装模型选择
from ...模型后端.llm import 创建用户消息
from ...模型后端.llm.永不 import 断言永不
from ...内核.会话 import 会话标识
from ...会话检索.会话查询 import 会话查询错误
from .运行器内部 import 内部流
from .json流 import 投影json运行,约束json行

__all__=['名称','依赖','配置','应用','内部流']

名称='headless-runner'
依赖=['agentDefaultModel','agents','sessions']
配置={
    'task':字符串字段(),
    'sessionId':字符串字段(),
    'json':布尔字段(),
}

class 无头错误(Exception):
    """无头运行器失败。"""

def 汇总(会话,起始序号):
    """在一段已拥有区间内汇总最后助手文本与回合结局。"""
    已开始=False
    文本=''
    原因=None
    长度=会话.seq
    for 事件 in 会话.events:
        if 事件['seq']<起始序号:
            continue
        if 事件['seq']>=长度:
            break
        种类=事件['type']
        if 种类=='turn/start':
            已开始=True
            continue
        if not 已开始:
            continue
        if 种类=='assistant/message':
            内容=事件['data']['message']['content'] if 'content' in 事件['data']['message'] else []
            拼=''
            for 块 in 内容:
                if 块['type']=='text':
                    拼=拼+(块['text'] if 'text' in 块 else '')
            if 拼!='':
                文本=拼
        if 种类=='turn/end':
            原因=事件['data']['reason']
    return {'text':文本,'reason':原因}

def 流式推理(上下文,智能体,标准错误):
    """把本调用的提供者推理投影到标准错误。"""
    打开=False
    以换行结束=True

    def 关闭():
        """结束未终止的推理行。"""
        nonlocal 打开,以换行结束
        if not 打开:
            return
        if not 以换行结束:
            标准错误.write('\n')
        打开=False
        以换行结束=True

    def 帧处理(载荷):
        """只投影本智能体的助手流帧。"""
        nonlocal 打开,以换行结束
        if 载荷['agent'] is not 智能体:
            return
        帧=载荷['frame']
        if 帧['type']=='start' or 帧['type']=='end':
            关闭()
            return
        块=帧['chunk']
        种类=块['type']
        if 种类=='reasoning-delta':
            if 块['text']=='':
                return
            if not 打开:
                标准错误.write('dsh: 推理:\n')
                打开=True
            标准错误.write(块['text'])
            以换行结束=块['text'].endswith('\n')
            return
        if 种类=='block-start':
            if 块['blockType']!='reasoning':
                关闭()
            return
        if 种类=='block-end':
            if 块['block']['type']!='reasoning':
                关闭()
            return
        if 种类=='usage':
            return
        if 种类 in ('text-delta','tool-call-delta','finish'):
            关闭()
            return
        断言永不(块,'headless reasoning stream')

    拆除订阅=上下文.on('agent/assistant-stream',帧处理)
    def 拆除():
        """退订并关上未终止行。"""
        拆除订阅()
        关闭()
    return 拆除

def 当前预设(头,事件列表,会话标识值):
    """创建头被最后一条 agent-preset/selected 推进后的预设。"""
    预设=头['agentPreset'] if 'agentPreset' in 头 else None
    for 事件 in 事件列表:
        if 事件['type']!='agent-preset/selected':
            continue
        数据=事件['data'] if 'data' in 事件 else {}
        选中=数据['agentPreset'] if 'agentPreset' in 数据 else None
        if not isinstance(选中,str) or 选中=='':
            raise 无头错误('会话 "'+会话标识值+'" 记录了畸形的 agent-preset/selected 事件，无法收养')
        预设=选中
    return 预设

def 断言可收养(头,事件列表,会话标识值,工作目录):
    """拒绝一次性运行器不得收养的会话。"""
    预设=当前预设(头,事件列表,会话标识值)
    if 预设 is not None:
        raise 无头错误('会话 "'+会话标识值+'" 运行在智能体预设 "'+预设+'" 下，一次性运行器不组合该预设')
    if 头.get('origin')=='subagent' or 头.get('parentSession') is not None:
        raise 无头错误('会话 "'+会话标识值+'" 是子智能体或分叉会话，不能直接驱动')
    if 'cwd' not in 头 or 头['cwd'] is None:
        raise 无头错误('会话 "'+会话标识值+'" 没有记录工作目录，无法收养')
    if 头['cwd']!=工作目录:
        raise 无头错误('会话 "'+会话标识值+'" 记录的工作目录与当前进程工作目录不一致')

def 解析智能体(上下文,智能体服务,会话标识值,智能体选项,安装,工作目录):
    """收养已持久化会话；身份必须已存在且本进程没有活智能体。"""
    if 上下文.获取服务('sessionPersistence',False) is None:
        raise 无头错误('无头 --session-id 需要 sessionPersistence 服务；会话无法在本进程存活')
    查询=上下文.获取服务('sessionQuery',False)
    if 查询 is None:
        raise 无头错误('无头 --session-id 需要 sessionQuery 服务；dsh-base 提供该服务')
    活着=智能体服务.获取(会话标识值)
    if 活着 is not None:
        断言可收养(活着.session.header,活着.session.events,会话标识值,工作目录)
        raise 无头错误('会话 "'+会话标识值+'" 已在本进程活着，一次性运行器不能独占运行区间')
    try:
        观测=查询.观察会话(会话标识值)
        断言可收养(观测.header,观测.events,会话标识值,工作目录)
        句柄=智能体服务.恢复({'resumeSessionId':会话标识值,'agentOptions':智能体选项,'setup':安装})
        智能体=句柄.智能体
        断言可收养(智能体.session.header,智能体.session.events,会话标识值,工作目录)
        return 智能体
    except 会话查询错误 as 错误:
        if getattr(错误,'code',None)!='SESSION_QUERY_SESSION_NOT_FOUND':
            raise
        raise 无头错误('会话 "'+会话标识值+'" 不存在；省略 --session-id 以开始新会话')

def 失败(出入,错误,json模式):
    """报告意外的直接驱动失败并请求失败退出。"""
    消息=错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)
    if json模式:
        出入['stdout'].write(约束json行({'type':'error','message':消息})+'\n')
    出入['stderr'].write('dsh: '+str(消息)+'\n')
    出入['exit'](1)

def 执行任务(上下文,配置值,出入):
    """经一只智能体执行一项任务并请求进程退出。"""
    加载器=上下文.获取服务('loader')
    if 加载器 is not None:
        加载器.等待()
    智能体服务=上下文.获取服务('agents')
    默认模型=上下文.获取服务('agentDefaultModel')
    会话服务=上下文.获取服务('sessions')
    if 智能体服务 is None or 默认模型 is None or 会话服务 is None:
        return
    会话标识原文=配置值['sessionId'] if 'sessionId' in 配置值 else None
    if 会话标识原文 is not None and 会话标识原文.strip()=='':
        raise 无头错误('headless-runner: sessionId 不能为空白')
    任务原文=配置值['task'] if 'task' in 配置值 else None
    if 任务原文 is None or 任务原文=='-':
        任务=内部流['readStdin']()
    else:
        任务=任务原文
    if 任务.strip()=='':
        raise 无头错误('必须提供任务，例如：dsh --profile headless "run the tests"')
    选择=默认模型.当前选择()
    def 安装(智能体上下文):
        """安装当前选择引用。"""
        安装模型选择(智能体上下文,{'current':选择,'assembled':None})
    智能体选项={'provider':选择['provider'],'model':选择['model']}
    标识=会话标识(会话标识原文 if 会话标识原文 is not None else 'session-'+str(uuid.uuid4()))
    文件系统=上下文.获取服务('fs',False)
    工作目录=os.getcwd() if 文件系统 is None else 文件系统.进程路径(文件系统.解析('.'))
    if 会话标识原文 is None:
        句柄=智能体服务.创建({
            'sessionId':标识,
            'meta':{'cwd':工作目录},
            'agentOptions':智能体选项,
            'setup':安装,
        })
        智能体=句柄.智能体
    else:
        智能体=解析智能体(上下文,智能体服务,标识,智能体选项,安装,工作目录)
    智能体.等到空闲()
    if 会话标识原文 is not None:
        断言可收养(智能体.session.header,智能体.session.events,标识,工作目录)
    起始=智能体.session.seq
    json模式=配置值['json'] is True if 'json' in 配置值 else False
    投影=投影json运行(上下文,智能体,出入['stdout'],{'cwd':工作目录}) if json模式 else None
    停推理=None if 投影 is not None else 流式推理(上下文,智能体,出入['stderr'])
    try:
        try:
            智能体.后续(创建用户消息({
                'content':[{'type':'text','text':任务}],
                'source':{'kind':'user'},
            }))
            智能体.等到空闲()
        finally:
            if 停推理 is not None:
                停推理()
        会话服务.冲洗(智能体.session)
        结局=汇总(智能体.session,起始)
        if 投影 is None:
            出入['stdout'].write(结局['text']+'\n')
        else:
            投影['finish'](结局['text'])
        原因=结局['reason']
        if 原因 is not None and 原因['kind']=='error':
            错误体=原因['error']
            出入['stderr'].write('dsh: '+str(错误体['code'])+': '+str(错误体['message'])+'\n')
        出入['exit'](0 if 原因 is not None and 原因['kind']=='completed' else 1)
    finally:
        if 投影 is not None:
            投影['dispose']()

def 应用(上下文,配置值):
    """挂载一次性直接驱动器。"""
    退出=上下文.获取服务('appExit')
    if 退出 is None:
        raise 无头错误('headless-runner: 启动器必须在插件树挂载前提供 ctx.appExit')
    出入={'stdout':内部流['stdout'],'stderr':内部流['stderr'],'exit':退出}
    json模式=配置值['json'] is True if 'json' in 配置值 else False
    try:
        执行任务(上下文,配置值,出入)
    except Exception as 错误:
        失败(出入,错误,json模式)

name=名称
inject=依赖
apply=应用
Config=配置
