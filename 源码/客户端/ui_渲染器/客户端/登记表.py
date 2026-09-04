"""SlotRegistry：渲染器拥有的 Cordis 服务，叠在纯 SlotCore 之上。

对齐上游 `ui-renderer/src/client/registry.ts`。公开面仅中文名。
本层拥有 slots/changed 事件桥、register/声明注入、install/renderSlot、store 实例轴。
"""
from ...ui_槽位 import 槽位核心#纯核心
from ....依赖 import cordis#外部依赖胶水

服务=cordis.服务#Cordis 服务基类

__all__=['槽登记表','标准钩子属性名','根实例键','根拥有方属性']#仅中文公开名

根实例键='root'#根实例键
根拥有方属性=dict#禁止 children 透传的根拥有方份额形状

def 标准钩子属性名(名称):#钩子到标准 prop 名
    """`session` → `useSession`。"""
    if not 名称:#空
        return 'use'#仅前缀
    return 'use'+名称[0].upper()+名称[1:]#首字母大写加 use

def 拷贝唯一(种类,目标,值表,最终属性,属性名映射):#根贡献去重拷贝
    """重名则抛。"""
    if 值表 is None:#无来源
        return#跳过
    for 名称,值 in (值表.items() if isinstance(值表,dict) else []):#逐项
        属性名=属性名映射(名称)#最终 prop 名
        if 属性名 in 最终属性:#重名
            raise Exception(f"duplicate root standard {种类} '{名称}' at prop '{属性名}'")#抛错
        最终属性.add(属性名)#登记
        目标[名称]=值#写入

class 槽登记表(服务):#渲染器侧槽服务
    """与 SlotCore 的分工见模块文档。"""

    def __init__(自身,上下文):#构造服务
        """服务名 slots；桥接变更事件。"""
        super().__init__(上下文,'slots')#服务名 slots
        自身._core=槽位核心()#纯核心
        自身._stores={}#句柄轴
        自身._storeScopeOwners={}#作用域拥有方
        自身._renderer=None#已安装渲染器
        自身._locale=None#已安装 locale 面
        自身._host=None#缓存宿主面
        自身._rootContributions=[]#根贡献名册
        自身._rootListeners=set()#根绑定订阅者
        自身._rootBinding={'key':None,'hooks':{},'keyedHooks':{},'props':{}}#当前根绑定
        自身._rootSource={#根可观察源
            'getSnapshot':lambda:自身._rootBinding,#读根绑定
            'subscribe':自身._订根,#订阅
        }#根源结束
        自身._scopes={}#严格作用域适配器
        自身._scopeRevision=0#作用域名册版本
        自身._scopeListeners=set()#作用域订阅者
        自身._scopeRevisionSource={#版本可观察源
            'getSnapshot':lambda:自身._scopeRevision,#读版本
            'subscribe':自身._订作用域修订,#订阅
        }#版本源结束
        自身._core.变更时(lambda 键:上下文.emit('slots/changed',键))#桥接变更事件

    def _订根(自身,监听):#订阅根绑定
        """返回退订。"""
        自身._rootListeners.add(监听)#登记
        return lambda:自身._rootListeners.discard(监听)#退订

    def _订作用域修订(自身,监听):#订阅作用域版本
        """返回退订。"""
        自身._scopeListeners.add(监听)#登记
        return lambda:自身._scopeListeners.discard(监听)#退订

    def register(自身,选项,组件):#唯一登记 API
        """经调用方 ctx.effect 处置。"""
        return 自身.ctx.effect(lambda:自身._登记(选项,组件),'slots.register()')#经 fiber 处置

    def inject(自身,键,回调):#声明感知注入
        """声明已存在时回调同步跑；否则等声明后跑。"""
        上下文=自身.ctx#调用方上下文
        def 控制器寿命():#控制器寿命
            """对齐声明代次；失败永久停用。"""
            活跃=[None]#当前声明寿命 disposer
            活跃代=[None]#对应声明代次
            已停=[False]#永久停用
            退订箱=[lambda:None]#声明订阅退订

            def 停用():#永久停用
                """失败调用方永久退役注入。"""
                if 已停[0]:#已停
                    return#结束
                已停[0]=True#标记停用
                退订箱[0]()#退订声明
                拆除=活跃[0]#当前 disposer
                活跃[0]=None#清空
                活跃代[0]=None#清空代次
                if 拆除 is not None:#有
                    拆除()#执行清理

            def 对齐():#对齐声明代次
                """同代次复用。"""
                if 已停[0]:#已停
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
                    return#结束
                拆除效果=上下文.effect(回调,f'slots.inject({键!r}): declaration')#嵌套 effect
                活跃[0]=lambda:拆除效果()#包装 disposer
                活跃代[0]=代次#记下代次

            def 变更():#声明变更
                """尝试对齐；失败停用。"""
                try:#尝试对齐
                    对齐()#对齐
                except Exception as 错误:#失败
                    码=getattr(错误,'code',None)#错误码
                    停用()#停用
                    if 码=='INACTIVE_EFFECT':#fiber 已死
                        return#结束
                    raise#异步再抛由宿主

            退订箱[0]=自身._core.订阅声明(键,变更)#订声明
            try:#首轮对齐
                对齐()#对齐
            except Exception:#同步失败
                停用()#停用
                raise#上抛
            return 停用#控制器 disposer
        拆除控制器=上下文.effect(控制器寿命,f'slots.inject({键!r})')#诊断名
        return lambda:拆除控制器()#对外 disposer

    def install(自身,渲染器):#安装渲染器
        """启动一次：二次安装抛错。"""
        if 自身._renderer is not None:#已装
            raise Exception('slot renderer already installed (install() is boot-once)')#禁止二次
        def 寿命():#渲染器寿命
            """挂上；拆卸仅卸自己。"""
            自身._renderer=渲染器#挂上
            return lambda:(自身.__setattr__('_renderer',None) if 自身._renderer is 渲染器 else None)#拆卸
        自身.ctx.effect(寿命,'slots.install()')#诊断名

    def installLocale(自身,面):#安装 locale 面
        """与渲染器安装同为启动一次纪律。"""
        if 自身._locale is not None:#已装
            raise Exception('locale face already installed (installLocale() is boot-once)')#禁止二次
        def 寿命():#面寿命
            """挂上；拆卸仅卸自己。"""
            自身._locale=面#挂上
            return lambda:(自身.__setattr__('_locale',None) if 自身._locale is 面 else None)#拆卸
        自身.ctx.effect(寿命,'slots.installLocale()')#诊断名

    def provideRoot(自身,贡献):#贡献根源
        """钩子名必须全局唯一。"""
        def 寿命():#贡献寿命
            """挂上后重建；失败回滚。"""
            自身._rootContributions.append(贡献)#挂上
            try:#重建
                自身.重建根绑定()#重发根绑定
            except Exception:#失败回滚
                自身._rootContributions.pop()#弹出
                raise#上抛
            def 拆卸():#拆卸
                """卸下再重建。"""
                try:#定位
                    索引=自身._rootContributions.index(贡献)#定位
                except ValueError:#已不在
                    return#忽略
                自身._rootContributions.pop(索引)#卸下
                自身.重建根绑定()#再重建
            return 拆卸#返回拆卸
        拆除=自身.ctx.effect(寿命,'slots.provideRoot()')#诊断名
        return lambda:拆除()#对外 disposer

    def installScope(自身,作用域,适配器):#安装作用域
        """严格作用域；可选对偶经同一适配器解析。"""
        if 作用域 in 自身._scopes:#已有
            raise Exception(f"slot scope '{作用域}' already has an adapter")#禁止二次
        def 寿命():#适配器寿命
            """挂上并发版本。"""
            自身._scopes[作用域]=适配器#挂上
            自身.发布作用域修订()#发版本
            def 拆卸():#拆卸
                """仍是自己则卸下。"""
                if 自身._scopes.get(作用域) is 适配器:#仍是自己
                    自身._scopes.pop(作用域,None)#卸下
                    自身.发布作用域修订()#发版本
            return 拆卸#返回拆卸
        自身.ctx.effect(寿命,f'slots.installScope({作用域!r})')#诊断名

    def bindStoreScope(自身,绑定):#绑 store 作用域
        """重绑同一键会把清理所有权交给最新 Context 代。"""
        键=绑定['key'] if isinstance(绑定,dict) else 绑定.key#作用域键
        上下文=绑定['ctx'] if isinstance(绑定,dict) else 绑定.ctx#拥有 Context
        当前=自身._storeScopeOwners.get(键)#当前拥有方
        if 当前 is 上下文:#同代次
            return#跳过
        自身._storeScopeOwners[键]=上下文#记下最新代
        def 寿命():#作用域死亡清理
            """已被更新代接管则忽略。"""
            def 清理():#清理
                """清拥有方与实例。"""
                if 自身._storeScopeOwners.get(键) is not 上下文:#已被更新代接管
                    return#忽略
                自身._storeScopeOwners.pop(键,None)#清拥有方
                自身.清除存储作用域(键)#清实例
            return 清理#返回清理
        上下文.effect(寿命,f'slots: store scope {键}')#诊断名

    def renderSlot(自身,键,拥有方):#ctx 级渲染
        """仅渲染 root；三道守卫响亮失败。"""
        if 键!='root':#非 root
            raise Exception(f"ctx-level renderSlot only renders 'root' (got \"{键}\"); child slots render through the component props face")#抛错
        if 自身._renderer is None:#未安装
            raise Exception("slot renderer not installed — boot must call ctx.slots.install(createSlotRenderer()) before rendering 'root'")#抛错
        if len(自身._core.条目们('root'))==0:#无登记
            raise Exception("'root' has no registration — a layout entry must register into 'root' before the shell renders it")#抛错
        渲根=自身._renderer['renderRoot'] if isinstance(自身._renderer,dict) else 自身._renderer.renderRoot#渲染根
        return 渲根(自身.宿主面(),拥有方)#渲染根

    def entries(自身,键):#条目快照
        """委托核心。"""
        return 自身._core.条目们(键)#委托核心

    def entriesOfSlot(自身,键):#胜出条目
        """委托核心。"""
        return 自身._core.槽位条目们(键)#委托核心

    def snapshot(自身,根=None):#声明树快照
        """委托核心。"""
        return 自身._core.快照(根)#委托核心

    def onEntryError(自身,回调):#订崩溃
        """委托核心。"""
        return 自身._core.条目错误时(回调)#委托核心

    def spec(自身,键):#查规范
        """委托核心。"""
        return 自身._core.规格(键)#委托核心

    def subscribe(自身,键,回调):#订变更
        """委托核心。"""
        return 自身._core.订阅(键,回调)#委托核心

    def getVersion(自身,键):#读版本
        """委托核心。"""
        return 自身._core.版本(键)#委托核心

    def _登记(自身,选项,组件):#内部登记
        """工厂铸造 + registrant 戳 + 核心写入 + 实例轴记账。"""
        存储=选项.get('store') if isinstance(选项,dict) else getattr(选项,'store',None)#store
        if callable(存储):#工厂
            存储=存储()#铸造
        登记方=选项.get('registrant') if isinstance(选项,dict) else getattr(选项,'registrant',None)#登记方戳
        if 登记方 is None:#缺
            纤=getattr(自身.ctx,'fiber',None)#fiber
            登记方=getattr(纤,'name',None) if 纤 is not None else None#诊断戳
        擦除=dict(选项) if isinstance(选项,dict) else dict(getattr(选项,'__dict__',{}))#擦除选项
        if 存储 is not None:#有
            擦除['store']=存储#可解析句柄
        if 登记方 is not None:#有
            擦除['registrant']=登记方#诊断戳
        拆除=自身._core.登记(擦除,组件)#核心写入
        if 存储 is not None:#有 store
            规格=自身._core.动态规格(擦除.get('name'))#取作用域
            作用域=规格.get('scope') if isinstance(规格,dict) else getattr(规格,'scope',None)#作用域
            自身._获取(存储,作用域)#轴记账
        已卸=[False]#幂等门闩
        def 拆除器():#disposer
            """幂等卸核心并释引用。"""
            if 已卸[0]:#已卸
                return#结束
            已卸[0]=True#标记
            拆除()#卸核心
            if 存储 is not None:#有
                自身._释放(存储)#释引用
        return 拆除器#返回

    def 宿主面(自身):#宿主面
        """构建一次域中立宿主面；已安装适配器经 getter 保持活。"""
        if 自身._host is not None:#复用
            return 自身._host#缓存
        服务别名=自身#服务别名
        自身._host={#构建宿主
            'subscribe':lambda 键,回调:自身._core.订阅(键,回调),#订变更
            'getVersion':lambda 键:自身._core.版本(键),#读版本
            'entriesOf':lambda 键:自身._core.条目们(键),#条目快照
            'entriesOfSlot':lambda 键:自身._core.槽位条目们(键),#胜出条目
            'reportEntryError':lambda 键,条目,错误,信息:自身._core.报告条目错误(键,条目,错误,信息),#报告崩溃
            'specOf':lambda 键:自身._core.动态规格(键),#动态规范
            'isLive':lambda 条目:自身._core.仍存活(条目),#是否活
            'storeOf':lambda 条目,作用域绑定:自身.解析存储(条目.get('store') if isinstance(条目,dict) else getattr(条目,'store',None),作用域绑定) if (条目.get('store') if isinstance(条目,dict) else getattr(条目,'store',None)) is not None else None,#解析 store
            'root':自身._rootSource,#根源
            'scopeRevision':自身._scopeRevisionSource,#作用域版本
            'scope':lambda 作用域:服务别名._scopes.get('session' if 作用域=='session-maybe' else 作用域),#取适配器
            'locale':lambda:服务别名._locale,#活 locale（调用形）
        }#宿主结束
        return 自身._host#返回

    def 重建根绑定(自身):#重建根绑定
        """校验并原子发布当前根贡献名册。"""
        钩子={}#钩子表
        键控={}#键控表
        属性={}#prop 表
        最终属性=set()#去重集
        for 贡献 in 自身._rootContributions:#逐贡献
            拷贝唯一('hook',钩子,贡献.get('hooks') if isinstance(贡献,dict) else getattr(贡献,'hooks',None),最终属性,标准钩子属性名)#拷钩子
            拷贝唯一('keyed hook',键控,贡献.get('keyedHooks') if isinstance(贡献,dict) else getattr(贡献,'keyedHooks',None),最终属性,标准钩子属性名)#拷键控
            拷贝唯一('prop',属性,贡献.get('props') if isinstance(贡献,dict) else getattr(贡献,'props',None),最终属性,lambda 名:名)#拷 prop
        自身._rootBinding={'key':None,'hooks':钩子,'keyedHooks':键控,'props':属性}#发布
        for 监听 in list(自身._rootListeners):#通知订阅者
            try:#隔离失败
                监听()#回调
            except Exception as 错误:#订阅者抛错
                print('root standard-source subscriber failed:',错误)#打印

    def 发布作用域修订(自身):#发作用域版本
        """在映射已权威后发布一次已安装作用域名册过渡。"""
        自身._scopeRevision+=1#递增
        for 监听 in list(自身._scopeListeners):#通知
            try:#隔离失败
                监听()#回调
            except Exception as 错误:#订阅者抛错
                print('scope-adapter subscriber failed:',错误)#打印

    def 解析存储(自身,句柄,作用域绑定):#解析（创建或复用）已登记句柄的 store 实例
        """会话实例拿作用域键；根实例保持无键。"""
        记录=自身._stores.get(句柄)#轴记录
        if 记录 is None:#未登记
            raise Exception('store handle is not registered (entry unloaded, or the handle never went through register)')#未登记
        if 记录['scope']=='root':#根作用域
            键=根实例键#根键
        else:#会话作用域
            if 作用域绑定 is None:#缺绑定
                raise Exception(f"{记录['scope']} store resolution requires a session id")#缺绑定
            键=作用域绑定['key'] if isinstance(作用域绑定,dict) else 作用域绑定.key#会话键
            自身.bindStoreScope(作用域绑定)#确保寿命
        实例=记录['instances'].get(键)#读缓存
        if 实例 is None:#未创建
            创建=句柄['create'] if isinstance(句柄,dict) else 句柄.create#创建入口
            实例=创建() if 记录['scope']=='root' else 创建(键)#创建
            记录['instances'][键]=实例#写入
        return 实例#返回

    def 清除存储作用域(自身,键):#清作用域 store
        """为一个死亡作用域键清除每一个活的非根 Store 句柄。"""
        for 句柄,记录 in list(自身._stores.items()):#逐句柄
            if 记录['scope']=='root':#根跳过
                continue#跳过
            实例=记录['instances'].get(键)#读
            if 实例 is None:#未创建
                创建=句柄['create'] if isinstance(句柄,dict) else 句柄.create#创建
                实例=创建(键)#物化以便清持久
            清=getattr(实例,'clearPersisted',None)#清持久
            if callable(清):#有
                清()#清持久
            记录['instances'].pop(键,None)#删实例

    def _获取(自身,句柄,作用域):#获取引用
        """在轴上绑定（或再引用）句柄。"""
        记录=自身._stores.get(句柄)#已有记录
        if 记录 is None:#新建
            自身._stores[句柄]={'scope':作用域,'refs':1,'instances':{}}#首引用
            return#结束
        记录['refs']+=1#再引用

    def _释放(自身,句柄):#释放引用
        """最后持有者卸载丢掉记录。"""
        记录=自身._stores.get(句柄)#轴记录
        if 记录 is None:#无记录
            return#结束
        记录['refs']-=1#减引用
        if 记录['refs']!=0:#仍有持有者
            return#结束
        自身._stores.pop(句柄,None)#删记录

SlotRegistry=槽登记表#上游名
