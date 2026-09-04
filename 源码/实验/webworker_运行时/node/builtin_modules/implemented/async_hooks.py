"""worker 的 `node:async_hooks`：显式切换模型上的 `AsyncLocalStorage`，带两路回退。
浏览器没有异步上下文跟踪，因此一次读取所答的存储由三个槽按序决定：

1. 钩子覆盖层 — 由钩子层在一个回调持续期间设置。
2. 恢复上下文 — 显式切换槽。`快照全部` 复制每个活动实例的有效存储，
   `恢复全部` 发布一份拷贝。
2b. 边界环境 — `run()` 也在此发布自有存储。
3. 折叠栈 — 改写器未触及代码的回退。

对齐上游 `webworker-runtime/src/node/builtin_modules/implemented/async_hooks.ts`。
公开面中文名；Node 面经 default 暴露英文名。
"""
from ...未实现失败 import 未实现失败#未实现失败工厂

__all__=[#公开面
    '异步本地存储','捕获异步上下文','在异步上下文运行','绑定异步上下文',
    '在异步上下文根运行','快照全部','恢复全部','als因果',
    'executionAsyncId','triggerAsyncId','createHook','AsyncResource',
    'AsyncLocalStorage','__esModule','default',
]#公开结束

原生then=None#原生then引用；模块加载时绑定
_承诺类=globals().get('Promise')#Promise构造器
if _承诺类 is not None and hasattr(_承诺类,'prototype'):#有原型
    原生then=getattr(_承诺类.prototype,'then',None)#原生then

实例们=set()#活动实例集

def 是否thenable(值):#是否thenable
    """对象或函数且带 then 方法。"""
    if 值 is None: return False#空
    if not isinstance(值,(dict,object)) and not callable(值): return False#非对象函数
    if isinstance(值,(int,float,str,bool)): return False#原始否
    return callable(getattr(值,'then',None))#有then方法

class 异步本地存储:#异步本地存储
    """Node 的 AsyncLocalStorage 面，收窄到宿主树所用成员。"""

    def __init__(自身):#构造
        """登记实例并清空各槽。"""
        自身._条目们=[]#折叠栈
        自身._覆盖=None#钩子覆盖层
        自身._环境们=[]#边界环境栈
        自身._已恢复=None#恢复上下文槽
        实例们.add(自身)#登记实例

    def run(自身,存储,回调,*参数):#进入边界运行
        """在操作整个寿命内以可见存储运行回调。"""
        条目={'store':存储}#折叠栈项
        自身._条目们.append(条目)#压入

        def 移除():#移除折叠项
            """按项身份移除。"""
            for 下标 in range(len(自身._条目们)-1,-1,-1):#自后向前
                if 自身._条目们[下标] is 条目:#身份匹配
                    自身._条目们.pop(下标)#移除
                    return#结束

        环境={'store':存储}#环境槽
        自身._环境们.append(环境)#压入环境

        def 卸边界():#卸边界
            """卸环境与折叠项，并恢复先前恢复槽。"""
            for 下标 in range(len(自身._环境们)-1,-1,-1):#自后向前
                if 自身._环境们[下标] is 环境:#身份匹配
                    自身._环境们.pop(下标)#移除环境
                    break#结束环境
            if 自身._已恢复 is None: 自身._已恢复=恢复已恢复#恢复先前恢复槽
            移除()#卸折叠项

        恢复覆盖=自身._覆盖#保存覆盖
        恢复已恢复=自身._已恢复#保存恢复槽
        自身._覆盖=None#清覆盖
        自身._已恢复=None#清恢复槽
        try:#执行回调
            结果=回调(*参数)#调用
        except BaseException:#同步抛错
            自身._覆盖=恢复覆盖#恢复覆盖
            卸边界()#卸边界
            raise#再抛
        自身._覆盖=恢复覆盖#恢复覆盖
        if not 是否thenable(结果):#同步结果
            卸边界()#立即卸边界
            return 结果#返回
        try:#挂结算清理
            if 原生then is not None:#有原生then
                原生then(结果,卸边界,卸边界)#结算时卸边界
            else:#无则挂属性then
                结果.then(卸边界,卸边界)#结算时卸边界
        except Exception:#品牌promise可能暴露失败
            卸边界()#立即卸
        return 结果#返回thenable

    def getStore(自身):#读当前存储
        """按槽序解析当前存储。"""
        if 自身._覆盖 is not None: return 自身._覆盖['store']#覆盖优先
        if 自身._已恢复 is not None: return 自身._已恢复['store']#其次恢复槽
        if len(自身._环境们)>0: return 自身._环境们[-1]['store']#最内环境
        if len(自身._条目们)>0: return 自身._条目们[-1]['store']#折叠栈顶
        return None#无

    def exit(自身,回调,*参数):#退出存储运行
        """以无存储运行回调。"""
        return 自身.run(None,回调,*参数)#以None跑

    def enterWith(自身,存储):#持久进入
        """进入持续到 disable 的边界。"""
        自身._条目们.append({'store':存储})#压入折叠栈

    def disable(自身):#禁用并清空
        """丢掉每个槽。"""
        自身._条目们.clear()#清空折叠栈
        自身._覆盖=None#清覆盖
        自身._环境们.clear()#清空环境
        自身._已恢复=None#清恢复槽

    @staticmethod
    def 快照全部():#全实例快照
        """复制每个活动实例的有效存储。"""
        return [{'instance':实例,'store':实例.getStore()} for 实例 in 实例们]#逐实例

    @staticmethod
    def 恢复全部(快照):#安装环境快照
        """把快照安装为其所点名每个实例的环境上下文。"""
        已装=[]#记录以便释放
        for 项 in 快照:#逐实例安装
            实例=项['instance']#实例
            槽={'store':项['store']}#新槽
            先前=实例._已恢复#先前值
            实例._已恢复=槽#发布
            已装.append({'instance':实例,'slot':槽,'before':先前})#记录

        def 释放():#释放器
            """按身份检查后恢复先前环境。"""
            for 记录 in 已装:#逐条
                if 记录['instance']._已恢复 is 记录['slot']:#仍是我们装的
                    记录['instance']._已恢复=记录['before']#恢复
        return 释放#释放器

    @staticmethod
    def 捕获上下文():#捕获有值上下文
        """复制每个活动实例的当前存储；全空时为 None。"""
        捕获=None#累积
        for 实例 in 实例们:#逐实例
            存储=实例.getStore()#读存储
            if 存储 is None: continue#跳过空
            if 捕获 is None: 捕获=[]#惰性建表
            捕获.append({'instance':实例,'store':存储})#追加
        return 捕获#可能None

    @staticmethod
    def 带上下文运行(快照,回调):#覆盖下运行
        """把捕获上下文恢复进覆盖槽后运行回调。"""
        if 快照 is None: return 回调()#无快照直接跑
        先前们=[]#记录
        for 项 in 快照:#安装覆盖
            实例=项['instance']#实例
            先前=实例._覆盖#先前覆盖
            实例._覆盖={'store':项['store']}#设覆盖
            先前们.append({'instance':实例,'before':先前})#记录
        try:#执行
            return 回调()#回调
        finally:#恢复
            for 记录 in 先前们:#还原覆盖
                记录['instance']._覆盖=记录['before']#还原

    @staticmethod
    def 活动实例们():#活动实例列表
        """每个活动实例。"""
        return list(实例们)#拷贝为数组

    @staticmethod
    def bind(回调):#绑定上下文
        """把回调绑定到当前上下文。"""
        return 绑定异步上下文(回调)#委托

    @staticmethod
    def snapshot():#延迟恢复工厂
        """匹配 Node 静态面的快照辅助。"""
        快照=异步本地存储.捕获上下文()#此刻捕获
        def 恢复器(回调):#返回恢复器
            """在捕获上下文中运行。"""
            return 异步本地存储.带上下文运行(快照,回调)#恢复
        return 恢复器#交回

def 捕获异步上下文():#捕获有值上下文
    """复制每个活动实例的当前存储。"""
    return 异步本地存储.捕获上下文()#委托静态

def 在异步上下文运行(快照,回调):#覆盖下运行
    """把捕获上下文恢复进覆盖槽后运行回调。"""
    return 异步本地存储.带上下文运行(快照,回调)#委托静态

def 绑定异步上下文(回调):#绑定回调
    """此刻捕获当前上下文，并在每次后续调用周围恢复。"""
    快照=捕获异步上下文()#捕获
    if 快照 is None: return 回调#无上下文原样
    def 已绑定(*参数):#包装
        """恢复后调用。"""
        def 调用():#在快照下调用
            """调用原回调。"""
            return 回调(*参数)#调用
        return 在异步上下文运行(快照,调用)#包装
    return 已绑定#断言同型

def 在异步上下文根运行(回调):#根上下文运行
    """在根处运行回调：每个实例读 None。"""
    根=[{'instance':实例,'store':None} for 实例 in 异步本地存储.活动实例们()]#全清快照
    return 在异步上下文运行(根,回调)#覆盖下跑

def 快照全部():#暂停点快照
    """加载器 await 改写的暂停点。"""
    return 异步本地存储.快照全部()#委托

def 恢复全部(快照):#恢复点安装
    """加载器 await 改写的恢复点。"""
    return 异步本地存储.恢复全部(快照)#委托

def 快照面():#als因果.snapshot
    """暂停。"""
    return 快照全部()#暂停

def 恢复面(快照):#als因果.restore
    """恢复（丢弃释放器）。"""
    恢复全部(快照)#恢复

als因果={#ALS因果面
    'snapshot':快照面,#暂停
    'restore':恢复面,#恢复
}#als因果结束

def executionAsyncId():#执行异步id
    """不跟踪 async id；稳定 id 让记录它的调用方仍能工作。"""
    return 1#占位常量

def triggerAsyncId():#触发异步id
    """亦不跟踪 trigger id。"""
    return 0#占位常量

def createHook(*位置参数,**关键字参数):#创建钩子（不可用）
    """无法创建异步钩子：worker 中无异步资源跟踪。"""
    raise Exception('web-preview: node:async_hooks.createHook is not available in the worker host')#响亮失败

AsyncResource=未实现失败('node:async_hooks','AsyncResource')#未实现失败
AsyncLocalStorage=异步本地存储#Node面别名
__snapshotAll=快照全部#变换器面
__restoreAll=恢复全部#变换器面
alsCausality=als因果#英文别名
__esModule=True#ES模块互操作标记

default={#默认导出
    'AsyncLocalStorage':异步本地存储,'AsyncResource':AsyncResource,#类
    'executionAsyncId':executionAsyncId,'triggerAsyncId':triggerAsyncId,'createHook':createHook,#其余
}#默认导出结束
