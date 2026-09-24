import builtins#localStorage
from ...依赖 import cordis#外部依赖胶水
from ...客户端.ui_渲染器.客户端 import 槽登记表,创建槽渲染器#槽登记与渲染器
from ...客户端.ui_渲染器.客户端.绑定选择器 import 绑定快照选择器 as 绑定渲染器快照选择器#选择器绑定
from ...客户端.ui_会话.客户端 import 应用 as 应用UI会话,依赖 as UI会话依赖
from .快照 import DOM快照序列化器,注册DOM快照序列化器#序列化器
from .会话 import 夹具会话,测试会话,创建快照存储#会话替身与快照存储
from .工作区 import 测试工作区#工作区替身
from .配置表单 import 桩配置表单#配置表单桩
from .远程 import 测试远程,远程错误#Remote 替身
from .夹具 import 聊天快照,对话快照,会话快照,工作区快照#fixture 工厂
from .翻译 import 制作翻译#translate 桩
from .语言环境 import 用钉住浏览器语言#语言钉住

上下文类=cordis.上下文#Cordis 上下文
依赖解析=getattr(cordis,'Inject',None)

__all__=[#仅中文公开名
    '绑定快照选择器','创建槽渲染器','测试根','槽测试运行时',
    'DOM快照序列化器','注册DOM快照序列化器','夹具会话','测试会话',
    '桩配置表单','测试工作区','测试远程','远程错误',
    '聊天快照','对话快照','会话快照','工作区快照','制作翻译','用钉住浏览器语言',
    '名称','依赖','应用',
]

名称='client-runtime-test'
依赖=['client']

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
        自身._owners={}#按键 {owner, opts}
        自身._listeners=set()#订阅者
        自身._version=0#版本

    def getVersion(自身):#读版本
        """供订阅配对的快照版本。"""
        return 自身._version#版本

    def subscribe(自身,回调):#订阅
        """订阅 owner-props 变更。"""
        自身._listeners.add(回调)#加入
        return lambda:自身._listeners.discard(回调)#退订

    def set(自身,键,拥有方,选项=None):#设置 owner
        """安装或替换一个键的 owner props 与渲染选项并通知。"""
        自身._owners[键]={'owner':拥有方,'opts':选项}#写入
        自身._version+=1#递增版本
        for 回调 in list(自身._listeners):#通知
            回调()#触发

    def entries(自身):#枚举条目
        """已供给 owner props 的键。"""
        return list(自身._owners.items())#展开为列表

class 测试根:#测试根
    """测试拥有的 root 占用者。"""

    def __init__(自身,槽表,稳定):#构造
        """记下登记表与稳定器。"""
        自身._slots=槽表#登记表
        自身._stabilize=稳定#稳定器
        自身._disposeEntry=None#根注册释放器

    def declare(自身,子项表,框架):#声明根
        """注册根 frame，声明子 slot。"""
        def 注册():#act 内注册
            """注册根。"""
            自身._disposeEntry=自身._slots.register({'name':'root','children':子项表},框架)#注册根
        自身._stabilize(注册)#稳定内注册

    def release(自身):#释放根
        """移除根注册。"""
        if 自身._disposeEntry is not None:#有释放器
            自身._disposeEntry()#调用
            自身._disposeEntry=None#清空

class 槽测试运行时:#slot 测试运行时
    """已组装的测试运行时。"""

    def __init__(自身,上下文,槽表):#私有构造经 create
        """组装会话/工作区/远程替身并安装渲染器。"""
        自身.ctx=上下文#根上下文
        自身.slots=槽表#注册表
        自身._stabilizer=lambda 函数:函数()#同步稳定器
        自身.root=测试根(槽表,自身._stabilizer)#测试根
        自身.sessions=测试会话(自身._stabilizer,上下文)#会话替身
        自身.remote=测试远程(上下文)#远程替身
        自身.workspaces=测试工作区(自身._stabilizer)#工作区替身
        自身.panelInfo=创建快照存储({'activePanelId':None})#面板信息
        def 未桩上传(*_参数,**_关键字):#未桩上传
            """响亮失败。"""
            raise Exception('客户端测试运行时：文件上传未桩')
        自身.fileUpload={'upload':未桩上传}#文件上传桩
        上下文.提供服务('sessions',自身.sessions)#提供会话
        上下文.提供服务('workspaces',自身.workspaces)#提供工作区
        上下文.提供服务('fileUpload',自身.fileUpload)#提供上传
        自身._disposeWorkspaceSource=槽表.provideRoot({'hooks':{'workspaces':自身.workspaces.list}}) if hasattr(槽表,'provideRoot') else (lambda:None)#工作区源
        自身._disposePanelInfoSource=槽表.provideRoot({'hooks':{'panelInfo':自身.panelInfo}}) if hasattr(槽表,'provideRoot') else (lambda:None)#面板源
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
        槽表.install({'renderRoot':渲染根})#安装渲染器

    @staticmethod
    def create():#创建运行时
        """组装运行时：真实 Context、已挂载 SlotRegistry、已安装渲染器。"""
        注册DOM快照序列化器()#注册序列化器
        上下文=上下文类()#新建上下文
        纤程=上下文.启动插件(槽登记表)#挂注册表
        纤程.等待()#等待激活
        运行时=槽测试运行时(上下文,上下文.获取服务('slots'))#组装
        插件纤程=上下文.启动插件({'inject':list(UI会话依赖),'apply':应用UI会话})
        插件纤程.等待()#等待
        return 运行时#返回

    def mount(自身,插件):#挂载功能
        """在真实 fiber 上挂载功能插件。"""
        依赖表=getattr(插件,'inject',None) if not isinstance(插件,dict) else 插件.get('inject')
        必需=[]
        if 依赖解析 is not None and 依赖表 is not None:
            必需=list(依赖解析.resolve(依赖表).keys()) if hasattr(依赖解析,'resolve') else list(依赖表 or [])
        elif 依赖表 is not None:
            必需=list(依赖表)
        缺失=[名 for 名 in 必需 if 自身.ctx.获取服务(名) is None]#缺失服务
        if 缺失:#有缺失
            raise Exception(f"挂载会挂起：缺少服务 {', '.join(缺失)}，请先 provide()")
        纤程=自身.ctx.启动插件(插件)#挂插件
        def 等待激活():
            """稳定期内等待纤程激活。"""
            纤程.等待()#等待
        自身._stabilizer(等待激活)#稳定内等待
        已拆=[False]#是否已拆
        def 拆除():#拆除
            """幂等拆除。"""
            if 已拆[0]:#幂等
                return
            已拆[0]=True#标记
            def 拆除纤程():
                """稳定期内拆除纤程。"""
                纤程.拆除()#拆除
            自身._stabilizer(拆除纤程)#稳定内拆除
        句柄={'fiber':纤程,'dispose':拆除}#句柄
        自身._handles.append(句柄)#记账
        return 句柄#返回

    def releaseWorkspaceSource(自身):#释放工作区源
        """在挂载其生产 owner 前释放默认 Workspace 钩子。"""
        自身._disposeWorkspaceSource()#调用释放器

    def releasePanelInfoSource(自身):#释放面板源
        """在挂载生产 Layout owner 前释放默认 panel 钩子。"""
        自身._disposePanelInfoSource()#调用释放器

    def renderRoot(自身):#渲染根
        """经 ctx 级入口渲染根 slot 树。"""
        树=自身.slots.renderSlot('root',{})#渲染
        视图={'tree':树,'container':树,'unmount':lambda:None}#视图
        自身._views.append(视图)#记账
        return 视图#返回

    def declare(自身,子项表):#自动声明
        """在自动生成的根 frame 下声明子 slot。"""
        for 键 in 子项表:#记录键
            自身._autoDeclared.add(键)#记录
        单元=自身._ownerCell#owner 单元
        def 自动框架(属性):#自动 frame
            """订阅 owner 单元并按 scope 渲染条目。"""
            单元.subscribe(lambda:None)#订阅（触发版本读）
            单元.getVersion()#读版本
            渲染槽=属性['renderSlot'] if isinstance(属性,dict) else 属性.renderSlot#渲染函数
            会话提供者=属性['SessionProvider'] if isinstance(属性,dict) else getattr(属性,'SessionProvider',None)#会话提供者
            节点=[]#子节点
            for 键,项 in 单元.entries():#逐条
                拥有方=项['owner']#owner
                选项=项['opts']#opts
                体=渲染槽(键,拥有方,选项)#渲染体
                规格=子项表[键] if 键 in 子项表 else {}#规格
                作用域=规格['scope'] if isinstance(规格,dict) and 'scope' in 规格 else getattr(规格,'scope',None)#scope
                if 作用域=='root' or 会话提供者 is None:#根或无提供者
                    节点.append(体)#直接
                    continue#下一条
                会话=选项['session'] if isinstance(选项,dict) and 选项 is not None and 'session' in 选项 else (getattr(选项,'session',None) if 选项 is not None else None)#会话引用
                包装={'key':键,'session':会话,'children':体}#提供者属性
                if 作用域=='session-maybe':#可空会话
                    包装['empty']=lambda 体节点=体:体节点#空回退
                节点.append(会话提供者(包装) if callable(会话提供者) else 体)#包装
            return 节点#键控渲染
        自身.root.declare(子项表,自动框架)#注册根

    def renderSlot(自身,键,拥有方,选项=None):#渲染单 slot
        """用其 owner props 渲染一个已声明 slot。"""
        if 键 not in 自身._autoDeclared:#未声明
            raise Exception(f"renderSlot('{键}') without declare() — declare the key first (or use root.declare for a custom frame)")#英文诊断
        当前选项=[选项]#可变盒
        缺省选项=object()#未传选项哨兵
        def 安装(下一批,下一批选项=缺省选项):#安装 owner
            """写入单元；省略选项时保留本视图当前选项。"""
            if 下一批选项 is not 缺省选项:#显式传入
                当前选项[0]=下一批选项#更新
            自身._ownerCell.set(键,下一批,当前选项[0])#写入
        安装(拥有方,选项)#首次安装
        if 自身._autoRootView is None:#惰性挂根
            自身._autoRootView=自身.renderRoot()#挂根
        容器=自身._autoRootView.get('container')#容器
        return {'container':容器,'view':容器,'update':安装}#局部视图

    def storeOf(自身,键,会话引用=None):#解析 store
        """解析渲染器会交给 slot 组件的 store 实例。"""
        if 自身._host is None:#无宿主
            raise Exception('storeOf before renderRoot() — the host face exists only inside the installed renderer')#英文诊断
        条目列表=自身._host.entriesOf(键)#条目
        if not 条目列表:#无登记
            raise Exception(f"storeOf('{键}'): no registration on the ledger")#英文诊断
        条目=条目列表[0]#首条目
        作用域绑定=None#作用域绑定
        if 会话引用 is not None:#有会话引用
            适配=自身._host.scope('session') if hasattr(自身._host,'scope') else None#适配器
            源=适配.bindingSource(会话引用) if 适配 is not None and hasattr(适配,'bindingSource') else None#绑定源
            解析=源.getSnapshot() if 源 is not None else None#解析
            键值=解析['key'] if isinstance(解析,dict) and 'key' in 解析 else getattr(解析,'key',None) if 解析 is not None else None#key
            if 键值 is not None:#有键
                作用域绑定=解析#绑定
            if 作用域绑定 is None:#缺失
                会话标识=会话引用['sessionId'] if isinstance(会话引用,dict) and 'sessionId' in 会话引用 else getattr(会话引用,'sessionId',会话引用)#id
                raise Exception(f"storeOf('{键}'): no live Session binding for '{会话标识}'")#英文诊断
        实例=自身._host.storeOf(条目,作用域绑定)#取实例
        if 实例 is None:#无 store
            raise Exception(f"storeOf('{键}'): the entry declares no store")#英文诊断
        return 实例#返回

    def factoryOf(自身,名称):#取工厂
        """读一个已登记 Factory 定义。"""
        if 自身._host is None:#无宿主
            raise Exception('factoryOf before renderRoot()')#英文诊断
        定义=自身._host.factoryOf(名称)#取定义
        if 定义 is None:#无
            raise Exception(f"factoryOf('{名称}'): no definition")#英文诊断
        return 定义#返回

    def flush(自身):#冲刷
        """冲刷挂起的账本/store 通知。"""
        自身._stabilizer(lambda:None)#空趟

    def dispose(自身):#拆除
        """拆除运行时。"""
        if 自身._disposed:#幂等
            return
        自身._disposed=True#标记
        自身._autoRootView=None#清空自动根
        while 自身._views:#卸视图
            自身._views.pop().get('unmount',lambda:None)()#卸
        while 自身._handles:#拆功能
            自身._handles.pop()['dispose']()#拆
        自身.root.release()#释根
        自身._disposeWorkspaceSource()#释工作区源
        自身._disposePanelInfoSource()#释面板源
        自身.sessions.disposeScopes()#拆作用域
        def 拆根纤程():#拆根
            """稳定内拆根纤程。"""
            自身.ctx.纤程.拆除()#拆
        自身._stabilizer(拆根纤程)#稳定内
        存储=getattr(builtins,'localStorage',None)#本地存储
        if 存储 is not None and hasattr(存储,'clear'):#有 clear
            存储.clear()#清空

def 应用(上下文):#测试支持入口
    """客户端运行时由规格直接组装，无默认挂载面。"""
    return#空 apply

name=名称
inject=依赖
apply=应用
