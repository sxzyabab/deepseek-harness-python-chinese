import json,re#JSON 与 @pluginId 正则
from ...内核.工具 import 定义工具#工具定义工厂
from ...模型后端.llm import 创建用户消息#用户消息工厂
from ..cordis服务端 import 动态插件标识,动态包标识#标识构造
from .提示 import cordis系统提示#系统提示词
from .呈现 import (#展示函数
    呈现定义调用,呈现巡检列表调用,呈现巡检查询调用,呈现自检调用,
    呈现运行调用,呈现停止调用,呈现移除调用,
)#展示
from .提供方 import 列出宿主巡检提供方#宿主巡检提供方
from .巡检 import 缺失服务,已提供服务#缺失/已提供服务

__all__=['名称','注入','应用','工具错误']#仅中文公开名

名称='tool-cordis'#插件名
注入=['tools','systemPrompt','dynamicCordisRunner','cordisInspect']#硬依赖服务

引用模式=re.compile(r'(?:^|\s)@([a-z]{3,6}-\d+)(?=\s|$)')#空白包围的 @前缀-数字

class 工具错误(Exception):
    """Cordis 面向模型工具失败。"""
    pass#消息在构造时传入

def 要求智能体(执行):
    """工具执行必须带 Agent。执行为 dict。"""
    智能体=执行['agent'] if 'agent' in 执行 else None#调用方 Agent
    if 智能体 is None:#无会话
        raise 工具错误('Cordis 动态工具需要有 Agent 支撑的会话')#失败
    return 智能体#返回

def 要求json对象(值):
    """非普通对象则失败。"""
    if not isinstance(值,dict):#非普通对象
        raise 工具错误('需要 JSON 对象')#失败
    return 值#对象本身

def 要求json字符串(值,键):
    """非字符串则失败。值为 dict。"""
    if 键 not in 值:#缺键
        raise 工具错误('需要 JSON 字符串字段 "'+键+'"')#失败
    字段=值[键]#取出字段
    if not isinstance(字段,str):#非字符串
        raise 工具错误('需要 JSON 字符串字段 "'+键+'"')#失败
    return 字段#字符串值

def 自检状态(引用):
    """自检状态。引用为快照 dict。"""
    最近=引用['latestRun'] if 'latestRun' in 引用 else None#最近运行
    状态=None if 最近 is None else 最近['status']#最近运行状态
    if 状态=='awaiting-approval':#等审批
        return 'awaiting-approval'#等审批
    if 状态 in ('client-pending','starting-host'):#客户端未就绪
        return 'client-pending'#客户端未就绪
    if 状态 in ('failed','rejected','cancelled'):#失败类
        return 'failed'#失败
    if 状态=='waiting':#在等依赖
        return 'waiting'#等待
    if 状态=='running':#在跑
        return 'running'#在跑
    if 'activeRun' in 引用:#有活动运行
        return 'running'#在跑
    return 'defined' if 'currentPackageId' not in 引用 else 'stopped'#仅定义或已停

def 自检摘要(引用):
    """摘要对象。引用为快照 dict。"""
    最近=引用['latestRun'] if 'latestRun' in 引用 else None#最近一次运行
    摘要={#摘要
        'pluginId':str(引用['pluginId']),#插件 id
        'name':引用['name'],#名称
        'packageCount':(1 if 'packages' not in 引用 else len(引用['packages'])),#包数量；缺席按 1
        'state':自检状态(引用),#状态
    }#摘要
    if 'currentPackageId' in 引用:#有当前
        摘要['currentPackageId']=str(引用['currentPackageId'])#带上
    if 'nextPackageId' in 引用:#有 next
        摘要['nextPackageId']=str(引用['nextPackageId'])#带上
    活动=引用['activeRun'] if 'activeRun' in 引用 else None#活动运行
    if 活动 is not None:#有活动运行
        摘要['activeRun']={'pluginRunId':str(活动['pluginRunId']),'packageId':str(活动['packageId'])}#活动
    if 最近 is not None and 最近['status']=='awaiting-approval':#仅审批中
        摘要['pendingApproval']={'pluginRunId':str(最近['pluginRunId']),'packageId':str(最近['packageId']),'mode':最近['mode']}#待审批
    return 摘要#摘要

def 自检包(上下文,智能体,插件标识,包标识):
    """返回包详情。巡检包与快照行为 dict。"""
    已检=上下文.dynamicCordisRunner.巡检包(智能体,插件标识,包标识)#读包
    行=None#插件快照行
    for 候选 in 上下文.dynamicCordisRunner.快照(智能体):#查找
        if 候选['pluginId']==插件标识:#命中
            行=候选#记下
            break#结束
    包元=None#该包元数据
    if 行 is not None:#有行
        for 候选 in 行['packages']:#查找
            if 候选['packageId']==包标识:#命中
                包元=候选#记下
                break#结束
    活动=None#该包是否正在跑
    if 行 is not None and 'activeRun' in 行 and 行['activeRun']['packageId']==包标识:#正在跑
        活动=行['activeRun']#活动
    最近=None#该包最近运行
    if 'latestRun' in 已检 and 已检['latestRun']['packageId']==包标识:#该包最近
        最近=已检['latestRun']#记下
    if 活动 is not None and 'fiber' in 活动:#有 Fiber
        宿主等待=缺失服务(上下文,活动['fiber'])#宿主等待项
    elif 最近 is not None:#从最近取
        宿主等待=list(最近['host']['waitingFor'])#从最近取
    else:#无
        宿主等待=[]#空
    if 包元 is None or not 包元['hasHostHalf']:#无宿主半
        宿主状态='absent'#缺席
    elif 最近 is not None:#有最近
        宿主状态=最近['host']['status']#最近状态
    elif 活动 is None:#无活动
        宿主状态='stopped'#已停
    else:#按等待
        宿主状态='running' if len(宿主等待)==0 else 'waiting'#运行或等待
    if 包元 is None or not 包元['hasClientHalf']:#无客户端半
        客户端状态='absent'#缺席
    elif 最近 is not None:#有最近
        客户端状态=最近['client']['status']#最近
    else:#否则已停
        客户端状态='stopped'#已停
    宿主={#宿主半
        'status':宿主状态,#状态
        'provides':[] if 活动 is None or 'fiber' not in 活动 else 已提供服务(上下文,活动['fiber']),#提供的服务
        'waitingFor':宿主等待,#等待项
        'handlers':[] if 活动 is None or 'handlers' not in 活动 else 活动['handlers'],#宿主方法
    }#宿主
    if 最近 is not None and 'error' in 最近['host']:#有错误
        宿主['error']=最近['host']['error']#带上
    客户端={#客户端半
        'status':客户端状态,#状态
        'waitingFor':[] if 最近 is None else list(最近['client']['waitingFor']),#等待项
    }#客户端
    if 最近 is not None and 'error' in 最近['client']:#有错误
        客户端['error']=最近['client']['error']#带上
    if 活动 is not None and 'renderFailure' in 活动:#有渲染失败
        客户端['renderFailure']=活动['renderFailure']#带上
    return {#包详情
        'mode':'package',#模式
        'plugin':自检摘要(已检),#所属插件摘要
        'packageId':str(包标识),#包 id
        'name':已检['name'],#包名
        'purpose':已检['purpose'],#用途
        'code':已检['code'],#源码两半
        'runtime':{'state':自检状态(已检),'host':宿主,'client':客户端},#运行时
    }#详情

def 收集引用插件标识(消息列表):
    """去重后的 id。消息为 dict。"""
    已见=set()#去重
    for 消息 in 消息列表:#每条消息
        if 'source' not in 消息:#无来源
            continue#跳过
        来源=消息['source']#来源
        if 来源['kind']!='user':#只看用户来源
            continue#跳过
        文本块=[]#文本
        内容=消息['content'] if 'content' in 消息 else []#内容块
        for 块 in 内容:#内容块
            if 块['type']=='text':#文本块
                文本块.append(块['text'] if 'text' in 块 else '')#收入
        文本='\n'.join(文本块)#拼文本
        for 匹配 in 引用模式.finditer(文本):#逐个匹配
            已见.add(匹配.group(1))#收入捕获组
    return list(已见)#去重后的 id

def 渲染引用(引用):
    """上下文块。引用为 dict。"""
    模式='run' if 'currentPackageId' not in 引用 else 'update'#无当前则首次 run
    return '\n'.join([#上下文块
        '<cordis_dynamic_plugin_context>',#开始标记
        json.dumps(引用,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2),#引用 JSON
        '',#空行
        'The user explicitly referenced @'+引用['pluginId']+'. Use Package '+引用['packageId']+' as the base for this modification.',#点名
        'Before modifying it, call cordis_inspect_self with pluginId="'+引用['pluginId']+'" and packageId="'+引用['packageId']+'" to read the exact metadata and source.',#先自检
        'Use cordis_define with plugin.kind="existing" and the original pluginId="'+引用['pluginId']+'" to append an immutable Package.',#追加
        'Do not create a new Plugin for this request. After cordis_define succeeds, call cordis_run mode="'+模式+'" with the returned packageId.',#不要另起
        '</cordis_dynamic_plugin_context>',#结束
    ])#拼成一段

def 渲染不可用引用(标识):
    """上下文块。"""
    return '\n'.join([#上下文块
        '<cordis_dynamic_plugin_context>',#开始
        'The user explicitly referenced @'+标识+', but this Plugin is unavailable in the current Session.',#当前会话没有
        'It may have been removed, belong to another Session, or have been lost when the DSH process restarted.',#可能原因
        'Do not claim that it was updated or silently create a replacement Plugin. Tell the user that the reference is currently unavailable.',#不要偷换
        '</cordis_dynamic_plugin_context>',#结束
    ])#拼成一段

def 列表渲染(参数,值):
    """缩进 JSON 文本。"""
    return [{'type':'text','text':json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False,indent=2)}]#文本块

def 定义元数据(参数,值):
    """定义工具展示元数据。值为回执 dict。"""
    return {'pluginId':值['pluginId'],'packageId':值['packageId']}#展示元数据

def 运行元数据(参数,值):
    """运行工具展示元数据。值为回执 dict。"""
    结果=要求json对象(值)#必须是对象
    return {'pluginId':要求json字符串(结果,'pluginId'),'packageId':要求json字符串(结果,'packageId'),'pluginRunId':要求json字符串(结果,'pluginRunId')}#元数据

def 停止渲染(参数,值):
    """停止回执文本。"""
    return [{'type':'text','text':'Dynamic Plugin '+值['pluginId']+' is stopped; its definition and versions remain.'}]#文本

def 移除渲染(参数,值):
    """移除回执文本。"""
    return [{'type':'text','text':'Removed dynamic Plugin '+值['pluginId']+' and all of its Packages.'}]#文本

def 应用(上下文):
    """登记 Cordis 工具，并显式注入 @pluginId 上下文。"""
    上下文.systemPrompt.段落({'name':'tool:cordis','order':115,'text':cordis系统提示})#挂上系统提示词段

    def 登记一项(项):
        """闭包：按 Fiber 登记一个巡检提供方。"""
        def 登记():
            """副作用体。"""
            上下文.cordisInspect.登记(项)#登记
        return 登记#副作用

    for 提供方 in 列出宿主巡检提供方(上下文):#每个宿主巡检提供方
        上下文.副作用(登记一项(提供方),'tool-cordis: inspect '+提供方['manifest']['id'])#按 Fiber 登记

    def 列表执行(参数,执行):
        """列出全部巡检提供方。"""
        return {'providers':上下文.cordisInspect.列出()}#列出全部提供方

    上下文.tools.登记(定义工具({#登记巡检列表工具
        'name':'cordis_inspect_list',#工具名
        'description':(#工具说明
            'List every Cordis Inspect Provider currently known to the Host, including local Host Providers and the latest '
            +'manifests synchronized from the Client. Each entry includes its platform, purpose, read-only methods, and '
            +'input/output schemas. Call this Tool before creating or modifying a Package, then select the provider and '
            +'method for cordis_inspect_query from its result. Do not guess names or treat an Inspect method as a business '
            +'Service that Plugin code can call.'
        ),#说明
        'parameters':{},#无参数
        'output':{'schema':{'type':'json'},'render':列表渲染},#输出
        'execute':列表执行,#列出全部提供方
        'presentCall':呈现巡检列表调用,#调用展示
    }))#列表工具结束

    def 查询执行(参数,执行):
        """委托巡检服务。参数与执行为 dict。"""
        输入=参数['input'] if 'input' in 参数 else None#可选输入
        信号=执行['signal'] if 'signal' in 执行 else None#可选中止
        数据=上下文.cordisInspect.查询(参数['platform'],参数['provider'],参数['method'],输入,要求智能体(执行),信号)#查询
        return {'platform':参数['platform'],'provider':参数['provider'],'method':参数['method'],'data':数据}#回显

    上下文.tools.登记(定义工具({#登记巡检查询工具
        'name':'cordis_inspect_query',#工具名
        'description':(#工具说明
            'Run a read-only query explicitly declared by an Inspect Provider. platform, provider, and method must come '
            +'from cordis_inspect_list, and input must satisfy that method\'s schema. Use this Tool before cordis_define '
            +'to read exact Service methods, Event modes, Builtin signatures, Tool schemas, theme tokens, or live Slot '
            +'trees and props. Host queries run locally. A Client query waits for the first valid page response and '
            +'remains pending until a page answers or the Tool is cancelled. This Tool cannot invoke business Service '
            +'methods or modify the runtime. For Service.listService and Event.listEvents, query without input to navigate '
            +'the compact signature directory, then query the exact service or event for its structured contract and '
            +'referenced types. For Slots.listSubTree, query without root to navigate the compact tree, then query the '
            +'exact root for its complete registration contract and props.'
        ),#说明
        'parameters':{#参数
            'platform':{'type':'string','required':True,'enum':['host','client'],'description':'Runtime platform that owns the Provider.'},#平台
            'provider':{'type':'string','required':True,'description':'Exact Provider ID returned by cordis_inspect_list.'},#提供方
            'method':{'type':'string','required':True,'description':'Exact method name declared by the Provider manifest.'},#方法
            'input':{'type':'json','description':'Optional query input; it must satisfy the method input schema.'},#可选输入
        },#参数
        'output':{'schema':{'type':'json'},'render':列表渲染},#输出
        'execute':查询执行,#执行
        'presentCall':呈现巡检查询调用,#展示
    }))#查询工具结束

    def 自检执行(参数,执行):
        """按层细化自检。参数与执行为 dict。"""
        智能体=要求智能体(执行)#调用方 Agent
        if 'packageId' in 参数 and 'pluginId' not in 参数:#有包无插件
            raise 工具错误('cordis_inspect_self 的 packageId 必须带 pluginId')#必须带插件
        if 'pluginId' not in 参数:#列出全部插件
            return {'mode':'plugins','plugins':[自检摘要(引用) for 引用 in 上下文.dynamicCordisRunner.列插件(智能体)]}#摘要列表
        插件标识=动态插件标识(参数['pluginId'])#品牌化
        if 'packageId' not in 参数:#只查插件
            插件=上下文.dynamicCordisRunner.巡检插件(智能体,插件标识)#读插件
            包列表=[]#每个包
            for 包 in 插件['packages']:#映射
                项={**包,'packageId':str(包['packageId'])}#品牌转字符串
                项['isCurrent']='currentPackageId' in 插件 and 包['packageId']==插件['currentPackageId']#是否当前
                项['isNext']='nextPackageId' in 插件 and 包['packageId']==插件['nextPackageId']#是否下一个
                包列表.append(项)#收入
            return {#插件详情
                'mode':'plugin',#模式
                **自检摘要(插件),#摘要字段
                'packages':包列表,#包映射
            }#详情
        return 自检包(上下文,智能体,插件标识,动态包标识(参数['packageId']))#精确到包

    上下文.tools.登记(定义工具({#登记自检工具
        'name':'cordis_inspect_self',#工具名
        'description':(#工具说明
            'Inspect dynamic Cordis objects owned by the current Session at increasing levels of detail. With no IDs, '
            +'list only Plugin summaries. With pluginId alone, return version pointers, the latest Run, and every Package '
            +'summary. Only pluginId plus packageId returns that immutable Package\'s Host/Client source and runtime '
            +'diagnostics. packageId cannot be supplied alone. Query an exact Package before handling @pluginId, repairing '
            +'an asynchronous failure, or defining an updated version. This Tool is read-only: it neither executes code '
            +'nor changes version pointers.'
        ),#说明
        'parameters':{#参数
            'pluginId':{'type':'string','description':'Stable Plugin ID returned by cordis_define or injected by @pluginId; omit it to list every current Plugin.'},#插件
            'packageId':{'type':'string','description':'Exact immutable Package ID owned by pluginId; when specified, source and diagnostics are returned.'},#包
        },#参数
        'output':{'schema':{'type':'json'},'render':列表渲染},#输出
        'execute':自检执行,#执行
        'presentCall':呈现自检调用,#展示
    }))#自检工具结束

    def 定义执行(参数,执行):
        """写入定义。参数与执行为 dict。"""
        插件选择=参数['plugin']#插件选择
        if 插件选择['kind']=='new':#新建
            插件={'kind':'new','idPrefix':插件选择['idPrefix']}#只带前缀
        else:#已有
            插件={'kind':'existing','pluginId':动态插件标识(插件选择['pluginId'])}#品牌化
        代码={}#源码
        if 'host' in 参数['code']:#有宿主半
            代码['host']=参数['code']['host']#带上
        if 'client' in 参数['code']:#有客户端半
            代码['client']=参数['code']['client']#带上
        回执=上下文.dynamicCordisRunner.定义({#写入定义
            'sessionId':要求智能体(执行).id,#所属会话
            'plugin':插件,#新建或已有
            'name':参数['name'],#包名
            'purpose':参数['purpose'],#用途
            'code':代码,#源码
        })#define
        return {**回执,'pluginId':str(回执['pluginId']),'packageId':str(回执['packageId'])}#回执

    def 定义渲染(参数,值):
        """已定义未运行。"""
        return [{'type':'text','text':'Defined '+值['pluginId']+'/'+值['packageId']+' ('+值['name']+'); it is not running yet. Use cordis_run to activate this Package.'}]#文本

    上下文.tools.登记(定义工具({#登记定义工具
        'name':'cordis_define',#工具名
        'description':(#工具说明
            'Define an immutable Cordis Package. For a new Plugin, use kind:"new" and provide only a semantic prefix of '
            +'3–6 lowercase English letters; the Host returns the final pluginId and packageId. To modify an existing '
            +'Plugin, use kind:"existing" with its exact pluginId to append a Package without overwriting older versions. '
            +'Provide at least one of code.host and code.client. Each value is a plain Python function body (Host) or '
            +'plain JavaScript function body (Client) that returns a Cordis Plugin; no TypeScript, JSX, or import transformation occurs. Query Inspect before depending on a '
            +'Service, Event, Builtin, Slot, or token. Define only validates parameters and syntax and records source: it '
            +'does not request approval, execute apply, or change currentPackageId. On success, call cordis_run with the '
            +'returned IDs.'
        ),#说明
        'parameters':{#参数
            'plugin':{#插件选择
                'required':True,#必填
                'oneOf':[#新建或已有
                    {'type':'object','additionalProperties':False,'properties':{'kind':{'type':'string','const':'new','required':True},'idPrefix':{'type':'string','required':True,'description':'Suggested semantic prefix of 3–6 lowercase English letters; the Host adds a unique numeric suffix.'}}},#新建
                    {'type':'object','additionalProperties':False,'properties':{'kind':{'type':'string','const':'existing','required':True},'pluginId':{'type':'string','required':True,'description':'Exact ID of an existing Plugin; the new Package is appended to that instance.'}}},#已有
                ],#oneOf
            },#plugin
            'name':{'type':'string','required':True,'description':'Short, readable Package name.'},#包名
            'purpose':{'type':'string','required':True,'description':'One-sentence, user-facing description of the Package purpose.'},#用途
            'code':{'type':'object','additionalProperties':False,'required':True,'properties':{'host':{'type':'string','description':'Plain Python function body that returns the Host-half Cordis Plugin.'},'client':{'type':'string','description':'Plain JavaScript function body that returns the browser Client-half Cordis Plugin.'}}},#源码
        },#参数
        'output':{#输出
            'schema':{'type':'object','additionalProperties':False,'properties':{'pluginId':{'type':'string','required':True},'packageId':{'type':'string','required':True},'name':{'type':'string','required':True},'purpose':{'type':'string','required':True},'hasHostHalf':{'type':'boolean','required':True},'hasClientHalf':{'type':'boolean','required':True}}},#回执模式
            'render':定义渲染,#渲染
            'presentationMeta':定义元数据,#展示元数据
        },#输出
        'execute':定义执行,#执行
        'presentCall':呈现定义调用,#展示
    }))#定义工具结束

    def 运行渲染(参数,值):
        """按状态选句子。"""
        结果=要求json对象(值)#必须是对象
        插件标识=要求json字符串(结果,'pluginId')#插件 id
        包标识=要求json字符串(结果,'packageId')#包 id
        运行标识=要求json字符串(结果,'pluginRunId')#运行 id
        if 'status' in 结果 and 结果['status']=='awaiting-approval':#等审批
            文本=插件标识+'/'+包标识+' is awaiting user approval ('+运行标识+').'#等审批
        elif 'status' in 结果 and 结果['status']=='starting':#启动中
            文本=插件标识+'/'+包标识+' is starting asynchronously ('+运行标识+').'#异步启动
        else:#已在跑
            文本=插件标识+'/'+包标识+' is running ('+运行标识+').'#已在跑
        return [{'type':'text','text':文本}]#文本块

    def 运行执行(参数,执行):
        """请求运行。参数与执行为 dict。"""
        智能体=要求智能体(执行)#调用方 Agent
        插件标识=动态插件标识(参数['pluginId'])#品牌化
        包标识=动态包标识(参数['packageId'])#品牌化
        信号=执行['signal'] if 'signal' in 执行 else None#可选中止
        回执=上下文.dynamicCordisRunner.运行(智能体,插件标识,包标识,参数['mode'],信号)#请求运行
        if not 回执['ok']:#失败
            raise 工具错误(回执['message'])#抛出
        if 回执['status']!='running':#尚未跑起来
            结果={#异步/审批回执
                'status':回执['status'],#状态
                'pluginId':参数['pluginId'],#插件 id
                'packageId':参数['packageId'],#包 id
                'pluginRunId':str(回执['pluginRunId']),#运行 id
                'mode':回执['mode'],#模式
                'nextPackageId':str(回执['nextPackageId']),#下一个包
            }#回执
            if 'currentPackageId' in 回执:#有当前
                结果['currentPackageId']=str(回执['currentPackageId'])#带上
            return 结果#回执
        行=None#该插件快照
        for 候选 in 上下文.dynamicCordisRunner.快照(智能体):#查找
            if 候选['pluginId']==插件标识:#命中
                行=候选#记下
                break#结束
        光纤=None#匹配本次运行的 Fiber
        if 行 is not None and 'activeRun' in 行 and 行['activeRun']['pluginRunId']==回执['pluginRunId']:#匹配
            光纤=行['activeRun']['fiber'] if 'fiber' in 行['activeRun'] else None#纤维
        客户端等待=回执['clientWaitingFor'] if 'clientWaitingFor' in 回执 else None#客户端等待
        下一包={} if 'nextPackageId' not in 回执 else {'nextPackageId':str(回执['nextPackageId'])}#有 next 才带
        return {#已运行回执
            'status':'running',#状态
            'pluginId':参数['pluginId'],#插件 id
            'packageId':参数['packageId'],#包 id
            'pluginRunId':str(回执['pluginRunId']),#运行 id
            'currentPackageId':str(回执['currentPackageId']),#当前包
            **下一包,#有 next 才带
            'host':{#宿主半
                'status':'absent' if 光纤 is None else ('running' if len(缺失服务(上下文,光纤))==0 else 'waiting'),#状态
                'provides':[] if 光纤 is None else 已提供服务(上下文,光纤),#提供
                'waitingFor':[] if 光纤 is None else 缺失服务(上下文,光纤),#等待
            },#宿主
            'client':{#客户端半
                'status':'absent' if 客户端等待 is None else ('running' if len(客户端等待)==0 else 'waiting'),#状态
                'waitingFor':[] if 客户端等待 is None else list(客户端等待),#等待项
            },#客户端
        }#回执

    上下文.tools.登记(定义工具({#登记运行工具
        'name':'cordis_run',#工具名
        'description':(#工具说明
            'Activate one exact Package of a dynamic Plugin. Use mode:"run" for the first activation, restarting '
            +'currentPackageId, or rollback. When current exists, use mode:"update" to switch to a different Package, '
            +'even if the Plugin is currently stopped. An unauthorized Client Package creates an approval request and '
            +'returns awaiting-approval; an authorized Package returns starting and continues asynchronously in the '
            +'browser. Neither result waits for the final outcome inside the Tool. currentPackageId changes only after '
            +'complete success; on failure, the old current and target next remain. Asynchronous success, rejection, or '
            +'technical failure is reported through state and steering. After a technical failure, read diagnostics with '
            +'cordis_inspect_self, correct the same Plugin, and retry autonomously. Do not request approval again after '
            +'the user rejects it.'
        ),#说明
        'parameters':{#参数
            'pluginId':{'type':'string','required':True,'description':'Stable Plugin ID returned by cordis_define.'},#插件
            'packageId':{'type':'string','required':True,'description':'Exact immutable Package ID to activate under that Plugin.'},#包
            'mode':{'type':'string','required':True,'enum':['run','update'],'description':'Use run for the first activation, restarting current, or rollback; use update to switch from current to a different Package.'},#模式
        },#参数
        'output':{#输出
            'schema':{'type':'json'},#JSON
            'render':运行渲染,#渲染
            'presentationMeta':运行元数据,#元数据
        },#输出
        'execute':运行执行,#执行
        'presentCall':呈现运行调用,#展示
    }))#运行工具结束

    def 停止执行(参数,执行):
        """请求停止。"""
        回执=上下文.dynamicCordisRunner.停止(要求智能体(执行),动态插件标识(参数['pluginId']))#请求停止
        if (not 回执['ok']) and 回执['reason']!='not-running':#非幂等失败
            raise 工具错误(回执['message'])#抛
        return {'pluginId':参数['pluginId']}#回插件 id

    上下文.tools.登记(定义工具({#登记停止工具
        'name':'cordis_stop',#工具名
        'description':(#工具说明
            'Stop the current Run of a dynamic Plugin and cancel unfinished approval or activation requests. Retain the '
            +'Plugin, every immutable Package, grants, currentPackageId, and nextPackageId so it can later run or update '
            +'directly. Stopping an already stopped Plugin succeeds idempotently. Use this Tool to disable effects '
            +'temporarily; use cordis_undefine for permanent removal.'
        ),#说明
        'parameters':{'pluginId':{'type':'string','required':True,'description':'Stable dynamic Plugin ID to stop.'}},#参数
        'output':{'schema':{'type':'object','additionalProperties':False,'properties':{'pluginId':{'type':'string','required':True}}},'render':停止渲染},#输出
        'execute':停止执行,#执行
        'presentCall':呈现停止调用,#展示
    }))#停止工具结束

    def 移除执行(参数,执行):
        """请求移除。"""
        回执=上下文.dynamicCordisRunner.取消定义(要求智能体(执行),动态插件标识(参数['pluginId']))#请求移除
        if not 回执['ok']:#失败
            raise 工具错误(回执['message'])#抛
        return {'pluginId':参数['pluginId'],'wasRunning':回执['wasRunning']}#回 id 与是否曾在跑

    上下文.tools.登记(定义工具({#登记永久移除工具
        'name':'cordis_undefine',#工具名
        'description':(#工具说明
            'Permanently remove a dynamic Plugin owned by the current Session. If it is running or awaiting approval, '
            +'first stop it and cancel the request, then delete every Package, grant, and version pointer. After this '
            +'returns, its pluginId, packageIds, @ reference, and Package business views are invalid; historical cards '
            +'retain only a "Plugin removed" record. Do not call this Tool when versions must remain available for restart '
            +'or rollback; use cordis_stop instead.'
        ),#说明
        'parameters':{'pluginId':{'type':'string','required':True,'description':'Stable dynamic Plugin ID to remove permanently.'}},#参数
        'output':{'schema':{'type':'object','additionalProperties':False,'properties':{'pluginId':{'type':'string','required':True},'wasRunning':{'type':'boolean','required':True}}},'render':移除渲染},#输出
        'execute':移除执行,#执行
        'presentCall':呈现移除调用,#展示
    }))#移除工具结束

    def 步进前(载荷,下一):
        """把上下文接到后续消息后。载荷为 dict；下一() 同步返回决策 dict。"""
        决策=下一()#先走后续监听器
        if 决策['kind']=='reject':#已拒绝
            return 决策#原样返回
        消息列表=决策['messages'] if 'messages' in 决策 else []#后续消息；?? 缺席才空
        标识列表=收集引用插件标识(载荷['messages'] if 'messages' in 载荷 else [])#消息里点到的插件 id
        if len(标识列表)==0:#没有引用
            return 决策#原样
        信号=载荷['signal'] if 'signal' in 载荷 else None#取消信号
        if 信号 is not None and 信号.is_set():#已取消
            raise 工具错误('已中止')#抛
        智能体=载荷['agent']#智能体
        上下文列表=[]#每条引用一条上下文消息
        for 标识 in 标识列表:#每条引用
            引用=上下文.dynamicCordisRunner.引用(智能体,动态插件标识(标识))#查引用
            文本=渲染不可用引用(标识) if 引用 is None else 渲染引用(引用)#有则渲染
            上下文列表.append(创建用户消息({'content':[{'type':'text','text':文本}],'source':{'kind':'plugin','plugin':名称,'form':'instructions'}}))#合成
        return {'kind':'enter','messages':list(消息列表)+上下文列表}#把上下文接到后续消息后

    上下文.监听('agent/pre-step',步进前)#pre-step

name=名称#框架槽
inject=注入#框架槽
apply=应用#框架槽
