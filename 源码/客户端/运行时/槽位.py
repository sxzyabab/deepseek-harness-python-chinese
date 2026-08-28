"""槽位注册表：槽位系统在纯槽位核心之上的 cordis 服务层。

对齐上游 `runtime/src/client/slots.ts`。公开面仅中文名；英文别名对齐上游与既有消费方。
ui-slots 拥有登记语义、声明账本、加载时校验与卸载级联。
本层拥有运行时部分：'slots/changed' 事件桥、经调用方 ctx.effect 的登记与声明注入、
渲染器安装约定、以及 store 实例轴（句柄 × 作用域键 → 创建/缓存）。
"""
import json#序列化注入诊断名
import threading#微任务近似
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ..ui_slots import 槽位核心#纯槽位核心

__all__=['槽位注册表','根所有者属性','根实例键']#仅中文公开名

根实例键='root'#根作用域 store 实例键（会话记录按会话 id 键控，故不碰撞）

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

class 根所有者属性:#根所有者份额
    """壳什么都不供 — 框架由 inject 组装；禁止 children。"""
    children=None#类型面禁止 children；运行时不用此字段

class 仓库轴记录:#store 轴上的一条活句柄记录
    """作用域、引用计数、已解析实例、句柄本体。"""

    def __init__(自身,作用域,句柄):#新建轴记录
        """首次挂载时 refs=1、实例表空。"""
        自身.scope=作用域#槽位作用域（协议键）
        自身.refs=1#持有该句柄的活登记数
        自身.instances={}#作用域键 → 引擎实例
        自身.handle=句柄#句柄本体（dict 不可作映射键，故旁存）

class 渲染器宿主面:#SlotRendererHost 面
    """两个对象层服务都挂上之后建造一次；locale 为活 getter。"""

    def __init__(自身,注册表,会话们,工作区们):#绑死会话与工作区，locale 活读
        """缓存除 locale 外的全部宿主能力。"""
        自身._注册表=注册表#槽位注册表
        自身._核心=注册表._核心#纯核心
        自身.sessions={'list':会话们.list,'provideInfo':会话们.currentProvideInfo}#会话面（协议键）
        自身.workspaces={'list':工作区们.list}#工作区列表（协议键）

    def subscribe(自身,键,回调):#订阅登记变更
        """委托核心 subscribe。"""
        return 自身._核心.订阅(键,回调)#退订器

    def getVersion(自身,键):#读版本
        """委托核心 getVersion。"""
        return 自身._核心.版本(键)#版本号

    def entriesOf(自身,键):#读条目台账
        """委托核心 entries。"""
        return 自身._核心.条目们(键)#条目

    def entriesOfSlot(自身,键):#读胜出条目
        """委托核心 entriesOfSlot。"""
        return 自身._核心.槽位条目们(键)#胜者

    def reportEntryError(自身,键,条目,错误,信息):#报告条目崩溃
        """委托核心 reportEntryError。"""
        自身._核心.报告条目错误(键,条目,错误,信息)#同步报告

    def specOf(自身,键):#动态规格
        """委托核心 specDynamic。"""
        return 自身._核心.动态规格(键)#规格或 None

    def isLive(自身,条目):#条目是否仍活
        """委托核心 isLive。"""
        return 自身._核心.仍存活(条目)#是否活着

    def storeOf(自身,条目,作用域键):#解析 store 实例
        """条目无 store 则缺席；否则经注册表解析。"""
        仓库=取字段(条目,'store')#句柄
        if 仓库 is None:#无 store
            return None#缺席
        return 自身._注册表.解析仓库(仓库,作用域键)#实例

    @property
    def locale(自身):#活 locale 面
        """安装光纤寿命上的 locale；不得捕获死面。"""
        return 自身._注册表._本地化#当前面或 None

class 槽位注册表(服务):#槽位系统的 cordis 服务层
    """与槽位核心的拆分见模块文档。服务名协议键 'slots'。"""

    def __init__(自身,上下文):#绑定服务
        """构造核心、实例轴，并把核心变更桥到 'slots/changed'。"""
        super().__init__(上下文,'slots')#服务名 slots
        自身._核心=槽位核心()#纯核心
        自身._仓库们={}#id(句柄) → 仓库轴记录
        自身._渲染器=None#已安装渲染器
        自身._本地化=None#已安装 locale 面
        自身._宿主=None#缓存的宿主面
        def 桥接变更(键):#核心变更 → 事件
            """同步发出 slots/changed。"""
            上下文.emit('slots/changed',键)#事件桥
        自身._核心.变更时(桥接变更)#挂上

    def 登记(自身,选项,组件):#唯一登记 API
        """经调用方 ctx.effect 拆除；工厂铸造、登记者戳、实例轴记账见 _真正登记。

        必须是实例方法（非冻结闭包），以便 cordis 代理把 ctx 绑到调用方光纤。
        @param 选项 - 擦除后的登记选项（name/children/store/…）。
        @param 组件 - 贡献组件。
        @returns 幂等 disposer。
        """
        def 效应():#归调用方光纤
            """提交登记并在拆除时级联。"""
            return 自身._真正登记(选项,组件)#核心写入 + 轴记账
        拆除控制器=自身.ctx.effect(效应,'slots.register()')#effect 名
        def 同步拆除():#包成同步 disposer
            """对齐 void dispose()。"""
            拆除控制器()#拆除
        return 同步拆除#disposer

    def 注入(自身,键,回调):#声明寿命注入
        """为一条槽位的每个声明寿命安装 effect；折叠拆除后再声明会再跑。

        @param 键 - 已声明 SlotMap 键。
        @param 回调 - 创建 disposer 或可迭代 disposer（经 ctx.effect）。
        @returns 等待与活动 effect 的幂等 disposer。
        @raises 槽位已声明时，回调安装失败同步抛出。
        """
        调用方=自身.ctx#调用方上下文
        def 效应():#归调用方光纤
            """对照声明世代；永久停后不再重试。"""
            活动拆除=None#当前声明寿命的拆除
            活动世代=None#当前声明世代
            已停=False#是否永久停
            def 空退订():#订阅前占位
                """尚无声明订阅时的空拆除。"""
                return#无操作
            退订声明=空退订#声明订阅退订
            def 永久停():#永久停
                """失败调用方永久退役本注入。"""
                nonlocal 已停,活动拆除,活动世代#改封闭变量
                if 已停:#已停
                    return#幂等
                已停=True#钉住停止
                退订声明()#退订声明
                拆=活动拆除#取出活动拆除
                活动拆除=None#清活动
                活动世代=None#清世代
                if 拆 is not None:#有活动
                    拆()#拆除
            def 对照():#对照声明
                """世代未变则跳过；否则拆旧装新。"""
                nonlocal 活动拆除,活动世代#改封闭变量
                if 已停:#已停
                    return#停
                规格=自身._核心.动态规格(键)#当前规格
                世代=自身._核心.声明世代(键)#声明世代
                if 活动拆除 is not None and 活动世代==世代:#同一寿命
                    return#跳过
                拆=活动拆除#旧拆除
                活动拆除=None#先清
                活动世代=None#先清世代
                if 拆 is not None:#有旧
                    拆()#拆旧
                if 规格 is None:#声明不在
                    return#等下次
                效应名='slots.inject('+json.dumps(键)+'): declaration'#嵌套 effect 名
                拆除效应=调用方.effect(回调,效应名)#嵌套 effect
                def 包拆除():#包成同步拆除
                    """对齐 void disposeEffect()。"""
                    拆除效应()#拆除嵌套
                活动拆除=包拆除#记下
                活动世代=世代#记下世代
            def 声明变更():#声明变更
                """对照；安装失败则永久停并微任务再抛。"""
                try:#对照
                    对照()#同步对照
                except Exception as 错误:#安装失败
                    if getattr(错误,'code',None)=='INACTIVE_EFFECT':#光纤已死
                        永久停()#永久停
                        return#不再抛
                    永久停()#永久停
                    失败=错误 if isinstance(错误,Exception) else Exception(str(错误))#归一
                    def 再抛():#微任务再抛，避免吞掉
                        """对齐 queueMicrotask(() => { throw failure })。"""
                        raise 失败#再抛
                    threading.Timer(0,再抛).start()#近似微任务
            退订声明=自身._核心.订阅声明(键,声明变更)#听声明变更
            try:#首次对照
                对照()#同步跑
            except Exception as 错误:#已声明时的安装失败
                永久停()#永久停
                raise 错误#同步抛给调用方
            return 永久停#effect 拆除即永久停
        拆除控制器=调用方.effect(效应,'slots.inject('+json.dumps(键)+')')#effect 名
        def 同步拆除():#包成同步 disposer
            """对齐 void disposeController()。"""
            拆除控制器()#拆除
        return 同步拆除#disposer

    def 安装(自身,渲染器):#安装壳渲染器
        """启动一次：第二次安装抛错；经调用方 ctx.effect，光纤卸载卸掉渲染器。

        @param 渲染器 - 实现 SlotRenderer 的出口机械。
        """
        if 自身._渲染器 is not None:#已安装
            raise Exception('slot renderer already installed (install() is boot-once)')#禁止二次
        def 效应():#归调用方光纤
            """装上并在拆除时只卸自己装的。"""
            自身._渲染器=渲染器#装上
            def 拆除():#拆除
                """身份匹配才清。"""
                if 自身._渲染器 is 渲染器:#仍是自己
                    自身._渲染器=None#卸掉
            return 拆除#拆除器
        自身.ctx.effect(效应,'slots.install()')#effect 名

    def 安装本地化(自身,面):#安装 locale 面
        """支撑 t 标准座位；与渲染器同一套启动一次纪律。

        @param 面 - 命名空间绑定器 + 修订可观察源。
        """
        if 自身._本地化 is not None:#已安装
            raise Exception('locale face already installed (installLocale() is boot-once)')#禁止二次
        def 效应():#归调用方光纤
            """装上并在拆除时只卸自己装的。"""
            自身._本地化=面#装上
            def 拆除():#拆除
                """身份匹配才清。"""
                if 自身._本地化 is 面:#仍是自己
                    自身._本地化=None#卸掉
            return 拆除#拆除器
        自身.ctx.effect(效应,'slots.installLocale()')#effect 名

    def 渲染槽(自身,键,所有者):#唯一 ctx 级渲染入口
        """壳只渲染 'root'；三条守卫大声失败，无回退。

        @param 键 - 必须是 'root'。
        @param 所有者 - 根条目所有者份额（壳供应 {}）。
        @returns 渲染出的根树。
        """
        if 键!='root':#不是根
            raise Exception('ctx-level renderSlot only renders \'root\' (got "'+str(键)+'"); child slots render through the component props face')#大声失败
        if 自身._渲染器 is None:#尚未安装
            raise Exception("slot renderer not installed — boot must call ctx.slots.install(createSlotRenderer()) before rendering 'root'")#启动顺序
        if len(自身._核心.条目们('root'))==0:#根没有条目
            raise Exception("'root' has no registration — a layout entry must register into 'root' before the shell renders it")#缺布局
        return 自身._渲染器.renderRoot(自身.宿主面(),所有者)#交给渲染器

    def 剪裁仓库作用域(自身,会话标识):#剪会话作用域
        """丢掉死去会话的按会话 store 实例；根作用域记录不动。

        @param 会话标识 - 已拆除的会话。
        """
        for 记 in list(自身._仓库们.values()):#每个活句柄
            if 记.scope!='session':#根作用域跳过
                continue#下一个
            句柄=记.handle#句柄
            实例=记.instances.get(会话标识)#已有
            if 实例 is None:#瞬时造
                创建=取字段(句柄,'create')#create
                实例=创建(会话标识)#造
            取字段(实例,'clearPersisted')()#清持久键
            记.instances.pop(会话标识,None)#丢掉实例

    def 条目们(自身,键):#读条目快照
        """渲染擦除视图；变更之间引用稳定。"""
        return 自身._核心.条目们(键)#交给核心

    def 槽位条目们(自身,键):#读胜出条目
        """每个单元格按优先级的第一条活着条目。"""
        return 自身._核心.槽位条目们(键)#交给核心

    def 快照(自身,根=None):#导出声明树
        """JSON 安全的槽位声明树，供只读检查。"""
        return 自身._核心.快照(根)#交给核心

    def 条目错误时(自身,回调):#听条目错误
        """边界收住的每一次渲染时条目失败；返回取消订阅。"""
        return 自身._核心.条目错误时(回调)#交给核心

    def 规格(自身,键):#读规格
        """register 声明的或内置 'root'；未声明为 None。"""
        return 自身._核心.规格(键)#交给核心

    def 订阅(自身,键,回调):#订阅变更
        """微任务批；返回取消订阅。"""
        return 自身._核心.订阅(键,回调)#交给核心

    def 版本(自身,键):#读版本
        """给 uSES 配对用的版本计数器。"""
        return 自身._核心.版本(键)#交给核心

    def _真正登记(自身,选项,组件):#委托登记路径
        """工厂铸造 + 登记者戳 + 核心写入 + 实例轴记账。"""
        原始仓库=取字段(选项,'store')#可选 store
        仓库=原始仓库() if callable(原始仓库) else 原始仓库#工厂则铸造
        登记者=取字段(选项,'registrant')#显式戳
        if 登记者 is None:#缺省取光纤名
            光纤=getattr(自身.ctx,'fiber',None)#调用方光纤
            登记者=getattr(光纤,'name',None) if 光纤 is not None else None#诊断戳
        if isinstance(选项,dict):#映射选项（消费方惯例）
            擦除=dict(选项)#浅拷贝
        else:#对象选项：抽已知键
            擦除={}#空
            for 键名 in ('name','children','store','inject','key','id','order','label','select','priority','locale','registrant'):#已知键
                if hasattr(选项,键名):#属性在场（含 0/False）
                    擦除[键名]=getattr(选项,键名)#写入
        if 仓库 is not None:#已解析句柄
            擦除['store']=仓库#覆盖
        if 登记者 is not None:#诊断戳
            擦除['registrant']=登记者#写入
        拆除=自身._核心.登记(擦除,组件)#核心写入（加载时校验先抛）
        if 仓库 is not None:#有 store
            目标规格=自身._核心.动态规格(取字段(选项,'name'))#目标规格
            作用域=取字段(目标规格,'scope')#目标作用域
            自身._获得(仓库,作用域)#轴上加引用
        已拆=False#幂等拆除
        def 条目拆除():#条目 disposer
            """核心拆除 + 轴上减引用。"""
            nonlocal 已拆#改封闭
            if 已拆:#已拆
                return#幂等
            已拆=True#钉住
            拆除()#核心拆除
            if 仓库 is not None:#有 store
                自身._释放(仓库)#轴上减引用
        return 条目拆除#disposer

    def 宿主面(自身):#渲染器宿主面
        """建造一次并缓存；按会话 provide 仍惰性。"""
        if 自身._宿主 is not None:#已缓存
            return 自身._宿主#返回
        会话们=自身.ctx.get('sessions')#会话服务
        if 会话们 is None:#尚未挂上
            raise Exception("renderSlot('root') before the sessions service mounted — boot order puts runtime apply first")#启动顺序
        工作区们=自身.ctx.get('workspaces')#工作区服务
        if 工作区们 is None:#尚未挂上
            raise Exception("renderSlot('root') before the workspaces service mounted — boot order puts runtime apply first")#启动顺序
        自身._宿主=渲染器宿主面(自身,会话们,工作区们)#缓存
        return 自身._宿主#返回

    def 解析仓库(自身,句柄,会话标识):#解析 store 实例
        """创建或复用已登记句柄在某作用域键下的实例。"""
        记=自身._仓库们.get(id(句柄))#轴记录
        if 记 is None:#未登记
            raise Exception('store handle is not registered (entry unloaded, or the handle never went through register)')#未登记
        键=根实例键 if 记.scope=='root' else 会话标识#根用字面量，会话用 id
        if 键 is None:#会话作用域缺 id
            raise Exception(str(记.scope)+' store resolution requires a session id')#缺 id
        实例=记.instances.get(键)#已有
        if 实例 is None:#尚未创建
            创建=取字段(句柄,'create')#create
            实例=创建() if 记.scope=='root' else 创建(键)#按作用域 create
            记.instances[键]=实例#写入轴
        return 实例#返回

    def _获得(自身,句柄,作用域):#轴上加引用
        """首次挂载新建记录；跨作用域冲突已在核心抛过。"""
        标识=id(句柄)#句柄身份
        记=自身._仓库们.get(标识)#已有
        if 记 is None:#首次
            自身._仓库们[标识]=仓库轴记录(作用域,句柄)#新建
            return#结束
        记.refs+=1#再引用

    def _释放(自身,句柄):#轴上减引用
        """最后一个持有者卸载丢掉记录（实例跟着走）。"""
        标识=id(句柄)#句柄身份
        记=自身._仓库们.get(标识)#轴记录
        if 记 is None:#防御：没有则停
            return#停
        记.refs-=1#减一
        if 记.refs==0:#最后一个
            del 自身._仓库们[标识]#丢掉记录

    # 英文方法别名：对齐上游 SlotRegistry 与既有 ctx.slots.* 消费方
    register=登记#登记
    inject=注入#注入
    install=安装#安装
    installLocale=安装本地化#安装本地化
    renderSlot=渲染槽#渲染槽
    pruneStoreScope=剪裁仓库作用域#剪裁仓库作用域
    entries=条目们#条目们
    entriesOfSlot=槽位条目们#槽位条目们
    snapshot=快照#快照
    onEntryError=条目错误时#条目错误时
    spec=规格#规格
    subscribe=订阅#订阅
    getVersion=版本#版本
    hostFace=宿主面#宿主面
    resolveStore=解析仓库#解析仓库

SlotRegistry=槽位注册表#上游类名别名
RootOwnerProps=根所有者属性#上游类型别名
ROOT_INSTANCE_KEY=根实例键#上游常量别名
