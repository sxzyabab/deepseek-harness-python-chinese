"""建议性的按智能体重复调用检测器。它用已记录的模型上下文丰富后执行决策，既不否决也不改写调用。配置与链语义见包 README；理由见 repeat-tool-reminder Agent Note。"""
import json,re,weakref#JSON规范串、通配正则与按智能体弱表
from ...依赖 import cordis#外部依赖胶水
from ...依赖.schemastery import 路径上节点,列表字段,数字字段,字符串字段#配置字段
是否thenable=cordis.工具.是否thenable#可等待判定
from ...模型后端.llm import 创建用户消息#构造提醒用户消息

名称='repeat-tool-reminder'#loader诊断所用的Cordis插件名
name=名称#Cordis插件名

__all__=['名称','配置模式','应用','默认']#仅中文公开名；Cordis 槽英文别名不入表

配置模式=路径上节点({#插件配置：同名 schema 加 apply 里的加载时检查（错误配置大声失败）
    'thresholds':列表字段(数字字段(),默认值=[3,5,8]),#触发提醒的连续重复次数
    'include':列表字段(字符串字段(),默认值=[]),#要跟踪的工具名模式；空表示跟踪每个工具
    'exclude':列表字段(字符串字段(),默认值=[]),#对链透明的工具名模式（既不计数也不重置）
    'argumentsPreviewChars':数字字段(默认值=500),#DETAILED提醒里引用的规范参数最大字符数
})#配置模式结束
Config=配置模式#Cordis配置模式

# 本守卫注入的每条提醒上盖的 `{kind:'plugin'}` 来源——标签是承重的（未标记的上下文在派生历史里会渲成用户提示词）。
插件来源={'kind':'plugin','plugin':'repeat-tool-reminder'}#插件来源戳

# 温和的第一阈值提醒。键到 `thresholds[0]`，而不是字面次数，因此自定义第一阈值仍保持先温和再详细的升级。
温和提醒=(#第一档温和提醒
    'You are repeating the exact same tool call with identical arguments. '#前半
    +'Carefully analyze the previous result before calling again: if the task is '#中段
    +'not complete, try a different approach or different arguments instead of '#续段
    +'repeating the call.'#温和提醒正文
)#温和提醒结束

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 是否整数(值):#对齐 Number.isInteger；排除布尔
    """是否为整数（排除布尔）。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整型
        return True#是整数
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return True#是整数
    return False#其余非法

def 详细提醒(工具名,次数,规范参数):#拼详细提醒
    """点名工具、连续次数与规范参数的后续阈值详细提醒。"""
    return (#详细提醒正文
        'Repeated tool call detected:\n'#标题
        +'- tool: '+工具名+'\n'#工具名
        +'- consecutive_calls: '+str(次数)+'\n'#连续次数
        +'- arguments: '+规范参数+'\n'#规范参数
        +'The repeated calls are not making progress. Do not call this tool with '#要求换做法前半
        +'these exact arguments again. Inspect the latest result and choose a '#中段
        +'different action, different arguments, or finish the task if enough '#续段
        +'evidence has been gathered.'#结尾
    )#返回详细提醒

def 排序Json值(值):#深键排序JSON值
    """对已解析 JSON 值做深键排序，使仅属性顺序不同的两个参数对象规范化后相同。参数以循环的 JSON.parse 输出到达守卫（或畸形参数 JSON 的原始字符串回退），因此 JSON 的值域就是全部输入域——不处理 bigint、环或 undefined，因为没有任何输入路径能产生它们。"""
    if isinstance(值,list):#数组逐项排序
        return [排序Json值(项) for 项 in 值]#递归排序
    if isinstance(值,dict):#普通对象
        已排={}#按键排序后的对象
        for 键 in sorted(值.keys()):#按键名排序
            已排[键]=排序Json值(值[键])#递归排序值
        return 已排#返回排序对象
    return 值#标量原样返回

def 规范化(参数值):#规范化参数
    """一次调用参数的规范字符串形式：深键排序后 stringify。"""
    return json.dumps(排序Json值(参数值),ensure_ascii=False,separators=(',',':'))#排序后紧凑序列化

def 通配转正则(模式串):#通配转正则
    """把一条 `*` 通配模式编译成锚定正则（其余正则元字符按字面匹配）。"""
    转义=re.sub(r'[|\\{}()\[\]^$+?.]',lambda 匹配:'\\'+匹配.group(0),模式串)#转义元字符（不含*）
    return re.compile('^'+转义.replace('*','.*')+'$')#锚定并把*换成.*

def 预览参数(规范串,上限):#预览截断
    """为在详细提醒里引用而头截断规范参数，并标出省略了多少。只约束模型可见文本——链键始终使用完整规范字符串。"""
    if len(规范串)<=上限:#未超上限原样
        return 规范串#原样
    return 规范串[:上限]+'… (+'+str(len(规范串)-上限)+' more chars)'#截断并标省略量

def 校验阈值(值们):#校验并排序阈值
    """按大声失败约定校验 `thresholds` 并返回升序排序结果（升级规则把 `thresholds[0]` 读成温和档，因此顺序在此归一一次）。"""
    if len(值们)==0:#空列表
        raise Exception('repeat-tool-reminder: `thresholds` must not be empty')#拒绝空阈值
    for 值 in 值们:#逐个检查
        if (not 是否整数(值)) or 值<2:#非整数或小于2
            raise Exception('repeat-tool-reminder: invalid threshold '+str(值)+' — every threshold must be an integer >= 2')#拒绝非法阈值
    if len(set(值们))!=len(值们):#有重复
        raise Exception('repeat-tool-reminder: `thresholds` must not contain duplicates')#拒绝重复
    return sorted(值们)#升序拷贝

def 前置上下文(本提醒,下游们):#叠提醒到下游上下文
    """前置本守卫的提醒，同时保留每条下游上下文的来源与元数据。"""
    return [本提醒]+list(下游们 or [])#本提醒在前

def 应用(上下文对象,配置):#安装重复提醒守卫
    """安装守卫的监听器。`thresholds` 在此再按大声失败检查一遍。"""
    # schemastery 的默认= 保证校验后字段已设。
    阈值们=校验阈值(list(取字段(配置,'thresholds') or []))#校验并排序阈值
    阈值集合=set(阈值们)#阈值集合
    包含模式们=[通配转正则(项) for 项 in list(取字段(配置,'include') or [])]#包含正则
    排除模式们=[通配转正则(项) for 项 in list(取字段(配置,'exclude') or [])]#排除正则
    参数预览字符=取字段(配置,'argumentsPreviewChars')#预览上限
    if (not 是否整数(参数预览字符)) or 参数预览字符<1:#预览上限非法
        raise Exception('repeat-tool-reminder: invalid argumentsPreviewChars '+str(参数预览字符)+' — must be an integer >= 1')#拒绝非法上限
    链表=weakref.WeakKeyDictionary()#按智能体持有重复链（对齐 WeakMap）

    def 已跟踪(工具名):#是否跟踪该工具
        """工具是否参与链（未跟踪的调用透明：既不计数也不重置）。"""
        if len(包含模式们)>0 and (not any(模式.match(工具名) for 模式 in 包含模式们)):#不在包含集
            return False#不跟踪
        return not any(模式.match(工具名) for 模式 in 排除模式们)#不在排除集

    def 观察(执行):#观察一次调用
        """为一次尝试推进调用方智能体的链，若本次连续长度命中配置阈值则返回要投递的提醒。计数发生在这里——后执行——因为被拒绝的调用也流经本瀑布（`ToolRuntime.execute` 把拒绝走同一管道），模型对着被拒绝调用猛砸正是值得打断的循环。"""
        # 直接 `ctx.tools.execute()` 的调用方没有可提醒的模型，也没有可键控的 id；只有智能体循环调用参与。
        智能体=取字段(执行,'agent')#调用方智能体
        if 智能体 is None:#非智能体调用忽略
            return None#无提醒
        工具名=取字段(执行,'name')#工具名
        if not 已跟踪(工具名):#未跟踪工具透明
            return None#无提醒
        规范串=规范化(取字段(执行,'arguments'))#规范化参数
        键=json.dumps([工具名,规范串],ensure_ascii=False,separators=(',',':'))#调用身份键
        链=链表.get(智能体)#取出该智能体的链
        次数=(取字段(链,'count')+1) if (链 is not None and 取字段(链,'key')==键) else 1#同键则累加否则从1
        链表[智能体]={'key':键,'count':次数}#写回链
        if 次数 not in 阈值集合:#未命中阈值
            return None#无提醒
        文本=温和提醒 if 次数==阈值们[0] else 详细提醒(工具名,次数,预览参数(规范串,参数预览字符))#第一档温和，后续详细
        return 创建用户消息({#构造提醒消息
            'content':[{'type':'text','text':文本}],#提醒正文
            'source':{**插件来源,'form':'notice','summary':工具名+' × '+str(次数)},#插件通知来源
        })#createUserMessage结束

    def 工具后臂(执行,结果,下一步,*剩余):#拦截后执行瀑布
        """观察并丰富，从不否决：先计数（无论下游结局状态都推进），再委托以便后续监听器仍可拦截或替换，然后把提醒叠到返回值上——additionalContexts 骑在两种决策变体上，因此被拦截的调用仍会收到轻推。"""
        提醒=观察(执行)#观察并可能得到提醒
        下游=解开(下一步())#委托下游
        if 提醒 is None:#无提醒则原样返回
            return 下游#原样
        if 取字段(下游,'kind')=='block':#下游拦截
            return {#把提醒叠到拦截上
                'kind':'block',#拦截
                'feedback':取字段(下游,'feedback'),#下游反馈
                'additionalContexts':前置上下文(提醒,取字段(下游,'additionalContexts')),#叠提醒
            }#拦截返回
        合并=dict(下游)#继续决策：保留下游字段
        合并['additionalContexts']=前置上下文(提醒,取字段(下游,'additionalContexts'))#叠提醒
        return 合并#继续返回

    上下文对象.on('tools/post-execute',工具后臂)#安装后执行监听

    def 步进前臂(载荷,下一步,*剩余):#步进前重置
        """用户插话改变了上下文；跨过它的重复不是循环。纯重置钩：总是委托（既不附加也不否决）。"""
        智能体=取字段(载荷,'agent')#提交本步的智能体
        消息们=取字段(载荷,'messages') or []#本步消息
        if 智能体 is not None and any(取字段(取字段(消息,'source'),'kind')=='user' for 消息 in 消息们):#有用户消息则清链
            链表.pop(智能体,None)#删除该智能体链
        return 解开(下一步())#始终委托

    上下文对象.on('agent/pre-step',步进前臂)#安装步进前监听

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
