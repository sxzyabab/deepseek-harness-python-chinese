"""jsdom slot 测试运行时：Cordis Context、SlotRegistry、ui-session 与 UI 渲染器。

对齐上游 `client-runtime/src/index.ts`。公开面仅中文名。
无真 React：稳定器用同步调用；渲染结果为结构字典。
"""
from ...依赖 import cordis#外部依赖胶水
from ...客户端.ui_渲染器.客户端 import 槽登记表,创建槽渲染器#槽登记与渲染器
from ...客户端.ui_渲染器.客户端.绑定选择器 import 绑定快照选择器 as 绑定渲染器快照选择器#选择器绑定
from ...客户端.ui_会话.客户端 import 应用 as 应用UI会话,注入 as UI会话注入#ui-session
from .快照 import DOM快照序列化器,注册DOM快照序列化器#序列化器
from .会话 import 夹具会话,测试会话#会话替身
from .工作区 import 测试工作区#工作区替身
from .设置作用域 import 桩设置作用域#设置作用域桩
from .设置远程 import 脚本化设置远程#脚本化 settings
from .远程 import 测试远程,远程错误#Remote 替身
from .夹具 import 聊天快照,对话快照,会话快照,工作区快照#fixture 工厂
from .翻译 import 制作翻译#translate 桩
from .语言环境 import 用钉住浏览器语言#语言钉住

上下文类=cordis.Context#Cordis 上下文
注入解析=getattr(cordis,'Inject',None)#Inject 解析器

__all__=[#仅中文公开名
    '绑定快照选择器','创建槽渲染器','测试根','槽测试运行时',
    'DOM快照序列化器','注册DOM快照序列化器','夹具会话','测试会话',
    '桩设置作用域','脚本化设置远程','测试工作区','测试远程','远程错误',
    '聊天快照','对话快照','会话快照','工作区快照','制作翻译','用钉住浏览器语言',
    '名称','注入','应用',
]#公开面结束

名称='client-runtime-test'#插件名
注入=['client']#依赖
Error=Exception#错误别名

def 绑定快照选择器(源):#绑定选择器
    """把可观察源绑定到生产渲染器的选择器钩子。"""
    return 绑定渲染器快照选择器(源)#委托生产绑定

def 创建槽渲染器实例():#创建 slot 渲染器
    """创建客户端功能测试使用的生产 slot 渲染器。"""
    return 创建槽渲染器()#生产渲染器

class 拥有方属性单元:#owner-props 单元
    """自动 frame 背后的 owner-props 单元。"""

    def __init__(自身):#构造
        """空表。"""
        自身._owners={}#按键 owner
        自身._listeners=set()#订阅者
        自身._version=0#版本

    def getVersion(自身):#读版本
        """供订阅配对的快照版本。"""
        return 自身._version#版本

    def subscribe(自身,回调):#订阅
        """订阅 owner-props 变更。"""
        自身._listeners.add(回调)#加入
        return lambda:自身._listeners.discard(回调)#退订

    def set(自身,键,拥有方):#设置 owner
        """安装或替换一个键的 owner props 并通知。"""
        自身._owners[键]=拥有方#写入
        自身._version+=1#递增版本
        for 回调 in list(自身._listeners):#通知
            回调()#触发

    def entries(自身):#枚举条目
        """已供给 owner props 的键。"""
        return list(自身._owners.items())#展开为列表

class 测试根:#测试根
    """测试拥有的 root 占用者。"""

    def __init__(自身,槽们,稳定):#构造
        """记下登记表与稳定器。"""
        自身._slots=槽们#登记表
        自身._stabilize=稳定#稳定器
        自身._disposeEntry=None#根注册释放器

    def declare(自身,子们,框架):#声明根
        """注册根 frame，声明子 slot。"""
        def 注册():#act 内注册
            """注册根。"""
            自身._disposeEntry=自身._slots.register({'name':'root','children':子们},框架)#注册根
        自身._stabilize(注册)#稳定内注册

    def release(自身):#释放根
        """移除根注册。"""
        if 自身._disposeEntry is not None:#有释放器
            自身._disposeEntry()#调用
            自身._disposeEntry=None#清空

class 槽测试运行时:#slot 测试运行时
    """已组装的测试运行时。"""

    def __init__(自身,上下文,槽们):#私有构造经 create
        """组装会话/工作区替身并安装渲染器。"""
        自身.ctx=上下文#根上下文
        自身.slots=槽们#注册表
        自身._stabilizer=lambda 函数:函数()#同步稳定器
        自身.root=测试根(槽们,自身._stabilizer)#测试根
        自身.sessions=测试会话(自身._stabilizer,上下文)#会话替身
        自身.workspaces=测试工作区(自身._stabilizer)#工作区替身
        上下文.provide('sessions',自身.sessions)#提供会话
        上下文.provide('workspaces',自身.workspaces)#提供工作区
        自身._disposeWorkspaceSource=槽们.provideRoot({'hooks':{'workspaces':自身.workspaces.list}}) if hasattr(槽们,'provideRoot') else (lambda:None)#工作区源
        自身._host=None#渲染宿主
        自身._views=[]#已渲染视图
        自身._handles=[]#功能句柄
        自身._disposed=False#是否已拆除
        自身._ownerCell=拥有方属性单元()#owner 单元
        自身._autoDeclared=set()#已自动声明键
        自身._autoRootView=None#自动根视图
        渲染器=创建槽渲染器实例()#创建渲染器
        def 渲染根(宿主,拥有方属性):#渲染根
            """捕获宿主并委托生产。"""
            自身._host=宿主#捕获宿主
            return 渲染器.renderRoot(宿主,拥有方属性)#委托生产
        槽们.install({'renderRoot':渲染根})#安装渲染器

    @staticmethod
    def create():#创建运行时
        """组装运行时：真实 Context、已挂载 SlotRegistry、已安装渲染器。"""
        注册DOM快照序列化器()#注册序列化器
        上下文=上下文类()#新建上下文
        光纤=上下文.plugin(槽登记表)#挂注册表
        if hasattr(光纤,'await'):#等待激活
            光纤.await()#等待
        运行时=槽测试运行时(上下文,上下文.get('slots'))#组装
        插件光纤=上下文.plugin({'inject':list(UI会话注入),'apply':应用UI会话})#挂 ui-session
        if hasattr(插件光纤,'await'):#等待
            插件光纤.await()#等待
        return 运行时#返回

    def mount(自身,插件):#挂载功能
        """在真实 fiber 上挂载功能插件。"""
        注入表=getattr(插件,'inject',None) if not isinstance(插件,dict) else 插件.get('inject')#解析注入
        必需=[]#必需服务
        if 注入解析 is not None and 注入表 is not None:#有解析器
            必需=list(注入解析.resolve(注入表).keys()) if hasattr(注入解析,'resolve') else list(注入表 or [])#解析
        elif 注入表 is not None:#列表形
            必需=list(注入表)#列表
        缺失=[名 for 名 in 必需 if 自身.ctx.get(名) is None]#缺失服务
        if 缺失:#有缺失
            raise Error(f"mount would suspend: missing service(s) {', '.join(缺失)} — provide() them first")#英文诊断
        光纤=自身.ctx.plugin(插件)#挂插件
        自身._stabilizer(lambda:光纤.await() if hasattr(光纤,'await') else None)#稳定内等待
        已拆=[False]#是否已拆
        def 拆除():#拆除
            """幂等拆除。"""
            if 已拆[0]:#幂等
                return#结束
            已拆[0]=True#标记
            自身._stabilizer(lambda:光纤.dispose() if hasattr(光纤,'dispose') else None)#稳定内拆除
        句柄={'fiber':光纤,'dispose':拆除}#句柄
        自身._handles.append(句柄)#记账
        return 句柄#返回

    def releaseWorkspaceSource(自身):#释放工作区源
        """在挂载其生产 owner 前释放默认 Workspace 钩子。"""
        自身._disposeWorkspaceSource()#调用释放器

    def renderRoot(自身):#渲染根
        """经 ctx 级入口渲染根 slot 树。"""
        树=自身.slots.renderSlot('root',{})#渲染
        视图={'tree':树,'container':树,'unmount':lambda:None}#视图
        自身._views.append(视图)#记账
        return 视图#返回

    def declare(自身,子们):#自动声明
        """在自动生成的根 frame 下声明子 slot。"""
        for 键 in 子们:#记录键
            自身._autoDeclared.add(键)#记录
        单元=自身._ownerCell#owner 单元
        def 自动框架(属性):#自动 frame
            """订阅 owner 单元并渲染条目。"""
            单元.subscribe(lambda:None)#订阅（触发版本读）
            单元.getVersion()#读版本
            渲染槽=属性['renderSlot'] if isinstance(属性,dict) else 属性.renderSlot#渲染函数
            return [渲染槽(键,拥有方) for 键,拥有方 in 单元.entries()]#键控渲染
        自身.root.declare(子们,自动框架)#注册根

    def renderSlot(自身,键,拥有方):#渲染单 slot
        """用其 owner props 渲染一个已声明 slot。"""
        if 键 not in 自身._autoDeclared:#未声明
            raise Error(f"renderSlot('{键}') without declare() — declare the key first (or use root.declare for a custom frame)")#英文诊断
        def 安装(下一批):#安装 owner
            """写入单元。"""
            自身._ownerCell.set(键,下一批)#写入
        安装(拥有方)#首次安装
        if 自身._autoRootView is None:#惰性挂根
            自身._autoRootView=自身.renderRoot()#挂根
        容器=自身._autoRootView.get('container')#容器
        return {'container':容器,'view':容器,'update':安装}#局部视图

    def storeOf(自身,键,作用域键=None):#解析 store
        """解析渲染器会交给 slot 组件的 store 实例。"""
        if 自身._host is None:#无宿主
            raise Error('storeOf before renderRoot() — the host face exists only inside the installed renderer')#英文诊断
        条目们=自身._host.entriesOf(键)#条目
        if not 条目们:#无登记
            raise Error(f"storeOf('{键}'): no registration on the ledger")#英文诊断
        条目=条目们[0]#首条目
        作用域绑定=None if 作用域键 is None else (自身._host.scope('session').resolve(作用域键) if 自身._host.scope('session') else None)#作用域绑定
        if 作用域键 is not None and 作用域绑定 is None:#作用域缺失
            raise Error(f"storeOf('{键}'): no live Session binding for '{作用域键}'")#英文诊断
        实例=自身._host.storeOf(条目,作用域绑定)#取实例
        if 实例 is None:#无 store
            raise Error(f"storeOf('{键}'): the entry declares no store")#英文诊断
        return 实例#返回

    def flush(自身):#冲刷
        """冲刷挂起的账本/store 通知。"""
        自身._stabilizer(lambda:None)#空趟

    def dispose(自身):#拆除
        """拆除运行时。"""
        if 自身._disposed:#幂等
            return#结束
        自身._disposed=True#标记
        自身._autoRootView=None#清空自动根
        while 自身._views:#卸视图
            自身._views.pop().get('unmount',lambda:None)()#卸
        while 自身._handles:#拆功能
            自身._handles.pop()['dispose']()#拆
        自身.root.release()#释根
        自身.sessions.disposeScopes()#拆作用域

def 应用(上下文对象):#测试支持入口
    """客户端运行时由规格直接组装，无默认挂载面。"""
    return#空 apply

apply=应用#入口
SlotTestRuntime=槽测试运行时#上游名
TestRoot=测试根#上游名
createSlotRenderer=创建槽渲染器实例#上游名
bindSnapshotSelector=绑定快照选择器#上游名
