"""用 git 工作树快照与文件工具整文件捕获汇总每轮变更，以 workspace/changes 宣告，经 workspaceChanges 提供摘要与对比。

公开业务面仅中文名。包名、服务名、事件名与配置键保持英文线协议。
"""
import os,sys,tempfile#平台、家目录与临时根
from ...依赖.schemastery import 数字字段#配置字段
from ...工具.超时 import 中止控制器#插件寿命
from .记录器 import 轮次记录器#每会话记录器
from .版本库 import git运行器#git命令运行器
from .类型 import (#再导出类型面
    工作区变更文件字段,
    工作区变更摘要字段,
    差异块字段,
    工作区文件差异字段,
    工作区变更服务字段,
)#类型字段

__all__=[#仅中文公开名
    '名称','注入','配置','应用','默认','工作区变更错误',
    '工作区变更文件字段','工作区变更摘要字段','差异块字段','工作区文件差异字段','工作区变更服务字段',
]#公开面结束

名称='workspace-changes'#Cordis插件名（字面量）
注入=['subprocess']#依赖子进程能力
配置={#部署配置
    'timeoutMs':数字字段(默认值=30000),#单条git超时毫秒
    'outputMaxBytes':数字字段(默认值=8*1024*1024),#git输出帽
    'maxFiles':数字字段(默认值=500),#摘要最大文件数
    'maxFileBytes':数字字段(默认值=2*1024*1024),#捕获/对比字节帽
    'diffTimeoutMs':数字字段(默认值=100),#逐行对比超时毫秒
}#配置模式结束

class 工作区变更错误(Exception):#本包异常基类
    """工作区变更插件入参或运行失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 可记录(会话):#顶层有cwd的会话
    """子代理或委托会话不记录；否则返回工作目录，无则 None。"""
    头=会话.header#会话头
    来源=头['origin'] if 'origin' in 头 else None#来源
    委托=头['delegationDepth'] if 'delegationDepth' in 头 else 0#委托深度
    if 委托 is None:#缺省0
        委托=0#零
    if 来源=='subagent' or 委托>0:#非顶层
        return None#不记
    return 头['cwd'] if 'cwd' in 头 else None#工作目录

def 解析git(上下文,信号):#解析git可执行
    """解析 git 可执行；macOS 上 /usr/bin/git 桩在未选开发者工具时视为不可用。"""
    try:#查找
        可执行=上下文.subprocess.解析可执行文件('git',None,信号)#解析
    except Exception:#找不到
        return None#不可用
    if sys.platform!='darwin' or 可执行!='/usr/bin/git':#非Xcode桩
        return 可执行#可用
    句柄=上下文.subprocess.启动({#探测xcode-select
        'argv':['/usr/bin/xcode-select','-p'],#探测
        'cwd':os.path.expanduser('~'),#家目录
        'stdio':{'stdin':'ignore','stdout':{'maxBytes':4096},'stderr':{'maxBytes':4096}},#有界
        'graceMs':1000,#宽限
        'signal':信号,#取消
    })#启动
    try:#等结局
        结局=句柄.等待结局()#同步
    except Exception:#失败当不可用
        return None#无
    return 可执行 if 结局['exitCode']==0 else None#选中工具才可用

def 应用(上下文,配置值):#登记服务并观察轮次
    """观察顶层轮次、捕获文件工具编辑、宣告摘要，并提供 workspaceChanges。"""
    for 字段,值 in [#逐字段校验
        ('timeoutMs',配置值['timeoutMs']),
        ('outputMaxBytes',配置值['outputMaxBytes']),
        ('maxFiles',配置值['maxFiles']),
        ('maxFileBytes',配置值['maxFileBytes']),
        ('diffTimeoutMs',配置值['diffTimeoutMs']),
    ]:#字段表
        if isinstance(值,bool) or not isinstance(值,int) or 值<1:#须正整数
            raise 工作区变更错误('workspace-changes requires a positive integer '+字段)#加载失败
    寿命=中止控制器()#插件寿命
    记录器表={}#Session -> 记录器
    按号表={}#SessionId -> 记录器
    运行器箱=[None]#惰性git运行器
    已解析=[False]#是否已解析git

    def 遗忘(会话):#释放一会话记录器
        """摘掉并释放该会话的记录器。"""
        记录器=记录器表.pop(会话,None)#取出
        if 会话.id in 按号表:#有号
            del 按号表[会话.id]#摘号
        if 记录器 is not None:#有实例
            记录器.释放()#释放

    def 拆除体():#插件拆除
        """中止寿命并释放全部记录器。"""
        def 拆除():#实际拆除
            """跑遗忘。"""
            寿命.中止()#中止
            for 会话 in list(记录器表.keys()):#逐会话
                遗忘(会话)#释放
        return 拆除#拆除器
    上下文.副作用(拆除体,'workspace-changes')#挂effect

    def 取摘要(会话号,序号):#服务.summary
        """按会话号与事件序号取摘要。"""
        记录器=按号表[会话号] if 会话号 in 按号表 else None#查找
        return None if 记录器 is None else 记录器.摘要(序号)#摘要

    def 取差异(会话号,序号,下标,信号):#服务.diff
        """按需对比所列文件。"""
        记录器=按号表[会话号] if 会话号 in 按号表 else None#查找
        return None if 记录器 is None else 记录器.差异(序号,下标,信号)#差异

    class 工作区变更服务:#Host服务面
        """workspaceChanges 服务：摘要与按需差异。"""
        def 摘要(自身,会话号,序号):#取摘要
            """取摘要。"""
            return 取摘要(会话号,序号)#委托
        def 差异(自身,会话号,序号,下标,信号):#取差异
            """取差异。"""
            return 取差异(会话号,序号,下标,信号)#委托

    上下文.提供服务('workspaceChanges',工作区变更服务())#登记服务

    def 取git运行器():#惰性解析
        """首次调用时解析 git 并构造运行器。"""
        if not 已解析[0]:#尚未
            已解析[0]=True#钉住
            可执行=解析git(上下文,寿命.信号)#解析
            if 可执行 is None:#不可用
                上下文.日志.信息('workspace-changes: git is unavailable; only file-tool edits are summarized')#信息
                运行器箱[0]=None#无
            else:#可用
                运行器箱[0]=git运行器(上下文.subprocess,可执行,{'timeoutMs':配置值['timeoutMs'],'outputMaxBytes':配置值['outputMaxBytes']})#构造
        return 运行器箱[0]#运行器或None

    def 警告(消息):#转日志
        """把记录器警告转到上下文日志。"""
        上下文.日志.警告(消息)#警告

    def 记录器自(会话,工作目录):#取或建记录器
        """为会话取得轮次记录器。"""
        记录器=记录器表[会话] if 会话 in 记录器表 else None#已有
        if 记录器 is None:#新建
            记录器=轮次记录器(会话,工作目录,{#环境
                'git':取git运行器(),#同步已解析或None
                'tempRoot':tempfile.gettempdir(),#临时根
                'maxFiles':配置值['maxFiles'],#文件帽
                'maxFileBytes':配置值['maxFileBytes'],#字节帽
                'diffTimeoutMs':配置值['diffTimeoutMs'],#对比超时
                'warn':警告,#警告回调
            })#构造结束
            记录器表[会话]=记录器#按对象
            按号表[会话.id]=记录器#按号
        return 记录器#实例

    def 会话事件(会话,事件):#session/event
        """观察 turn/start、tool/result、turn/end。"""
        if 事件['type']=='turn/start':#开轮
            工作目录=可记录(会话)#是否记录
            if 工作目录 is not None:#顶层有cwd
                记录器自(会话,工作目录).开始(事件['data']['turn'])#拍基线
            return
        if 事件['type']=='tool/result':#工具结果
            if 会话 in 记录器表:#有记录器
                记录器表[会话].观察(事件)#记序号
        elif 事件['type']=='turn/end':#关轮
            if 会话 in 记录器表:#有记录器
                记录器表[会话].结束(事件['data']['turn'])#可能再记

    def 会话已拆除(会话):#session/disposed
        """会话释放时遗忘记录器。"""
        遗忘(会话)#释放

    def 轮次将停(载荷):#agent/turn-stopping
        """轮内提交记录。"""
        智能体=载荷['agent']#智能体
        会话=智能体.session#会话
        if 会话 in 记录器表:#有记录器
            记录器表[会话].停止中(载荷['turn'])#记录

    def 工具前执行(执行,下一步):#tools/pre-execute
        """变更前捕获并等到记录队列空。"""
        智能体=执行['agent'] if 'agent' in 执行 else None#智能体
        会话=智能体.session if 智能体 is not None else None#会话
        记录器=记录器表[会话] if 会话 is not None and 会话 in 记录器表 else None#记录器
        if 记录器 is not None:#有
            记录器.捕获(执行['name'],执行['arguments'])#捕获
            记录器.已结算()#等到空
        return 下一步()#继续瀑布

    上下文.监听('session/event',会话事件)#轮次与工具结果
    上下文.监听('session/disposed',会话已拆除)#拆除
    上下文.监听('agent/turn-stopping',轮次将停)#轮内记录
    上下文.监听('tools/pre-execute',工具前执行)#捕获

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
默认=应用
default=应用#框架槽
