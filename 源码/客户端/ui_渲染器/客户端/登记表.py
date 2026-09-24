from ...ui_槽位 import 槽位登记表,过期授权错误#纯登记表与过期授权
from ....依赖 import cordis#外部依赖胶水
from ..错误 import 槽装配错误#独占持久装配失败
from .绑定 import 槽组装错误,可观察源#本包组装失败与可观察源

服务=cordis.服务#Cordis 服务基类

__all__=['槽登记表','槽宿主面','标准钩子属性名','根实例键','根拥有方属性']#仅中文公开名

根实例键='root'#根实例键
根拥有方属性=dict#禁止 children 透传的根拥有方份额形状

def 标准钩子属性名(名称):
    """`session` → `useSession`。"""
    if 名称=='':#空
        return 'use'#仅前缀
    return 'use'+名称[0].upper()+名称[1:]#首字母大写加 use

def 恒等属性名(名):
    """prop 名原样。"""
    return 名#原样

def 拷贝唯一(种类,目标,值表,最终属性,属性名映射):
    """重名则抛。值表为 dict。"""
    if 值表 is None:#无来源
        return#跳过
    for 名称,值 in 值表.items():#逐项
        属性名=属性名映射(名称)#最终 prop 名
        if 属性名 in 最终属性:#重名
            raise 槽组装错误("duplicate root standard "+种类+" '"+str(名称)+"' at prop '"+str(属性名)+"'")#抛错
        最终属性.add(属性名)#登记
        目标[名称]=值#写入

def 要求作用域键(定义,绑定):
    """非根工厂 store 解析必须有会话键。定义为 dict。"""
    if 绑定 is None:#缺绑定
        raise 槽组装错误(str(定义['scope'])+' factory store resolution requires a session id')#抛错
    return 绑定['key']#返回键

def 空拆除():
    """空 disposer。"""
    return None#无

class 槽宿主面:
    """域中立宿主 API；locale / 适配器经登记表活读。"""
    def __init__(自身,登记表):
        """记下登记表。"""
        自身._登记表=登记表#服务
        自身.root=登记表._rootSource#根源 dict
        自身.scopeRevision=登记表._scopeRevisionSource#版本源 dict

    def subscribe(自身,键,回调):
        """订变更。"""
        return 自身._登记表._core.订阅(键,回调)#订

    def getVersion(自身,键):
        """读版本。"""
        return 自身._登记表._core.版本(键)#版本

    def entriesOf(自身,键):
        """条目快照。"""
        return 自身._登记表._core.取条目列表(键)#条目

    def entriesOfSlot(自身,键):
        """胜出条目。"""
        return 自身._登记表._core.取槽位条目(键)#胜出

    def reportEntryError(自身,键,条目,错误,信息):
        """报告崩溃。"""
        自身._登记表._core.报告条目错误(键,条目,错误,信息)#报告

    def reportFactoryError(自身,名,登记,错误):
        """报告工厂崩溃。"""
        自身._登记表._core.报告工厂错误(名,登记,错误)#报告

    def specOf(自身,键):
        """动态规范。"""
        return 自身._登记表._core.动态规格(键)#规格

    def isLive(自身,条目):
        """条目是否仍在台账。"""
        return 自身._登记表._core.仍存活(条目)#活

    def storeOf(自身,条目,作用域绑定):
        """解析条目 store。条目为 dict。"""
        if 'store' not in 条目:#无
            return None#无
        存储=条目['store']#句柄
        if 存储 is None:#空
            return None#无
        return 自身._登记表.解析存储(存储,作用域绑定)#解析

    def factoryStoreOf(自身,定义,作用域绑定,出现):
        """解析工厂 store。定义为 dict。"""
        return 自身._登记表.解析工厂存储(定义,作用域绑定,出现)#解析

    def retainFactoryOccurrence(自身,定义,出现):
        """保留工厂出现。定义为 dict。"""
        return 自身._登记表.保留工厂出现(定义,出现)#保留

    def subscribeFactory(自身,名,回调):
        """订工厂定义寿命。"""
        return 自身._登记表._core.订阅工厂(名,回调)#订

    def getFactoryVersion(自身,名):
        """工厂版本。"""
        return 自身._登记表._core.工厂版本(名)#版本

    def factoryOf(自身,名):
        """取工厂定义。"""
        return 自身._登记表._core.取工厂(名)#定义

    def isFactoryLive(自身,定义):
        """工厂定义是否仍登记。定义为 dict。"""
        return 自身._登记表._core.工厂仍存活(定义)#活

    def scope(自身,作用域):
        """取已安装适配器。session-maybe 与 session 共用。"""
        名='session' if 作用域=='session-maybe' else 作用域#名
        表=自身._登记表._scopes#适配器表
        return 表[名] if 名 in 表 else None#适配器

    def locale(自身):
        """已安装 locale 面；未装为 None。"""
        return 自身._登记表._locale#面

class 槽登记表(服务):
    """与 SlotCore 的分工见模块文档。"""
    def __init__(自身,上下文):
        """服务名 slots；桥接变更事件。"""
        super().__init__(上下文,'slots')#服务名 slots
        自身._core=槽位登记表()#纯登记表
        自身._stores={}#句柄轴
        自身._factoryStores={}#工厂 store 轴
        自身._storeScopeOwners={}#作用域拥有方
        自身._renderer=None#已安装渲染器
        自身._locale=None#已安装 locale 面
        自身._host=None#缓存宿主面
        自身._rootContributions=[]#根贡献名册
        自身._rootListeners=set()#根绑定订阅者
        自身._rootBinding={'key':None,'hooks':{},'keyedHooks':{},'props':{}}#当前根绑定
        def 取根快照():
            """读根绑定。"""
            return 自身._rootBinding#快照
        自身._rootSource=可观察源(取根快照,自身._订根)#根可观察源
        自身._scopes={}#严格作用域适配器
        自身._scopeRevision=0#作用域名册版本
        自身._scopeListeners=set()#作用域订阅者
        def 取作用域修订():
            """读版本。"""
            return 自身._scopeRevision#版本
        自身._scopeRevisionSource=可观察源(取作用域修订,自身._订作用域修订)#版本可观察源
        def 桥接变更(键):
            """转发 slots/changed。"""
            上下文.广播('slots/changed',键)#桥
        自身._core.变更时(桥接变更)#桥接变更事件

    def _订根(自身,监听):
        """返回退订。"""
        自身._rootListeners.add(监听)#登记
        def 退订():
            """拿掉监听。"""
            自身._rootListeners.discard(监听)#退
        return 退订#退订

    def _订作用域修订(自身,监听):
        """返回退订。"""
        自身._scopeListeners.add(监听)#登记
        def 退订():
            """拿掉监听。"""
            自身._scopeListeners.discard(监听)#退
        return 退订#退订

    def register(自身,选项,组件):
        """经调用方副作用拆除。选项为 dict。"""
        def 寿命():
            """登记并交 fiber 拆除。"""
            return 自身._登记(选项,组件)#拆除器
        return 自身.ctx.副作用(寿命,'slots.register()')#经纤程拆除

    def registerFactory(自身,选项,组件):
        """经调用方副作用拆除。选项为 dict。"""
        def 寿命():
            """登记工厂并交 fiber 拆除。"""
            return 自身._登记工厂(选项,组件)#拆除器
        return 自身.ctx.副作用(寿命,'slots.registerFactory()')#经纤程拆除

    def inject(自身,键,回调):
        """声明已存在时回调同步跑；否则等声明后跑。"""
        上下文=自身.ctx#调用方上下文
        def 空退订():
            """声明订阅占位。"""
            return None#无
        def 控制器寿命():
            """对齐声明代次；失败永久停用。"""
            活跃=[None]#当前声明寿命 disposer
            活跃代=[None]#对应声明代次
            已停=[False]#永久停用
            退订箱=[空退订]#声明订阅退订

            def 停用():
                """失败调用方永久退役注入。"""
                if 已停[0] is True:#已停
                    return
                已停[0]=True#标记停用
                退订箱[0]()#退订声明
                拆除=活跃[0]#当前 disposer
                活跃[0]=None#清空
                活跃代[0]=None#清空代次
                if 拆除 is not None:#有
                    拆除()#执行清理

            def 对齐():
                """同代次复用。"""
                if 已停[0] is True:#已停
                    return#跳过
                规格=自身._core.动态规格(键)#动态规范
                代次=自身._core.声明世代(键)#声明代次
                if 活跃[0] is not None and 活跃代[0]==代次:#同代次
                    return#复用
                旧=活跃[0]#旧 disposer
                活跃[0]=None#清空
                活跃代[0]=None#清空代次
                if 旧 is not None:#有旧
                    旧()#卸旧
                if 规格 is None:#声明已去
                    return
                拆除效果=上下文.副作用(回调,'slots.inject('+repr(键)+'): declaration')#嵌套副作用
                def 卸声明效果():
                    """卸嵌套 effect。"""
                    拆除效果()#卸
                活跃[0]=卸声明效果#包装 disposer
                活跃代[0]=代次#记下代次

            def 变更():
                """尝试对齐；失败停用。"""
                try:#尝试对齐
                    对齐()#对齐
                except Exception as 错误:#fiber/注入失败形态含 INACTIVE_EFFECT
                    码=None#错误码
                    try:#Cordis 错误带 code
                        码=错误.code#码
                    except AttributeError:#无 code
                        码=None#无
                    停用()#停用
                    if 码=='INACTIVE_EFFECT':#fiber 已死
                        return
                    raise#异步再抛由宿主

            退订箱[0]=自身._core.订阅声明(键,变更)#订声明
            try:#首轮对齐
                对齐()#对齐
            except Exception:#同步失败
                停用()#停用
                raise#上抛
            return 停用#控制器 disposer
        拆除控制器=上下文.副作用(控制器寿命,'slots.inject('+repr(键)+')')#诊断名
        def 对外拆除():
            """卸控制器。"""
            拆除控制器()#卸
        return 对外拆除#对外 disposer

    def install(自身,渲染器):
        """启动一次：二次安装抛错。渲染器为对象。"""
        if 自身._renderer is not None:#已装
            raise 槽组装错误('slot renderer already installed (install() is boot-once)')#禁止二次
        def 寿命():
            """挂上；拆卸仅卸自己。"""
            自身._renderer=渲染器#挂上
            def 拆卸():
                """仅卸本实例。"""
                if 自身._renderer is 渲染器:#仍是自己
                    自身._renderer=None#卸
            return 拆卸#拆卸
        自身.ctx.副作用(寿命,'slots.install()')#诊断名

    def installLocale(自身,面):
        """与渲染器安装同为启动一次纪律。面为对象。"""
        if 自身._locale is not None:#已装
            raise 槽组装错误('locale face already installed (installLocale() is boot-once)')#禁止二次
        def 寿命():
            """挂上；拆卸仅卸自己。"""
            自身._locale=面#挂上
            def 拆卸():
                """仅卸本实例。"""
                if 自身._locale is 面:#仍是自己
                    自身._locale=None#卸
            return 拆卸#拆卸
        自身.ctx.副作用(寿命,'slots.installLocale()')#诊断名

    def provideRoot(自身,贡献):
        """钩子名必须全局唯一。贡献为 dict。"""
        def 寿命():
            """挂上后重建；失败回滚。"""
            自身._rootContributions.append(贡献)#挂上
            try:#重建
                自身.重建根绑定()#重发根绑定
            except Exception:#失败回滚
                自身._rootContributions.pop()#弹出
                raise#上抛
            def 拆卸():
                """卸下再重建。"""
                try:#定位
                    索引=自身._rootContributions.index(贡献)#定位
                except ValueError:#已不在
                    return#忽略
                自身._rootContributions.pop(索引)#卸下
                自身.重建根绑定()#再重建
            return 拆卸#返回拆卸
        拆除=自身.ctx.副作用(寿命,'slots.provideRoot()')#诊断名
        def 对外拆除():
            """卸贡献。"""
            拆除()#卸
        return 对外拆除#对外 disposer

    def installScope(自身,作用域,适配器):
        """严格作用域；可选对偶经同一适配器解析。适配器为 dict。"""
        if 作用域 in 自身._scopes:#已有
            raise 槽组装错误("slot scope '"+str(作用域)+"' already has an adapter")#禁止二次
        def 寿命():
            """挂上并发版本。"""
            自身._scopes[作用域]=适配器#挂上
            自身.发布作用域修订()#发版本
            def 拆卸():
                """仍是自己则卸下。"""
                if 作用域 in 自身._scopes and 自身._scopes[作用域] is 适配器:#仍是自己
                    del 自身._scopes[作用域]#卸下
                    自身.发布作用域修订()#发版本
            return 拆卸#返回拆卸
        自身.ctx.副作用(寿命,'slots.installScope('+repr(作用域)+')')#诊断名

    def bindStoreScope(自身,绑定):
        """清理只丢内存实例；持久属作用域键。绑定为 dict。"""
        键=绑定['key']#作用域键
        上下文=绑定['ctx']#拥有 Context
        当前=自身._storeScopeOwners[键] if 键 in 自身._storeScopeOwners else None#当前拥有方
        if 当前 is 上下文:#同代次
            return#跳过
        if 当前 is not None:#换代
            自身.释放存储作用域(键)#先丢掉上一代内存实例
        自身._storeScopeOwners[键]=上下文#记下最新代
        def 寿命():
            """作用域死亡清理。"""
            def 清理():
                """清拥有方并释放实例。"""
                if 键 not in 自身._storeScopeOwners:#无
                    return#忽略
                if 自身._storeScopeOwners[键] is not 上下文:#已被更新代接管
                    return#忽略
                del 自身._storeScopeOwners[键]#清拥有方
                自身.释放存储作用域(键)#仅释内存实例
            return 清理#返回清理
        上下文.副作用(寿命,'slots: store scope '+str(键))#诊断名

    def renderSlot(自身,键,拥有方):
        """仅渲染 root；三道守卫响亮失败。"""
        if 键!='root':#非 root
            raise 槽组装错误('ctx-level renderSlot only renders \'root\' (got "'+str(键)+'"); child slots render through the component props face')#抛错
        if 自身._renderer is None:#未安装
            raise 槽组装错误("slot renderer not installed — boot must call ctx.slots.install(createSlotRenderer()) before rendering 'root'")#抛错
        if len(自身._core.取条目列表('root'))==0:#无登记
            raise 槽组装错误("'root' has no registration — a layout entry must register into 'root' before the shell renders it")#抛错
        return 自身._renderer.renderRoot(自身.宿主面(),拥有方)#渲染根

    def entries(自身,键):
        """委托核心。"""
        return 自身._core.取条目列表(键)#委托核心

    def entriesOfSlot(自身,键):
        """委托核心。"""
        return 自身._core.取槽位条目(键)#委托核心

    def snapshot(自身,根=None):
        """委托核心。"""
        return 自身._core.快照(根)#委托核心

    def onEntryError(自身,回调):
        """委托核心；登记可为条目或工厂。"""
        return 自身._core.条目错误时(回调)#委托核心

    def spec(自身,键):
        """查规范。"""
        return 自身._core.规格(键)#委托核心

    def subscribe(自身,键,回调):
        """订变更。"""
        return 自身._core.订阅(键,回调)#委托核心

    def getVersion(自身,键):
        """读版本。"""
        return 自身._core.版本(键)#委托核心

    def _登记(自身,选项,组件):
        """工厂铸造 + registrant 戳 + 核心写入 + 实例轴记账。选项为 dict。"""
        存储=选项['store'] if 'store' in 选项 else None#store
        if 存储 is not None and callable(存储):#工厂；上游 typeof === 'function'
            存储=存储()#铸造
        登记方=选项['registrant'] if 'registrant' in 选项 else None#登记方戳
        if 登记方 is None:#缺
            try:#可选 fiber 诊断戳
                纤=自身.ctx.纤程#纤程
            except AttributeError:#无
                纤=None#无
            登记方=纤.name if 纤 is not None else None#诊断戳
        擦除=dict(选项)#擦除选项
        if 存储 is not None:#有
            擦除['store']=存储#可解析句柄
        if 登记方 is not None:#有
            擦除['registrant']=登记方#诊断戳
        拆除=自身._core.登记(擦除,组件)#核心写入
        if 存储 is not None:#有 store
            规格=自身._core.动态规格(擦除['name'])#取作用域
            作用域=规格['scope'] if 规格 is not None and 'scope' in 规格 else None#作用域
            自身._获取(存储,作用域)#轴记账
        已卸=[False]#幂等门闩
        def 拆除器():
            """幂等卸核心并释引用。"""
            if 已卸[0] is True:#已卸
                return
            已卸[0]=True#标记
            拆除()#卸核心
            if 存储 is not None:#有
                自身._拆除(存储)#释引用
        return 拆除器#返回

    def _登记工厂(自身,选项,组件):
        """核心写入 + 共享轴或工厂轴记账。选项为 dict。"""
        登记方=None#登记方戳
        try:#可选 fiber 诊断戳
            纤=自身.ctx.纤程#纤程
        except AttributeError:#无
            纤=None#无
        if 纤 is not None:#有
            登记方=纤.name#诊断戳
        擦除=dict(选项)#擦除选项
        if 登记方 is not None:#有
            擦除['registrant']=登记方#诊断戳
        拆除=自身._core.登记工厂(擦除,组件)#核心写入
        定义=自身._core.取工厂(选项['name'])#取定义
        if 定义 is None:#消失
            raise 槽组装错误('slot factory "'+str(选项['name'])+'" disappeared during registration')#抛错
        存储=定义['store'] if 'store' in 定义 else None#store
        if 存储 is not None and callable(存储) is False:#共享句柄
            自身._获取(存储,定义['scope'])#轴记账
        elif callable(存储):#独占工厂
            自身._factoryStores[定义]={'occurrences':{},'mounted':{}}#建工厂轴
        已卸=[False]#幂等门闩
        def 拆除器():
            """幂等卸核心并释轴。"""
            if 已卸[0] is True:#已卸
                return
            已卸[0]=True#标记
            拆除()#卸核心
            自身._factoryStores.pop(定义,None)#删工厂轴
            if 存储 is not None and callable(存储) is False:#共享句柄
                自身._拆除(存储)#释引用
        return 拆除器#返回

    def 宿主面(自身):
        """构建一次域中立宿主面。"""
        if 自身._host is not None:#复用
            return 自身._host#缓存
        自身._host=槽宿主面(自身)#对象面
        return 自身._host#返回

    def 重建根绑定(自身):
        """校验并原子发布当前根贡献名册。"""
        钩子={}#钩子表
        键控={}#键控表
        属性={}#prop 表
        最终属性=set()#去重集
        for 贡献 in 自身._rootContributions:#逐贡献
            拷贝唯一('hook',钩子,贡献['hooks'] if 'hooks' in 贡献 else None,最终属性,标准钩子属性名)#拷钩子
            拷贝唯一('keyed hook',键控,贡献['keyedHooks'] if 'keyedHooks' in 贡献 else None,最终属性,标准钩子属性名)#拷键控
            拷贝唯一('prop',属性,贡献['props'] if 'props' in 贡献 else None,最终属性,恒等属性名)#拷 prop
        自身._rootBinding={'key':None,'hooks':钩子,'keyedHooks':键控,'props':属性}#发布
        for 监听 in list(自身._rootListeners):#通知订阅者
            try:#隔离失败
                监听()#回调
            except Exception as 错误:#订阅者抛错
                print('根标准源订阅者失败:',错误)#打印

    def 发布作用域修订(自身):
        """在映射已权威后发布一次已安装作用域名册过渡。"""
        自身._scopeRevision+=1#递增
        for 监听 in list(自身._scopeListeners):#通知
            try:#隔离失败
                监听()#回调
            except Exception as 错误:#订阅者抛错
                print('作用域适配器订阅者失败:',错误)#打印

    def 解析存储(自身,句柄,作用域绑定):
        """解析（创建或复用）已登记句柄的 store 实例。句柄为对象。"""
        记录=自身._stores[句柄] if 句柄 in 自身._stores else None#轴记录
        if 记录 is None:#未登记
            raise 槽组装错误('store handle is not registered (entry unloaded, or the handle never went through register)')#未登记
        if 记录['scope']=='root':#根作用域
            键=根实例键#根键
        else:#会话作用域
            if 作用域绑定 is None:#缺绑定
                raise 槽组装错误(记录['scope']+' store resolution requires a session id')#缺绑定
            键=作用域绑定['key']#会话键
            自身.bindStoreScope(作用域绑定)#确保寿命
        实例表=记录['instances']#实例
        实例=实例表[键] if 键 in 实例表 else None#读缓存
        if 实例 is None:#未创建
            创建=句柄.create#创建入口
            实例=创建() if 记录['scope']=='root' else 创建(键)#创建
            实例表[键]=实例#写入
        return 实例#返回

    def 解析工厂存储(自身,定义,作用域绑定,出现):
        """按出现解析工厂 store。定义为 dict。"""
        if 自身._core.工厂仍存活(定义) is False:#已死
            raise 过期授权错误('slot factory "'+str(定义['name'])+'" is not registered')#过期授权
        声明=定义['store'] if 'store' in 定义 else None#store 声明
        if 声明 is None:#无
            return None#无
        if callable(声明) is False:#共享句柄
            return 自身.解析存储(声明,作用域绑定)#走条目轴
        轴=自身._factoryStores[定义]#工厂轴
        if 定义['scope']=='root':#根
            作用域键=根实例键#根键
        else:#会话
            作用域键=要求作用域键(定义,作用域绑定)#要求会话键
        if 作用域绑定 is not None and 定义['scope']!='root':#非根有绑定
            自身.bindStoreScope(作用域绑定)#绑寿命
        出现表=轴['occurrences']#出现表
        记录=出现表[出现] if 出现 in 出现表 else None#出现记录
        if 记录 is None:#首遇
            句柄=声明()#铸造句柄
            规格=句柄.spec#规格
            if isinstance(规格,dict) and 'persist' in 规格:
                raise 槽装配错误('exclusive store for factory "'+str(定义['name'])+'" cannot declare persistence')
            记录={'handle':句柄,'instances':{},'retainers':0}#新记录
            出现表[出现]=记录#写入
        实例表=记录['instances']#实例
        if 作用域键 in 实例表:#已有
            return 实例表[作用域键]#复用
        创建=记录['handle'].create#创建入口
        if 定义['scope']=='root' or 作用域绑定 is None:#无键
            实例=创建()#创建
        else:#会话键
            实例=创建(作用域绑定['key'])#创建
        实例表[作用域键]=实例#写入
        return 实例#返回

    def 保留工厂出现(自身,定义,出现):
        """提交可枚举出现；返回拆除器。定义为 dict。"""
        if 自身._core.工厂仍存活(定义) is False:#死
            return 空拆除#空
        存储=定义['store'] if 'store' in 定义 else None#store
        if callable(存储) is False:#非独占
            return 空拆除#空
        轴=自身._factoryStores[定义]#工厂轴
        记录=轴['occurrences'][出现]#出现记录
        记录['retainers']+=1#加保留
        轴['mounted'][出现]=记录#提交可枚举
        已释=[False]#幂等门闩
        def 拆除器():
            """减保留；归零卸挂载。"""
            if 已释[0] is True:#已释
                return
            已释[0]=True#标记
            记录['retainers']-=1#减保留
            if 记录['retainers']!=0:#仍有持有
                return
            轴['mounted'].pop(出现,None)#卸挂载
        return 拆除器#返回

    def 释放存储作用域(自身,键):
        """丢掉已物化的非根实例；不 clearPersisted。"""
        for 记录 in list(自身._stores.values()):#逐句柄
            if 记录['scope']=='root':#根跳过
                continue#跳过
            记录['instances'].pop(键,None)#删实例
        for 轴 in list(自身._factoryStores.values()):#逐工厂轴
            for 记录 in list(轴['mounted'].values()):#已挂载出现
                记录['instances'].pop(键,None)#删出现实例

    def _获取(自身,句柄,作用域):
        """在轴上绑定（或再引用）句柄。"""
        if 句柄 not in 自身._stores:#新建
            自身._stores[句柄]={'scope':作用域,'refs':1,'instances':{}}#首引用
            return
        自身._stores[句柄]['refs']+=1#再引用

    def _拆除(自身,句柄):
        """最后持有者卸载丢掉记录。"""
        if 句柄 not in 自身._stores:#无记录
            return
        记录=自身._stores[句柄]#轴记录
        记录['refs']-=1#减引用
        if 记录['refs']!=0:#仍有持有者
            return
        del 自身._stores[句柄]#删记录
