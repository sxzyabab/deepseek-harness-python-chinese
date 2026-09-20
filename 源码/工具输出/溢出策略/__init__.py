"""溢出策略插件：`tools/post-execute` 结果变换器，把过大的纯文本工具结果挡在模型上下文外。当最终结果的 UTF-8 大小超过 `maxInlineBytes` 时，它把全文保存到会话作用域溢出产物（`ctx.spillStore`），并用有界头/尾预览加上后端定位器与检索指引替换面向模型的结果。

它不注册服务，也不拥有存储或预览机制：预览是 `output_retention`（`文本保留器`），存储是 `ctx.spillStore`。策略只决定何时溢出并组合通知。

第二臂把同一上限应用到持久日志：`tools/ptc-dispatch-log` 瀑布约束 `tool/ptc-dispatch` 事件上过大 `run_code` 子调用结果的副本（程序的值不动；UI 和回放经溢出产物读全文）。

## 故意狭窄

- 省略 `maxInlineBytes` ⇒ 插件什么也不注册（真正空操作）。
- 仅纯文本结果：携带任何非文本块的结果原样留下（策略只知道最终格式化文本，不知道工具内部）。
- 嵌套复合调用跳过面向模型的臂；其持久日志副本改由 dispatch-log 臂约束。
- 已接受的值替换为注册表再校验和渲染而透传；此呈现策略不能在同一互斥决策里再替换内容。
- 面向模型的臂跳过 `read`，避免 `read → spill → 再 read` 循环；dispatch-log 臂也约束 `read` 子调用（日志副本不是模型上下文，而 `read` 正是产出巨大日志的工具）。
- 尽力而为：没有会话所有者、没有 `ctx.spillStore` 后端，或保存失败 ⇒ 记日志并返回原结果。溢出失败绝不能把成功的工具调用变成 `isError` 或藏起内联结果。

它与其他执行后监听器组合：其前置监听器经 `next()` 委托并约束得到的内容投影，因此工具拥有的异步投影先于通用约束跑，替换了内容的钩子其替换仍会被约束，值替换和 `block` 决策原样透传。
"""
from ...依赖.schemastery import 数字字段
from ...工具.输出保留 import 文本保留器,描述省略
from .类型 import (
    溢出策略执行字段,
    溢出策略智能体字段,
    溢出策略会话字段,
    溢出策略会话头字段,
)
__all__=[
    '名称','依赖','配置模式','应用',
    '溢出策略执行字段','溢出策略智能体字段','溢出策略会话字段','溢出策略会话头字段',
    '溢出策略错误',
]

名称='spill-policy'
依赖=['tools']
配置模式={
    'maxInlineBytes':数字字段(),#纯文本工具结果的面向模型上下文上限，UTF-8字节；省略则完全禁用
}

class 溢出策略错误(Exception):
    """溢出策略加载或运行失败。"""
    def __init__(自身,消息):
        super().__init__(消息)

def 字节长(文本):
    """按 UTF-8 计字节长度。"""
    return len(文本.encode('utf-8'))

def 压平纯文本(内容):
    """全文本内容压成一个 UTF-8 字符串；任一非文本块则为 None。"""
    文本=''
    for 块 in 内容:
        if 块['type']!='text':
            return None
        文本+=(块['text'] if 'text' in 块 else '') or ''
    return 文本

def 所有者会话标识(执行):
    """所属会话 id；没有智能体的调用（直接/测试调用）为 None。"""
    智能体=执行.agent
    if 智能体 is None:
        return None
    会话=智能体.session
    if 会话 is None:
        return None
    头=会话.header
    if 头 is None:
        return None
    return 头['id']

def 预览(文本,预算):
    """为 text 构造有界头/尾预览，把 budget 字节分到两端。"""
    头字节=(预算+1)//2#对齐 Math.ceil
    尾字节=预算//2#对齐 Math.floor
    保留器=文本保留器({'kind':'headTail','headBytes':头字节,'tailBytes':尾字节})
    保留器.推入(文本)
    留下=保留器.收尾()
    return {'text':留下['text'],'omitted':留下['omittedBytes']}

def 溢出通知(省略,引用):
    """给定省略与已存引用的溢出通知行（无预览、无前导空行）。"""
    省略句=描述省略(省略,'bytes')
    return '('+省略句+' Full formatted result stored at: '+str(引用['locator'])+'. '+str(引用['retrievalHint'])+')'

def 应用(上下文,配置):
    """安装溢出策略：省略上限则空操作；否则校验后挂前置 post-execute 与 code-dispatch-log 臂。"""
    if 'maxInlineBytes' not in 配置:
        return
    内联上限=配置['maxInlineBytes']
    if isinstance(内联上限,bool):
        raise 溢出策略错误('spill-policy: maxInlineBytes 必须是非负整数（实际为 '+str(内联上限)+')')#布尔不是数字
    if isinstance(内联上限,int):
        合法=内联上限>=0
    elif isinstance(内联上限,float) and 内联上限.is_integer():
        合法=内联上限>=0
    else:
        合法=False
    if not 合法:
        raise 溢出策略错误('spill-policy: maxInlineBytes 必须是非负整数（实际为 '+str(内联上限)+')')
    上限=int(内联上限)

    def 溢出替换(文本,总字节,会话标识,工具名,调用标识,标签):
        """溢出 text 并构造有界替换（预览 + 通知），或在策略必须保留原文时返回 None（无会话所有者、无后端、存储失败、或没有上限内替换）。面向模型的执行后臂与持久 dispatch-log 臂原样共享，使两边产出字节相同的投影。"""
        if 会话标识 is None:
            上下文.日志.警告('spill-policy: '+工具名+' '+标签+' 没有会话所有者；保留内联内容')
            return None
        溢出存储=上下文.获取服务('spillStore',False)
        if 溢出存储 is None:
            上下文.日志.警告('spill-policy: 未加载 ctx.spillStore 后端；保留内联内容')
            return None
        保存={
            'owner':{'sessionId':会话标识},
            'source':{'toolName':工具名,'callId':调用标识,'label':标签},
            'suggestedName':工具名+'.txt',
            'content':文本,
        }
        try:
            引用=溢出存储.保存文本(保存)
        except (OSError,UnicodeEncodeError) as 错误:
            #尽力而为：存储失败（权限、ENOSPC、后端宕）绝不能让调用失败或藏起内容——保留原内联。
            上下文.日志.警告('spill-policy: '+工具名+' 的 saveText 失败: '+str(错误)+'；保留内联内容')
            return None
        #把通知的字节成本预留在maxInlineBytes内，使替换（预览+空行+通知）永不超出已文档化上限——天真地花光预算再追加通知可能比上限还大，对刚好超限的结果甚至比原文还大。预留按最坏省略计数（完整字节总数）给通知定价：其位数上界真实计数，因此预留大小是安全上界，最终通知从不长于预留。`\n\n`是2字节连接。
        预留=字节长(溢出通知({'kind':'exact','count':总字节},引用))+2
        预览预算=max(0,上限-预留)
        预览结果=预览(文本,预览预算)
        通知=溢出通知(预览结果['omitted'],引用)
        预览文本=预览结果['text'] or ''
        替换文本=(预览文本+'\n\n'+通知) if len(预览文本)>0 else 通知
        #不变量：策略永不发出大于上限的替换。当通知单独就超过maxInlineBytes（极小上限或很长溢出根）时，没有上限内替换，因此保留内联内容——溢出会打破宣称的上限。（上限内替换总是小于原文，而原文按入口条件已>cap，因此这一次检查也覆盖「不比原文小」。已写下的溢出文件是无害孤儿；清理推迟。）
        if 字节长(替换文本)>上限:
            上下文.日志.警告('spill-policy: '+工具名+' 的溢出通知超过 maxInlineBytes；保留内联内容')
            return None
        return 替换文本

    def 面向模型臂(执行,结果,下一步,*剩余):
        """先委托，让下游监听器（例如钩子）结算结果；我们约束它所接受的。block 透传——溢出只塑造已接受的纯文本结果，从不塑造纠正反馈。"""
        决策=下一步()
        #跳过read，避免read→spill→再read循环。
        if 决策['kind']!='accept' or 'value' in 决策 or 执行.parent is not None or 执行.name=='read':
            return 决策
        内容=决策['content'] if 'content' in 决策 else None
        if 内容 is None:
            内容=结果['content']
        文本=压平纯文本(内容)
        if 文本 is None:
            return 决策
        总字节=字节长(文本)
        if 总字节<=上限:
            return 决策
        替换文本=溢出替换(文本,总字节,所有者会话标识(执行),执行.name,执行.callId,'result')
        if 替换文本 is None:
            return 决策
        接受={'kind':'accept','content':[{'type':'text','text':替换文本}]}
        if 'additionalContexts' in 决策:
            接受['additionalContexts']=决策['additionalContexts']
        return 接受

    上下文.监听('tools/post-execute',面向模型臂,{'前置':True})

    def 派发日志臂(派发,下一步,*剩余):
        """用与面向模型臂约束外层结果相同的方式，约束 tool/ptc-dispatch 事件上过大子调用结果的副本。程序返回值不动（它已整体越过 worker 边界）；只有会话日志副本缩成预览 + 定位器，因此回放和 UI 经溢出产物读全文，与溢出的原生结果一样。"""
        内容=下一步()
        #read子调用也溢出：日志副本不是模型上下文，因此执行后臂要避免的read→spill→再read循环在此不会发生，而read正是产出巨大日志的工具。
        文本=压平纯文本(内容)
        if 文本 is None:
            return 内容
        总字节=字节长(文本)
        if 总字节<=上限:
            return 内容
        替换文本=溢出替换(文本,总字节,所有者会话标识(派发['exec']),派发['name'],派发['subCallId'],'dispatch')
        if 替换文本 is None:
            return 内容
        return [{'type':'text','text':替换文本}]

    上下文.监听('tools/ptc-dispatch-log',派发日志臂,{'前置':True})

name=名称
inject=依赖
Config=配置模式
apply=应用
default=应用
