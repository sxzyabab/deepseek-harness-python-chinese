"""一次性直接 Agent 驱动器。

组合包补丁骑在 dsh-base 上；本运行器经核心注册表创建一名 Agent，把任务驱动到静止，flush 其 Session，打印最终助手文本，然后退出。

对齐上游 `@deepseek-ai/dsh-headless`。公开面仅中文名。
"""
import os,uuid,sys#路径、uuid、标准流
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 字符串字段#配置字段
from ...内核.智能体 import 安装模型选择#模型选择安装
from ...模型后端.llm import 创建用户消息#用户消息构造
from ...内核.会话 import 会话标识#会话 id 品牌

__all__=['名称','注入','配置','应用','内部流']#仅中文公开名

名称='headless-runner'#插件名
注入=['agentDefaultModel','agents','sessions']#依赖
配置={#无头运行器配置
    'task':字符串字段(可空=False),#任务必填
}#配置结束

内部流={#可替换输出流
    'stdout':sys.stdout,#标准输出
    'stderr':sys.stderr,#标准错误
}#内部流结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步值

def 汇总(事件们,起始序号):#汇总本区间结局
    """在一段已拥有区间内汇总最后助手文本与回合结局。"""
    已开始=False#是否已见到 turn/start
    文本=''#最后助手文本
    原因=None#回合结束原因
    for 事件 in 事件们:#按事件扫描
        if 取字段(事件,'seq')<起始序号:#跳过区间前
            continue#跳过
        种类=取字段(事件,'type')#事件类型
        if 种类=='turn/start':#回合开始
            已开始=True#标记
            continue#继续
        if not 已开始:#开始前忽略
            continue#跳过
        if 种类=='assistant/message':#助手消息
            内容=取字段(取字段(取字段(事件,'data'),'message'),'content') or []#内容块
            拼=''#拼接
            for 块 in 内容:#逐块
                if 取字段(块,'type')=='text':#文本块
                    拼=拼+取字段(块,'text')#取出
            if 拼!='':#非空
                文本=拼#记下最后一段
        if 种类=='turn/end':#回合结束
            原因=取字段(取字段(事件,'data'),'reason')#原因
    return {'text':文本,'reason':原因}#结局

def 失败(出入,错误):#失败路径
    """报告意外的直接驱动失败并请求失败退出。"""
    出入['stderr'].write('dsh: '+str(错误)+'\n')#写错误
    出入['exit'](1)#请求失败退出

def 跑(上下文,任务,出入):#跑一次性任务
    """经新创建的 Agent 跑一项任务并请求进程退出。"""
    加载器=上下文.get('loader')#Loader
    if 加载器 is not None:#有 Loader
        解开(加载器.等待())#等待结算
    智能体们=上下文.get('agents')#智能体服务
    默认模型=上下文.get('agentDefaultModel')#默认模型
    会话们=上下文.get('sessions')#会话服务
    if 智能体们 is None or 默认模型 is None or 会话们 is None:#服务已拆除
        return#退出
    选择=默认模型.当前选择()#当前默认模型选择
    def 安装(智能体上下文):#子上下文安装模型选择
        """安装当前选择引用。"""
        安装模型选择(智能体上下文,{'current':选择,'assembled':None})#安装
    句柄=解开(智能体们.创建({#创建一次性智能体
        'sessionId':会话标识('session-'+str(uuid.uuid4())),#新会话 id
        'meta':{'cwd':os.getcwd()},#以进程 cwd 为会话头
        'agentOptions':{'provider':取字段(选择,'provider'),'model':取字段(选择,'model')},#默认模型
        'setup':安装,#setup
    }))#create
    智能体=取字段(句柄,'智能体')#循环驱动
    解开(智能体.等到空闲())#等到空闲
    起始=取字段(取字段(智能体,'session'),'seq')#区间起点
    智能体.后续(创建用户消息({#投入用户任务
        'content':[{'type':'text','text':任务}],#任务文本
        'source':{'kind':'user'},#用户来源
    }))#后续
    解开(智能体.等到空闲())#等到回合静止
    解开(会话们.冲洗(取字段(智能体,'session')))#flush 会话
    结局=汇总(取字段(取字段(智能体,'session'),'events'),起始)#汇总
    出入['stdout'].write(取字段(结局,'text')+'\n')#打印最终文本
    原因=取字段(结局,'reason')#结束原因
    if 取字段(原因,'kind')=='error':#错误结束
        错误体=取字段(原因,'error')#错误
        出入['stderr'].write('dsh: '+str(取字段(错误体,'code'))+': '+str(取字段(错误体,'message'))+'\n')#打印
    出入['exit'](0 if 取字段(原因,'kind')=='completed' else 1)#完成则 0 否则 1

def 应用(上下文,配置值):#安装无头运行器
    """挂载一次性直接驱动器。"""
    退出=上下文.get('appExit')#退出请求
    if 退出 is None:#启动器未提供
        raise Exception('headless-runner: the launcher must provide ctx.appExit before the tree mounts')#拒绝
    出入={'stdout':内部流['stdout'],'stderr':内部流['stderr'],'exit':退出}#组装 IO
    try:#跑任务
        跑(上下文,取字段(配置值,'task'),出入)#跑
    except Exception as 错误:#失败
        失败(出入,错误)#报告
