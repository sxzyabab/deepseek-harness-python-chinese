"""按包的浏览器生命周期：可观察面、加载结果与现场摘要。

对齐上游 `cordis-client-runner/src/client/runtime.ts` 可落盘面。公开面仅中文名。
无法 JS·vm / Loader / ModuleLoader 执行：evaluateClientHalf、loader.create、模块表工厂。
本模块落盘类型词汇、错误抽取、模块 id、排队/收回/优先级/认领与现场快照投影。
"""
from .求值器 import 客户端重定向,动态样式#渲染崩溃重定向与样式记账

__all__=[#仅中文公开名
    '加载失败阶段','浏览器半字段','渲染失败字段','运行器环境字段',
    '模块标识','错误字段','渲染失败消息','成功结果','说明',
    '可观察','现场包投影','包运行器记账',
]#公开面结束

说明='mount/teardown 的 Loader 入口与 ModuleLoader 工厂需浏览器；排队/收回/认领/递减优先级本树可跑。'#说明

加载失败阶段=('evaluate','module-import','activate')#失败阶段

浏览器半字段=('pluginId','packageId','pluginRunId','agentId','name','code')#DynamicCordisClientHalf

渲染失败字段=('slot','message','stack','abdicated')#DynamicCordisRenderFailure

运行器环境字段=('ctx','loader','modules','slots','invoke','reportRenderFailure','reportGuardFailure')#RunnerEnv

def 模块标识(插件标识):#模块/入口 id
    """dyn/<pluginId>。"""
    return f'dyn/{插件标识}'#前缀

def 错误字段(错误):#抽取错误字段
    """保住 message 与可选 stack。"""
    if not isinstance(错误,(dict,BaseException)) and not hasattr(错误,'message'):#非对象
        return {'message':str(错误)}#串
    if isinstance(错误,dict):#映射
        消息=错误.get('message')#消息
        栈=错误.get('stack')#栈
        出={'message':消息 if isinstance(消息,str) else str(错误)}#消息
        if isinstance(栈,str):#有栈
            出['stack']=栈#带
        return 出#字段
    消息=getattr(错误,'message',None)#属性
    出={'message':消息 if isinstance(消息,str) else str(错误)}#消息
    栈=getattr(错误,'stack',None)#栈
    if isinstance(栈,str):#有
        出['stack']=栈#带
    return 出#字段

def 渲染失败消息(槽,消息):#渲染崩溃教学
    """槽加崩溃；点名被扣全局则追加重定向。"""
    重定向=None#文
    for 名,文 in 客户端重定向.items():#每条
        if 名 in 消息 and 文 not in 消息:#点名且未带
            重定向=文#记下
            break#停
    基=f'your entry in slot "{槽}" crashed while React rendered it: {消息}'#基
    return 基 if 重定向 is None else 基+'\n'+重定向#拼

def 成功结果(运行标识,等待=None):#成功加载
    """对齐 settled。"""
    出={'ok':True,'pluginRunId':运行标识}#成功
    if 等待:#停等
        出['waitingFor']=list(等待)#带
    return 出#结果

def 可索引组件(组件):#能否当认领键
    """对象实例可认领；标量不可。"""
    return 组件 is not None and not isinstance(组件,(str,bytes,int,float,bool))#对象

class 可观察:#快照源
    """getSnapshot + subscribe。"""
    def __init__(自身,读快照):#构造
        """记下读函数。"""
        自身._读=读快照#读
        自身._听=set()#订阅者

    def getSnapshot(自身):#读
        """当前值。"""
        return 自身._读()#读

    def subscribe(自身,函数):#订阅
        """返回退订。"""
        自身._听.add(函数)#加
        def 退():#退订
            """拿掉。"""
            自身._听.discard(函数)#删
        return 退#拆除器

    def 通知(自身):#广播
        """通知全部。"""
        for 函数 in list(自身._听):#逐个
            函数()#唤

class 现场包投影:#DynamicCordisLivePackage
    """从记账投影只读行。"""
    @staticmethod
    def 从记账(记账):#投影
        """pkg + ledger + styles → 行。"""
        包=记账.get('pkg') or {}#包
        账本=记账.get('ledger') or []#账本
        样式=记账.get('styles')#样式
        槽名=[]#去重保序
        已见=set()#已见
        for 行 in 账本:#逐行
            if not isinstance(行,dict):#跳过
                continue#下一条
            槽=行.get('slot')#槽
            if 槽 is None or 槽 in 已见:#无或重复
                continue#跳
            已见.add(槽)#记下
            槽名.append(槽)#加入
        样式数=getattr(样式,'数量',None)#中文
        if 样式数 is None:#英文
            样式数=getattr(样式,'count',len(getattr(样式,'标签们',[]) or []) if 样式 else 0)#回退
        return {#行
            'pluginId':包.get('pluginId'),#插件
            'packageId':包.get('packageId'),#包
            'pluginRunId':包.get('pluginRunId'),#运行
            'name':包.get('name'),#名
            'slots':槽名,#槽
            'styleCount':样式数,#样式数
        }#结束

class 包运行器记账:#页本地现场表（无 Loader mount）
    """live/queues/failures/owners/priority；mount 本体仍需浏览器。"""
    def __init__(自身,环境=None):#构造
        """可选 env：挂载钩子 / 报告钩子。"""
        自身.环境=环境 or {}#环境
        自身.现场={}#pluginId → 记账
        自身.失败={}#pluginId → 渲染失败
        自身.队列尾={}#pluginId → 串队链接（Promise.then 同步等价）
        自身.所有者={}#id(组件) → {pluginId,pluginRunId,agentId}
        自身.下一优先级=0#页本地遮蔽名次；后登记 -- 递减
        自身._听=set()#订阅
        自身._快照缓存=None#现场快照缓存
        自身._失败缓存=None#失败快照缓存

    def subscribe(自身,函数):#订阅
        """退订器。"""
        自身._听.add(函数)#加
        def 退():#退
            """拿掉。"""
            自身._听.discard(函数)#删
        return 退#器

    def _通知(自身):#广播
        """清缓存并通知。"""
        自身._快照缓存=None#失效
        自身._失败缓存=None#失效
        for 函数 in list(自身._听):#逐个
            函数()#唤

    def 分配优先级(自身):#allocatePriority：对齐 `--nextPriority`
        """后登记更前；先递减再返回（首调为 -1）。"""
        自身.下一优先级-=1#递减
        return 自身.下一优先级#名次

    def _入队(自身,标识,操作):#enqueue：Promise 串队的同步等价
        """接在该包先前操作之后；先前成败吞掉，不堵后续；链接可幂等重读。"""
        上一=自身.队列尾.get(标识)#上一尾
        态={'done':False,'value':None,'error':None}#本环缓存
        def 链接():#一次包操作
            """落定后可重入只回缓存。"""
            if 态['done']:#已跑
                if 态['error'] is not None:#曾失败
                    raise 态['error']#原错
                return 态['value']#原值
            if 上一 is not None:#等上一
                try:#成败都过
                    上一()#落定上一
                except Exception:#吞掉——对齐 next.then(()=>{}, ()=>{})
                    pass#不堵
            try:#本操作
                态['value']=操作()#跑
            except Exception as 错:#失败
                态['error']=错#记下
                态['done']=True#落定
                raise#交给调用方
            态['done']=True#落定
            return 态['value']#结果
        自身.队列尾[标识]=链接#新尾（失败也挺住）
        return 链接()#启动本环

    def 认领(自身,组件,插件标识,运行标识,会话标识):#claim 组件
        """身份即键；标量跳过。"""
        if not 可索引组件(组件):#不可
            return#停
        自身.所有者[id(组件)]={#记所有者
            'pluginId':插件标识,#插件
            'pluginRunId':运行标识,#运行
            'agentId':会话标识,#会话
        }#结束

    def 处理入口崩溃(自身,槽,入口,错误,信息):#onEntryError 半
        """只报告本运行器认领过的组件。"""
        组件=(入口 or {}).get('component') if isinstance(入口,dict) else getattr(入口,'component',None)#组件
        主=自身.所有者.get(id(组件)) if 可索引组件(组件) else None#所有者
        if 主 is None:#不是我们的
            return#停
        细节=错误字段(错误)#字段
        失败={#渲染失败
            'slot':槽,#槽
            'message':渲染失败消息(槽,细节['message']),#教学
            'abdicated':bool((信息 or {}).get('abdicated') if isinstance(信息,dict) else getattr(信息,'abdicated',False)),#退役
        }#结束
        if 'stack' in 细节:#有栈
            失败['stack']=细节['stack']#带
        报告=自身.环境.get('reportRenderFailure')#报告钩
        if callable(报告):#有
            报告(主['agentId'],主['pluginId'],主['pluginRunId'],失败)#即发即忘
        自身.失败[主['pluginId']]=失败#页侧
        自身._通知()#通知

    def getSnapshot(自身):#现场快照
        """投影行；两次变更间引用稳定。"""
        if 自身._快照缓存 is None:#惰性
            自身._快照缓存=[现场包投影.从记账(记) for 记 in 自身.现场.values()]#投影
        return 自身._快照缓存#缓存

    def isLoaded(自身,插件标识):#是否已加载
        """表里有。"""
        return 插件标识 in 自身.现场#有

    def _拆掉(自身,插件标识):#teardown 记账半（无 Loader）
        """清现场、样式记账与失败。"""
        现=自身.现场.pop(插件标识,None)#拿掉
        自身.失败.pop(插件标识,None)#清崩溃
        if 现 is None:#无
            return#停
        样式=现.get('styles')#样式
        if 样式 is not None and hasattr(样式,'拆除全部'):#有
            样式.拆除全部()#清 CSS 记账

    def _加载体(自身,半边):#load 体（串队内）
        """同一运行空操作；另一运行先拆；无 mount 钩则只登记骨架（非冒充 Loader）。"""
        插件标识=半边['pluginId']#插件
        现=自身.现场.get(插件标识)#现有
        if 现 is not None:#已有
            包=现.get('pkg') or {}#包
            if 包.get('pluginRunId')==半边.get('pluginRunId'):#同一运行
                return 成功结果(半边['pluginRunId'],现.get('waitingFor'))#空操作
            自身._拆掉(插件标识)#另一运行先拆
        挂载=自身.环境.get('mount')#可选真实挂载（浏览器）
        if callable(挂载):#有钩
            结果=挂载(半边)#挂
            自身._通知()#通知
            return 结果#结局
        样式=动态样式(插件标识)#样式记账
        账本=[]#槽账本
        自身.现场[插件标识]={#骨架现场
            'pkg':{#包公告投影
                'pluginId':半边['pluginId'],#插件
                'packageId':半边['packageId'],#包
                'pluginRunId':半边['pluginRunId'],#运行
                'name':半边.get('name'),#名
            },#pkg
            'entryId':模块标识(插件标识),#入口 id
            'styles':样式,#样式
            'ledger':账本,#账本
            'waitingFor':[],#停等
        }#结束
        自身.失败.pop(插件标识,None)#新加载清旧崩溃
        自身._通知()#通知
        return 成功结果(半边['pluginRunId'])#骨架成功

    def load(自身,半边):#加载：按插件串队
        """对齐 enqueue(load)；重入接尾而非抛。"""
        return 自身._入队(半边['pluginId'],lambda:自身._加载体(半边))#串队

    def retract(自身,插件标识,运行标识):#收回：亦串队
        """匹配运行则拆掉。"""
        def 体():#串队内
            """匹配则拆。"""
            现=自身.现场.get(插件标识)#现有
            if 现 is None:#无
                return#停
            包=现.get('pkg') or {}#包
            if 包.get('pluginRunId')!=运行标识:#不是这次
                return#停
            自身._拆掉(插件标识)#拆
            自身._通知()#通知
        自身._入队(插件标识,体)#串队


    def dispose(自身):#拆除全部
        """插件拆除路径。"""
        for 标识 in list(自身.现场.keys()):#每个
            自身._拆掉(标识)#拆
        自身.所有者.clear()#清认领
        自身._通知()#通知

    @property
    def renderFailures(自身):#渲染失败可观察
        """可观察面。"""
        def 读():#惰性快照
            """失败图。"""
            if 自身._失败缓存 is None:#惰性
                自身._失败缓存=dict(自身.失败)#拷
            return 自身._失败缓存#缓存
        return 可观察(读)#图
