"""一次性直接智能体驱动。`--json` 时投影换行事件流，否则打印终局文本。"""
import os,uuid,sys#路径、uuid、标准流
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段,布尔字段#配置字段
from ...内核.智能体 import 安装模型选择#模型选择安装
from ...模型后端.llm import 创建用户消息#用户消息构造
from ...模型后端.llm.永不 import 断言永不#穷尽检查
from ...内核.会话 import 会话标识#会话 id 品牌
from ...会话检索.会话查询 import 会话查询错误#检索失败
from .运行器内部 import 内部流#进程流
from .json流 import 投影json运行,约束json行#JSON 投影

__all__=['名称','注入','配置','应用','内部流']#仅中文公开名

名称='headless-runner'#插件名
注入=['agentDefaultModel','agents','sessions']#依赖
配置={#无头运行器配置
    'task':字符串字段(),#任务可缺席，改从 stdin 读
    'sessionId':字符串字段(),#精确会话身份
    'json':布尔字段(),#机器可读流
}#配置结束

class 无头错误(Exception):
    """无头运行器失败。"""

def 汇总(会话,起始序号):
    """在一段已拥有区间内汇总最后助手文本与回合结局。"""
    已开始=False#是否已见到 turn/start
    文本=''#最后助手文本
    原因=None#回合结束原因
    长度=会话.seq#捕获长度
    for 事件 in 会话.events:#按事件扫描
        if 事件['seq']<起始序号:#跳过区间前
            continue#跳过
        if 事件['seq']>=长度:#超出捕获
            break#停
        种类=事件['type']#事件类型
        if 种类=='turn/start':#回合开始
            已开始=True#标记
            continue#继续
        if not 已开始:#开始前忽略
            continue#跳过
        if 种类=='assistant/message':#助手消息
            内容=事件['data']['message']['content'] if 'content' in 事件['data']['message'] else []#内容块
            拼=''#拼接
            for 块 in 内容:#逐块
                if 块['type']=='text':#文本块
                    拼=拼+(块['text'] if 'text' in 块 else '')#取出
            if 拼!='':#非空
                文本=拼#记下最后一段
        if 种类=='turn/end':#回合结束
            原因=事件['data']['reason']#原因
    return {'text':文本,'reason':原因}#结局

def 流式推理(上下文,智能体,标准错误):
    """把本调用的提供者推理投影到标准错误。"""
    打开=False#是否已开推理行
    以换行结束=True#行尾

    def 关闭():
        """结束未终止的推理行。"""
        nonlocal 打开,以换行结束#行态
        if not 打开:#未开
            return#空
        if not 以换行结束:#缺换行
            标准错误.write('\n')#补换行
        打开=False#关上
        以换行结束=True#复位

    def 帧处理(载荷):
        """只投影本智能体的助手流帧。"""
        nonlocal 打开,以换行结束#行态
        if 载荷['agent'] is not 智能体:#不是本智能体
            return#忽略
        帧=载荷['frame']#帧
        if 帧['type']=='start' or 帧['type']=='end':#起止
            关闭()#关行
            return#结束
        块=帧['chunk']#块
        种类=块['type']#块类型
        if 种类=='reasoning-delta':#推理增量
            if 块['text']=='':#空
                return#忽略
            if not 打开:#尚未开行
                标准错误.write('dsh: reasoning:\n')#标签
                打开=True#开
            标准错误.write(块['text'])#写出
            以换行结束=块['text'].endswith('\n')#行尾
            return#结束
        if 种类=='block-start':#块开始
            if 块['blockType']!='reasoning':#非推理
                关闭()#关
            return#结束
        if 种类=='block-end':#块结束
            if 块['block']['type']!='reasoning':#非推理
                关闭()#关
            return#结束
        if 种类=='usage':#用量
            return#忽略
        if 种类 in ('text-delta','tool-call-delta','finish'):#其他可见
            关闭()#关
            return#结束
        断言永不(块,'headless reasoning stream')#穷尽

    拆除订阅=上下文.on('agent/assistant-stream',帧处理)#订阅
    def 拆除():
        """退订并关上未终止行。"""
        拆除订阅()#退订
        关闭()#关行
    return 拆除#拆除器

def 当前预设(头,事件列表,会话标识值):
    """创建头被最后一条 agent-preset/selected 推进后的预设。"""
    预设=头['agentPreset'] if 'agentPreset' in 头 else None#头上的预设
    for 事件 in 事件列表:#逐事件
        if 事件['type']!='agent-preset/selected':#不是选择
            continue#跳过
        数据=事件['data'] if 'data' in 事件 else {}#数据
        选中=数据['agentPreset'] if 'agentPreset' in 数据 else None#选中
        if not isinstance(选中,str) or 选中=='':#畸形
            raise 无头错误('session "'+会话标识值+'" records a malformed agent-preset/selected event and cannot be adopted')#拒绝
        预设=选中#推进
    return 预设#当前

def 断言可收养(头,事件列表,会话标识值,工作目录):
    """拒绝一次性运行器不得收养的会话。"""
    预设=当前预设(头,事件列表,会话标识值)#当前预设
    if 预设 is not None:#有预设
        raise 无头错误('session "'+会话标识值+'" runs under agent preset "'+预设+'", which the one-shot runner does not compose')#拒绝
    if 头.get('origin')=='subagent' or 头.get('parentSession') is not None:#子智能体或分叉
        raise 无头错误('session "'+会话标识值+'" is a subagent or forked session and cannot be driven directly')#拒绝
    if 'cwd' not in 头 or 头['cwd'] is None:#无工作目录
        raise 无头错误('session "'+会话标识值+'" recorded no working directory, so it cannot be adopted')#拒绝
    if 头['cwd']!=工作目录:#工作目录不符
        raise 无头错误('session "'+会话标识值+'" was recorded in "'+头['cwd']+'", not "'+工作目录+'"')#拒绝

def 解析智能体(上下文,智能体服务,会话标识值,智能体选项,安装,工作目录):
    """收养已持久化会话；身份必须已存在且本进程没有活智能体。"""
    if 上下文.获取服务('sessionPersistence',False) is None:#无持久化
        raise 无头错误('headless --session-id requires the sessionPersistence service; the Session would not survive this process')#拒绝
    查询=上下文.获取服务('sessionQuery',False)#查询服务
    if 查询 is None:#无查询
        raise 无头错误('headless --session-id requires the sessionQuery service; dsh-base provides it')#拒绝
    活着=智能体服务.获取(会话标识值)#活智能体
    if 活着 is not None:#已被占用
        断言可收养(活着.session.header,活着.session.events,会话标识值,工作目录)#先点名真实不匹配
        raise 无头错误('session "'+会话标识值+'" is live in this process, so the one-shot runner cannot own an exclusive run interval')#拒绝
    try:#观察并恢复
        观测=查询.观察会话(会话标识值)#快照
        断言可收养(观测.header,观测.events,会话标识值,工作目录)#可收养
        句柄=智能体服务.恢复({'resumeSessionId':会话标识值,'agentOptions':智能体选项,'setup':安装})#恢复
        智能体=句柄.智能体#循环驱动
        断言可收养(智能体.session.header,智能体.session.events,会话标识值,工作目录)#再检
        return 智能体#恢复的智能体
    except 会话查询错误 as 错误:#检索失败
        if getattr(错误,'code',None)!='SESSION_QUERY_SESSION_NOT_FOUND':#其他失败
            raise#原样
        raise 无头错误('session "'+会话标识值+'" does not exist; omit --session-id to start a new Session')#拒绝

def 失败(出入,错误,json模式):
    """报告意外的直接驱动失败并请求失败退出。"""
    消息=错误.args[0] if isinstance(错误,Exception) and len(错误.args)>0 else str(错误)#消息
    if json模式:#JSON 契约
        出入['stdout'].write(约束json行({'type':'error','message':消息})+'\n')#事件
    出入['stderr'].write('dsh: '+str(消息)+'\n')#诊断
    出入['exit'](1)#请求失败退出

def 执行任务(上下文,配置值,出入):
    """经一只智能体执行一项任务并请求进程退出。"""
    加载器=上下文.获取服务('loader')#Loader
    if 加载器 is not None:#有 Loader
        加载器.等待()#等待结算
    智能体服务=上下文.获取服务('agents')#智能体服务
    默认模型=上下文.获取服务('agentDefaultModel')#默认模型
    会话服务=上下文.获取服务('sessions')#会话服务
    if 智能体服务 is None or 默认模型 is None or 会话服务 is None:#服务已拆除
        return#退出
    会话标识原文=配置值['sessionId'] if 'sessionId' in 配置值 else None#可选身份
    if 会话标识原文 is not None and 会话标识原文.strip()=='':#空白
        raise 无头错误('headless-runner: sessionId must not be blank')#拒绝
    任务原文=配置值['task'] if 'task' in 配置值 else None#任务
    if 任务原文 is None or 任务原文=='-':#从 stdin
        任务=内部流['readStdin']()#读完
    else:#字面任务
        任务=任务原文#原样
    if 任务.strip()=='':#空任务
        raise 无头错误('a task is required, for example: dsh --profile headless "run the tests"')#拒绝
    选择=默认模型.当前选择()#当前默认模型选择
    def 安装(智能体上下文):
        """安装当前选择引用。"""
        安装模型选择(智能体上下文,{'current':选择,'assembled':None})#安装
    智能体选项={'provider':选择['provider'],'model':选择['model']}#模型
    标识=会话标识(会话标识原文 if 会话标识原文 is not None else 'session-'+str(uuid.uuid4()))#会话 id
    文件系统=上下文.获取服务('fs',False)#文件系统
    工作目录=os.getcwd() if 文件系统 is None else 文件系统.进程路径(文件系统.解析('.'))#工作目录
    if 会话标识原文 is None:#新会话
        句柄=智能体服务.创建({#创建一次性智能体
            'sessionId':标识,#新会话 id
            'meta':{'cwd':工作目录},#会话头
            'agentOptions':智能体选项,#默认模型
            'setup':安装,#setup
        })#create
        智能体=句柄.智能体#循环驱动
    else:#收养
        智能体=解析智能体(上下文,智能体服务,标识,智能体选项,安装,工作目录)#恢复
    智能体.等到空闲()#等到空闲
    if 会话标识原文 is not None:#收养后再检
        断言可收养(智能体.session.header,智能体.session.events,标识,工作目录)#再读日志
    起始=智能体.session.seq#区间起点
    json模式=配置值['json'] is True if 'json' in 配置值 else False#输出模式
    投影=投影json运行(上下文,智能体,出入['stdout'],{'cwd':工作目录}) if json模式 else None#JSON 投影
    停推理=None if 投影 is not None else 流式推理(上下文,智能体,出入['stderr'])#推理流
    try:#驱动
        try:#投入任务
            智能体.后续(创建用户消息({#投入用户任务
                'content':[{'type':'text','text':任务}],#任务文本
                'source':{'kind':'user'},#用户来源
            }))#后续
            智能体.等到空闲()#等到回合静止
        finally:#停推理
            if 停推理 is not None:#有推理流
                停推理()#拆除
        会话服务.冲洗(智能体.session)#flush 会话
        结局=汇总(智能体.session,起始)#汇总
        if 投影 is None:#默认模式
            出入['stdout'].write(结局['text']+'\n')#打印最终文本
        else:#JSON
            投影['finish'](结局['text'])#终局
        原因=结局['reason']#结束原因
        if 原因 is not None and 原因['kind']=='error':#错误结束
            错误体=原因['error']#错误
            出入['stderr'].write('dsh: '+str(错误体['code'])+': '+str(错误体['message'])+'\n')#打印
        出入['exit'](0 if 原因 is not None and 原因['kind']=='completed' else 1)#完成则 0 否则 1
    finally:#拆投影
        if 投影 is not None:#有投影
            投影['dispose']()#拆除

def 应用(上下文,配置值):
    """挂载一次性直接驱动器。"""
    退出=上下文.获取服务('appExit')#退出请求
    if 退出 is None:#启动器未提供
        raise 无头错误('headless-runner: the launcher must provide ctx.appExit before the tree mounts')#拒绝
    出入={'stdout':内部流['stdout'],'stderr':内部流['stderr'],'exit':退出}#组装 IO
    json模式=配置值['json'] is True if 'json' in 配置值 else False#输出模式
    try:#执行任务
        执行任务(上下文,配置值,出入)#执行
    except Exception as 错误:#任务与智能体循环可抛任意类型
        失败(出入,错误,json模式)#报告

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
Config=配置#框架槽
