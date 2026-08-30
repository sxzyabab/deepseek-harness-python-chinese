"""溢出策略插件：`tools/post-execute` 结果变换器，把过大的纯文本工具结果挡在模型上下文外。当最终结果的 UTF-8 大小超过 `maxInlineBytes` 时，它把全文保存到会话作用域溢出产物（`ctx.spillStore`），并用有界头/尾预览加上后端定位器与检索指引替换面向模型的结果。

它不注册服务，也不拥有存储或预览机制：预览是 `output_retention`（`文本保留器`），存储是 `ctx.spillStore`。策略只决定何时溢出并组合通知。

第二臂把同一上限应用到持久日志：`tools/code-dispatch-log` 瀑布约束 `tool/code-dispatch` 事件上过大 `run_code` 子调用结果的副本（程序的值不动；UI 和回放经溢出产物读全文）。

## 故意狭窄

- 省略 `maxInlineBytes` ⇒ 插件什么也不注册（真正空操作）。
- 仅纯文本结果：携带任何非文本块的结果原样留下（策略只知道最终格式化文本，不知道工具内部）。
- 嵌套复合调用跳过面向模型的臂；其持久日志副本改由 dispatch-log 臂约束。
- 已接受的值替换为注册表再校验和渲染而透传；此展示策略不能在同一互斥决策里再替换内容。
- 面向模型的臂跳过 `read`，避免 `read → spill → 再 read` 循环；dispatch-log 臂也约束 `read` 子调用（日志副本不是模型上下文，而 `read` 正是产出巨大日志的工具）。
- 尽力而为：没有会话所有者、没有 `ctx.spillStore` 后端，或保存失败 ⇒ 记日志并返回原结果。溢出失败绝不能把成功的工具调用变成 `isError` 或藏起内联结果。

它与其他执行后监听器组合：其前置监听器经 `next()` 委托并约束得到的内容投影，因此工具拥有的异步投影先于通用约束跑，替换了内容的钩子其替换仍会被约束，值替换和 `block` 决策原样透传。
"""
import math#ceil与floor拆分头尾预算
from ...依赖 import cordis#外部依赖胶水
from ...依赖 import schemastery#配置字段
数字字段=schemastery.数字字段#配置字段
from ...工具.输出保留 import 文本保留器,描述省略#文本保留与省略描述
from .类型 import (#再导出执行视图词汇
    溢出策略执行字段,#策略所见执行
    溢出策略智能体字段,#可选智能体
    溢出策略会话字段,#会话
    溢出策略会话头字段,#会话头
)#类型导出结束
__all__=[#仅中文公开名；Cordis 英文槽不入表
    '名称','注入','配置模式','取字段','应用','默认',
    '溢出策略执行字段','溢出策略智能体字段','溢出策略会话字段','溢出策略会话头字段',
]#公开面结束

名称='spill-policy'#loader诊断所用的Cordis插件名
注入=['tools']#需要工具注册表（其tools/post-execute瀑布是我们变换的扩展点）
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
配置模式={#插件配置
    'maxInlineBytes':数字字段(),#纯文本工具结果的面向模型上下文上限，UTF-8字节；省略则完全禁用
}#配置模式结束
Config=配置模式#Cordis配置模式

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 缺席(对象,键):#字段是否缺席
    """对齐字段 === undefined。"""
    if 对象 is None:#空对象
        return True#缺席
    if isinstance(对象,dict):#映射
        return 键 not in 对象#无键则缺席
    return not hasattr(对象,键)#无属性则缺席

def 有自有(对象,键):#对齐Object.hasOwn
    """对齐 Object.hasOwn。"""
    if isinstance(对象,dict):#映射
        return 键 in 对象#映射键
    字典=getattr(对象,'__dict__',None)#实例字典
    if 字典 is None:#没有字典
        return False#没有字典
    return 键 in 字典#自有

def _是否thenable(值):#判定可等待对象
    if 值 is None:#空不是
        return False#不是
    if callable(getattr(值,'wait',None)):#Future 风格
        return True#可等待
    return callable(getattr(值,'等待',None))#外来 thenable

def _等待(值):#统一阻塞到结算
    if callable(getattr(值,'wait',None)):#Future 风格
        return 值.wait()#等待
    return 值.等待()#外来 thenable

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if _是否thenable(值):#可等待
        return _等待(值)#等待
    return 值#同步值

def 字节长(文本):#UTF-8字节长度
    """对齐 Buffer.byteLength(text, 'utf8')。"""
    return len(文本.encode('utf-8'))#按utf8计字节

def 是否非负整数(值):#对齐Number.isInteger且非负
    """非负整数（排除布尔）；浮点整值也接受以便对齐加载校验。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整型
        return 值>=0#非负
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return 值>=0#非负
    return False#其余非法

def 压平纯文本(内容):#全文本内容压成一个UTF-8字符串
    """全文本内容压成一个 UTF-8 字符串；任一非文本块则为 None。"""
    文本=''#累积文本
    for 块 in 内容:#逐块
        if 取字段(块,'type')!='text':#有非文本则放弃
            return None#放弃
        文本+=取字段(块,'text') or ''#拼接文本
    return 文本#纯文本

def 所有者会话标识(执行):#所属会话id
    """所属会话 id；没有智能体的调用（直接/测试调用）为 None。"""
    智能体=取字段(执行,'agent')#可选智能体
    会话=取字段(智能体,'session')#会话
    头=取字段(会话,'header')#会话头
    return 取字段(头,'id')#从头id读取

def 预览(文本,预算):#为text构造有界头/尾预览
    """为 text 构造有界头/尾预览，把 budget 字节分到两端。"""
    头字节=math.ceil(预算/2)#头预算
    尾字节=math.floor(预算/2)#尾预算
    保留器=文本保留器({'kind':'headTail','headBytes':头字节,'tailBytes':尾字节})#头尾保留器
    保留器.推入(文本)#推入全文
    留下=保留器.收尾()#完成保留
    return {'text':取字段(留下,'text'),'omitted':取字段(留下,'omittedBytes')}#预览与省略

def 溢出通知(省略,引用):#给定省略与已存引用的溢出通知行
    """给定省略与已存引用的溢出通知行（无预览、无前导空行）。"""
    省略句=描述省略(省略,'bytes')#省略描述
    return '('+省略句+' Full formatted result stored at: '+str(取字段(引用,'locator'))+'. '+str(取字段(引用,'retrievalHint'))+')'#通知正文

def 应用(上下文,配置):#安装溢出策略
    """安装溢出策略：省略上限则空操作；否则校验后挂前置 post-execute 与 code-dispatch-log 臂。"""
    if 缺席(配置,'maxInlineBytes'):#省略⇒无自动溢出策略
        return#什么也不注册
    内联上限=取字段(配置,'maxInlineBytes')#取出上限
    if not 是否非负整数(内联上限):#上限非法
        raise Exception('spill-policy: maxInlineBytes must be a non-negative integer (got '+str(内联上限)+')')#加载失败
    上限=int(内联上限)#已收窄上限（闭包收窄撑不过await）

    def 溢出替换(文本,总字节,会话标识,工具名,调用标识,标签):#构造溢出替换
        """溢出 text 并构造有界替换（预览 + 通知），或在策略必须保留原文时返回 None（无会话所有者、无后端、存储失败、或没有上限内替换）。面向模型的执行后臂与持久 dispatch-log 臂原样共享，使两边产出字节相同的投影。"""
        if 会话标识 is None:#没有会话所有者
            上下文.logger.warn('spill-policy: no session owner for '+工具名+' '+标签+'; keeping the inline content')#记警告
            return None#保留内联
        溢出存储=上下文.get('spillStore')#取溢出后端
        if not 溢出存储:#未加载后端
            上下文.logger.warn('spill-policy: no ctx.spillStore backend loaded; keeping the inline content')#记警告
            return None#保留内联
        保存={#保存请求
            'owner':{'sessionId':会话标识},#所有者
            'source':{'toolName':工具名,'callId':调用标识,'label':标签},#来源
            'suggestedName':工具名+'.txt',#建议名
            'content':文本,#全文
        }#save结束
        try:#持久全文
            引用=解开(溢出存储.保存文本(保存))#保存
        except Exception as 错误:#保存失败
            #尽力而为：存储失败（权限、ENOSPC、后端宕）绝不能让调用失败或藏起内容——保留原内联。
            上下文.logger.warn('spill-policy: saveText failed for '+工具名+': '+str(错误)+'; keeping the inline content')#记警告
            return None#保留内联
        #把通知的字节成本预留在maxInlineBytes内，使替换（预览+空行+通知）永不超出已文档化上限——天真地花光预算再追加通知可能比上限还大，对刚好超限的结果甚至比原文还大。预留按最坏省略计数（完整字节总数）给通知定价：其位数上界真实计数，因此预留大小是安全上界，最终通知从不长于预留。`\n\n`是2字节连接。
        预留=字节长(溢出通知({'kind':'exact','count':总字节},引用))+2#通知加连接的预留
        预览预算=max(0,上限-预留)#剩余给预览
        预览结果=预览(文本,预览预算)#头尾预览
        通知=溢出通知(取字段(预览结果,'omitted'),引用)#真实通知
        预览文本=取字段(预览结果,'text') or ''#预览正文
        替换文本=(预览文本+'\n\n'+通知) if len(预览文本)>0 else 通知#拼替换
        #不变量：策略永不发出大于上限的替换。当通知单独就超过maxInlineBytes（极小上限或很长溢出根）时，没有上限内替换，因此保留内联内容——溢出会打破宣称的上限。（上限内替换总是小于原文，而原文按入口条件已>cap，因此这一次检查也覆盖「不比原文小」。已写下的溢出文件是无害孤儿；清理推迟。）
        if 字节长(替换文本)>上限:#替换仍超上限
            上下文.logger.warn('spill-policy: spill notice for '+工具名+' exceeds maxInlineBytes; keeping the inline content')#记警告
            return None#保留内联
        return 替换文本#上限内替换

    def 面向模型臂(执行,结果,下一步,*剩余):#面向模型的post-execute臂
        """先委托，让下游监听器（例如钩子）结算结果；我们约束它所接受的。block 透传——溢出只塑造已接受的纯文本结果，从不塑造纠正反馈。"""
        决策=解开(下一步())#委托下游
        #跳过read，避免read→spill→再read循环。
        if 取字段(决策,'kind')!='accept' or 有自有(决策,'value') or 取字段(执行,'parent') is not None or 取字段(执行,'name')=='read':#非纯内容接受、嵌套或read则透传
            return 决策#透传
        内容=取字段(决策,'content')#决策内容
        if 内容 is None:#决策未换内容
            内容=取字段(结果,'content')#最终内容
        文本=压平纯文本(内容)#压平纯文本
        if 文本 is None:#非纯文本则透传
            return 决策#透传
        总字节=字节长(文本)#UTF-8字节
        if 总字节<=上限:#未超上限
            return 决策#原样
        替换文本=溢出替换(文本,总字节,所有者会话标识(执行),取字段(执行,'name'),取字段(执行,'callId'),'result')#尝试溢出
        if 替换文本 is None:#放弃则原样
            return 决策#原样
        接受={'kind':'accept','content':[{'type':'text','text':替换文本}]}#接受替换
        if 有自有(决策,'additionalContexts'):#保留下游附加上下文
            接受['additionalContexts']=取字段(决策,'additionalContexts')#附加上下文
        return 接受#接受替换

    上下文.on('tools/post-execute',面向模型臂,{'prepend':True})#前置监听

    def 派发日志臂(派发,下一步,*剩余):#持久dispatch-log臂
        """用与面向模型臂约束外层结果相同的方式，约束 tool/code-dispatch 事件上过大子调用结果的副本。程序返回值不动（它已整体越过 worker 边界）；只有会话日志副本缩成预览 + 定位器，因此回放和 UI 经溢出产物读全文，与溢出的原生结果一样。"""
        内容=解开(下一步())#委托下游
        #read子调用也溢出：日志副本不是模型上下文，因此执行后臂要避免的read→spill→再read循环在此不会发生，而read正是产出巨大日志的工具。
        文本=压平纯文本(内容)#压平纯文本
        if 文本 is None:#非纯文本
            return 内容#原样
        总字节=字节长(文本)#UTF-8字节
        if 总字节<=上限:#未超上限
            return 内容#原样
        替换文本=溢出替换(文本,总字节,所有者会话标识(取字段(派发,'exec')),取字段(派发,'name'),取字段(派发,'subCallId'),'dispatch')#尝试溢出日志副本
        if 替换文本 is None:#放弃则原样
            return 内容#原样
        return [{'type':'text','text':替换文本}]#替换日志副本

    上下文.on('tools/code-dispatch-log',派发日志臂,{'prepend':True})#前置监听

apply=应用#Cordis插件入口
default=应用#默认导出
默认=应用#中文默认导出
