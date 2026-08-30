"""纯槽位登记表（无 cordis）。



对齐上游 `ui-slots/src/index.ts` 中的 SlotCore 与 resolveSlotLabel。公开面仅中文名。

变更传播：每次变更同步抬版本并触发 onMutate；subscribe 按微任务批处理。

"""

import threading#微任务近似



__all__=['槽位核心','解析槽标签','空条目']#仅中文公开名



空条目=tuple()#空条目的稳定引用



def 解析槽标签(标签):#读时解析可能是 thunk 的列表标签

    """thunk 则调用，否则原样；未声明为 None。"""

    if 标签 is None:#未声明

        return None#缺席

    if callable(标签):#thunk

        return 标签()#调用

    return 标签#字面量



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



class 槽位核心:#纯槽位登记表

    """'root' 槽是唯一先验声明，构造时播种（single/root）。"""

    def __init__(自身):#播种先验根洞

        """构造时空无人观察，不 markDirty。"""

        自身.记录表={}#按键的登记记录；创建后永不删除

        自身.变更监听=set()#每次变更同步通知

        自身.句柄作用域={}#共享句柄→首次挂载作用域 + 活挂载计数

        自身.脏集=set()#待冲刷的脏记录

        自身.已排冲刷=False#是否已排微任务冲刷

        自身.已退位=set()#崩溃退位的条目 id

        自身.条目错误监听=set()#条目崩溃监听

        根=自身.取记录('root')#取得或创建 root

        根['spec']={'kind':'single','scope':'root'}#单占、根作用域

        根['declaredBy']='(built-in)'#框架内置

        根['declarationEpoch']=1#首次声明世代



    def 取记录(自身,键):#取得或创建按键记录

        """第一次碰到时创建空白记录。"""

        记=自身.记录表.get(键)#已有

        if 记 is None:#第一次

            记={#空白记录

                'spec':None,#尚未声明

                'declaredBy':None,#无声明者

                'parent':None,#无父

                'declarationEpoch':0,#首次声明前为 0

                'entries':空条目,#空台账

                'version':0,#未变更

                'listeners':set(),#登记变更订阅

                'declarationListeners':set(),#声明寿命订阅

            }#记录结束

            自身.记录表[键]=记#写入；永不删除

        return 记#返回



    def 登记(自身,选项,组件):#向已声明槽贡献组件

        """返回拆除器；未声明/冲突/基数约束失败则抛错。"""

        名=取字段(选项,'name')#目标槽键

        记=自身.记录表.get(名)#目标记录

        if 记 is None or 取字段(记,'spec') is None:#未声明

            raise Exception(f'slot "{名}" is not declared (a parent entry\'s children table must declare it)')#未声明

        规格=记['spec']#运行时规格

        优先级=取字段(选项,'priority')#优先级

        if 优先级 is None:#缺省

            优先级=0#0

        def 占用提示(占用者):#拼占用者提示

            """点名优先级与占用者。"""

            登记方=取字段(占用者,'registrant')#登记方

            尾='' if 登记方 is None else f' (registered by {登记方})'#尾

            return f'at priority {优先级}{尾} — register at a different priority to shadow it (lowest renders)'#提示

        种类=取字段(规格,'kind')#基数

        条目表=list(记['entries'])#台账副本

        if 种类=='single':#单占

            for 已有 in 条目表:#扫

                if (取字段(取字段(已有,'options'),'priority') or 0)==优先级:#同优先级

                    raise Exception(f'single slot "{名}" already has a registration {占用提示(已有)}')#冲突

        elif 种类=='keyed':#按键

            键=取字段(选项,'key')#字面键

            if 键 is None:#缺

                raise Exception(f'keyed slot "{名}" requires options.key')#缺 key

            for 已有 in 条目表:#扫

                if 取字段(取字段(已有,'options'),'key')==键 and (取字段(取字段(已有,'options'),'priority') or 0)==优先级:#同键同优先级

                    raise Exception(f'keyed slot "{名}" already has an entry for key "{键}" {占用提示(已有)}')#冲突

        elif 种类=='list':#列表

            标识=取字段(选项,'id')#id

            if 标识 is None:#缺

                raise Exception(f'list slot "{名}" requires options.id')#缺 id

            for 已有 in 条目表:#扫

                if 取字段(取字段(已有,'options'),'id')==标识 and (取字段(取字段(已有,'options'),'priority') or 0)==优先级:#同 id 同优先级

                    raise Exception(f'list slot "{名}" already has an entry with id "{标识}" {占用提示(已有)}')#冲突

        elif 种类=='chain':#链

            if 取字段(选项,'select') is None:#缺

                raise Exception(f'chain slot "{名}" requires options.select')#缺 select

        子表=取字段(选项,'children')#子槽声明

        if 子表:#有子

            for 子键 in 子表.keys():#每个子键

                子记=自身.记录表.get(子键)#已有

                if 子记 is not None and 取字段(子记,'spec') is not None:#已被声明

                    声明者=取字段(子记,'declaredBy') or 'an unknown entry'#声明者

                    raise Exception(f'slot "{子键}" is already declared (by {声明者})')#一槽一声明者

        仓库=取字段(选项,'store')#仓库座位

        if 仓库 is not None and not callable(仓库):#共享句柄

            钉=自身.句柄作用域.get(id(仓库))#已钉

            作用域=取字段(规格,'scope')#本作用域

            if 钉 is not None and 钉['scope']!=作用域:#跨作用域

                raise Exception(f'store handle mounted under "{名}" (scope "{作用域}") is already mounted under scope "{钉["scope"]}" — one handle, one scope')#一柄一作用域

            if 钉 is not None:#已钉

                钉['count']+=1#加计数

            else:#首次

                自身.句柄作用域[id(仓库)]={'scope':作用域,'count':1,'handle':仓库}#钉住

        形状={}#kind 形状字段

        if 取字段(选项,'key') is not None:#keyed

            形状['key']=取字段(选项,'key')#键

        if 取字段(选项,'id') is not None:#list

            形状['id']=取字段(选项,'id')#id

        if 取字段(选项,'order') is not None:#顺序

            形状['order']=取字段(选项,'order')#order

        if 取字段(选项,'label') is not None:#标签

            形状['label']=取字段(选项,'label')#label

        if 取字段(选项,'priority') is not None:#优先级

            形状['priority']=取字段(选项,'priority')#priority

        条目={#本条登记

            'component':组件,#组件

            'options':形状,#形状

        }#条目结束

        条目['_id']=id(条目)#稳定身份（退位用）

        if 取字段(选项,'select') is not None:#链选择器

            条目['select']=取字段(选项,'select')#select

        if 取字段(选项,'inject') is not None:#业务面

            条目['inject']=取字段(选项,'inject')#inject

        if 子表 is not None:#子槽

            条目['children']=子表#children

        if 仓库 is not None:#仓库

            条目['store']=仓库#store

        if 取字段(选项,'locale') is not None:#文案

            条目['locale']=取字段(选项,'locale')#locale

        if 取字段(选项,'registrant') is not None:#诊断

            条目['registrant']=取字段(选项,'registrant')#registrant

        下一批=条目表+[条目]#追加

        if 种类=='list':#list 再按 order

            下一批.sort(key=lambda 甲:(取字段(取字段(甲,'options'),'priority') or 0,取字段(取字段(甲,'options'),'order') or 0))#优先级+order

        else:#其余只按优先级

            下一批.sort(key=lambda 甲:取字段(取字段(甲,'options'),'priority') or 0)#优先级升序

        记['entries']=tuple(下一批)#写回台账

        自身.标脏(名,记)#标脏

        if 子表:#声明子槽

            本批=[]#攒齐再发布

            for 子键,子规格 in 子表.items():#每个子槽

                子记=自身.取记录(子键)#取得或创建

                子记['spec']=子规格#规格

                登记方=取字段(选项,'registrant')#登记方

                尾='' if 登记方 is None else f' ({登记方})'#尾

                子记['declaredBy']=f'an entry in "{名}"{尾}'#声明者

                子记['parent']=名#父

                子记['declarationEpoch']=取字段(子记,'declarationEpoch')+1#抬世代

                本批.append((子键,子记))#攒

            for 子键,子记 in 本批:#标脏

                自身.标脏(子键,子记)#变更

            for _,子记 in 本批:#声明寿命

                自身.通知声明(子记)#同步

        def 拆除():#拆除本条登记

            """幂等；级联后过期拆除器空操作。"""

            当前=list(记['entries'])#当前台账

            if 条目 not in 当前:#已不在

                return#空操作

            记['entries']=tuple(甲 for 甲 in 当前 if 甲 is not 条目)#拿掉

            自身.标脏(名,记)#标脏

            自身.释放条目(条目)#释放

        return 拆除#拆除器



    def 仍存活(自身,条目):#条目是否仍在台账

        """渲染机械的过期授权探测。"""

        for 记 in 自身.记录表.values():#扫

            if 条目 in 记['entries']:#在台账

                return True#活

        return False#死



    def 条目们(自身,键):#生台账快照

        """变更之间引用稳定。"""

        记=自身.记录表.get(键)#记录

        if 记 is None:#无

            return 空条目#空

        return 记['entries']#数组引用



    def 槽位条目们(自身,键):#投影每格遮蔽胜者

        """chain 不遮蔽；每次调用新元组。"""

        记=自身.记录表.get(键)#记录

        if 记 is None or 取字段(记,'spec') is None:#未声明

            return 空条目#空

        种类=取字段(记['spec'],'kind')#基数

        if 种类=='chain':#链

            return 记['entries']#原样

        胜者=[]#每格第一个活条目

        已见=set()#已见格

        for 条目 in 记['entries']:#按优先级扫

            if 取字段(条目,'_id') in 自身.已退位:#已退位

                continue#跳过

            形状=取字段(条目,'options') or {}#形状

            if 种类=='keyed':#keyed

                格=取字段(形状,'key')#格

            elif 种类=='list':#list

                格=取字段(形状,'id')#格

            else:#single

                格=None#共用

            if 格 in 已见:#已有胜者

                continue#跳过

            已见.add(格)#记下

            胜者.append(条目)#胜者

        return tuple(胜者)#元组



    def 规格(自身,键):#按槽键查规格

        """未声明为 None。"""

        记=自身.记录表.get(键)#记录

        return None if 记 is None else 取字段(记,'spec')#规格



    def 动态规格(自身,键):#按字符串键查宽规格

        """渲染器动态键逃生口。"""

        return 自身.规格(键)#同规格



    def 快照(自身,根=None):#导出声明拓扑

        """不含组件或可执行钩。"""

        def 建树(名,已见):#递归建节点

            """环或未声明则 None。"""

            记=自身.记录表.get(名)#记录

            if 记 is None or 取字段(记,'spec') is None or 名 in 已见:#丢掉

                return None#无

            支=set(已见)#本支

            支.add(名)#已见

            活动=set(自身.槽位条目们(名))#胜者集合

            子节点=[]#子树

            for 子名,候选 in 自身.记录表.items():#所有记录

                if 取字段(候选,'spec') is not None and 取字段(候选,'parent')==名:#活子

                    节=建树(子名,支)#建

                    if 节 is not None:#可用

                        子节点.append(节)#记入

            占用者=[]#占用者表

            for 条目 in 记['entries']:#每个登记

                形=取字段(条目,'options') or {}#形状

                行={'priority':取字段(形,'priority') or 0,'active':条目 in 活动}#基础

                if 取字段(条目,'registrant') is not None:#登记方

                    行['registrant']=取字段(条目,'registrant')#带上

                if 取字段(形,'key') is not None:#keyed

                    行['key']=取字段(形,'key')#键

                if 取字段(形,'id') is not None:#list

                    行['id']=取字段(形,'id')#id

                if 取字段(形,'order') is not None:#order

                    行['order']=取字段(形,'order')#order

                占用者.append(行)#记入

            节点={#活槽节点

                'name':名,#槽键

                'kind':取字段(记['spec'],'kind'),#基数

                'scope':取字段(记['spec'],'scope'),#作用域

                'occupants':占用者,#占用者

                'children':子节点,#子树

            }#节点结束

            if 取字段(记,'declaredBy') is not None:#声明者

                节点['declaredBy']=取字段(记,'declaredBy')#带上

            return 节点#返回

        if 根 is not None:#指定根

            节=建树(根,set())#建

            return [] if 节 is None else [节]#不可用则空

        结果=[]#活根表

        for 名,记 in 自身.记录表.items():#所有

            if 取字段(记,'spec') is None:#未声明

                continue#跳

            父=取字段(记,'parent')#父

            if 父 is not None:#有父

                父记=自身.记录表.get(父)#父记录

                if 父记 is not None and 取字段(父记,'spec') is not None:#父仍活

                    continue#非根

            节=建树(名,set())#建

            if 节 is not None:#可用

                结果.append(节)#记入

        return 结果#返回



    def 声明世代(自身,键):#读声明寿命世代

        """首次声明前为 0。"""

        记=自身.记录表.get(键)#记录

        return 0 if 记 is None else 取字段(记,'declarationEpoch')#世代



    def 订阅(自身,键,回调):#订阅登记变更

        """微任务批处理；允许声明前订阅。"""

        记=自身.取记录(键)#取得或创建

        记['listeners'].add(回调)#加入

        def 退订():#取消

            """从集合拿掉。"""

            记['listeners'].discard(回调)#删

        return 退订#退订器



    def 订阅声明(自身,键,回调):#订阅声明寿命

        """同步通知。"""

        记=自身.取记录(键)#取得或创建

        记['declarationListeners'].add(回调)#加入

        def 退订():#取消

            """从集合拿掉。"""

            记['declarationListeners'].discard(回调)#删

        return 退订#退订器



    def 版本(自身,键):#读变更版本

        """未碰过的键为 0。"""

        记=自身.记录表.get(键)#记录

        return 0 if 记 is None else 取字段(记,'version')#版本



    def 变更时(自身,回调):#钩住每一次变更

        """同步触发、不批处理。"""

        自身.变更监听.add(回调)#加入

        def 退订():#取消

            """从集合拿掉。"""

            自身.变更监听.discard(回调)#删

        return 退订#退订器



    def 报告条目错误(自身,键,条目,错误,信息):#报告条目崩溃

        """abdicate 时一次性退位；重复退位空操作。"""

        退位=bool(取字段(信息,'abdicate'))#是否退位

        if 退位:#遮蔽基数

            标识=取字段(条目,'_id')#身份

            if 标识 in 自身.已退位:#已退位

                return#空操作

            自身.已退位.add(标识)#记下

            记=自身.记录表.get(键)#记录

            if 记 is not None:#有

                自身.标脏(键,记)#抬版本

        for 回调 in list(自身.条目错误监听):#快照后通知

            回调(键,条目,错误,{'abdicated':退位})#同步



    def 条目错误时(自身,回调):#观察条目崩溃

        """每次报告同步触发。"""

        自身.条目错误监听.add(回调)#加入

        def 退订():#取消

            """从集合拿掉。"""

            自身.条目错误监听.discard(回调)#删

        return 退订#退订器



    def 释放条目(自身,条目):#拆除一条登记的副作用

        """释放仓库挂载并塌缩子槽。"""

        仓库=取字段(条目,'store')#仓库

        if 仓库 is not None and not callable(仓库):#共享句柄

            钉=自身.句柄作用域.get(id(仓库))#已钉

            if 钉 is not None:#有

                钉['count']-=1#减

                if 钉['count']==0:#归零

                    del 自身.句柄作用域[id(仓库)]#拿掉

        子表=取字段(条目,'children')#子槽

        if not 子表:#无子

            return#完

        for 子键 in 子表.keys():#每个子槽

            子记=自身.记录表.get(子键)#子记录

            if 子记 is None:#无

                continue#跳

            注定=list(子记['entries'])#将被拆除

            子记['spec']=None#清规格

            子记['declaredBy']=None#清声明者

            子记['parent']=None#清父

            子记['declarationEpoch']=取字段(子记,'declarationEpoch')+1#抬世代

            子记['entries']=空条目#清空

            自身.标脏(子键,子记)#标脏

            自身.通知声明(子记)#声明寿命

            for 死 in 注定:#递归

                自身.释放条目(死)#拆除



    def 标脏(自身,键,记):#同步抬版本、通知变更、排微任务冲刷

        """版本同步抬升。"""

        记['version']=取字段(记,'version')+1#抬版本

        for 回调 in list(自身.变更监听):#同步通知

            回调(键)#调用

        自身.脏集.add(id(记))#记下待冲刷（用 id 因 set 要可哈希）；并存映射

        if not hasattr(自身,'_脏映射'):#惰性

            自身._脏映射={}#id→记录

        自身._脏映射[id(记)]=记#映射

        if 自身.已排冲刷:#已排

            return#幂等

        自身.已排冲刷=True#记下

        def 微任务冲刷():#微任务 flush

            """冲刷 subscribe 监听。"""

            自身.冲刷()#冲刷

        threading.Timer(0,微任务冲刷).start()#近似 queueMicrotask



    def 通知声明(自身,记):#同步通知声明寿命监听

        """快照后调用。"""

        for 回调 in list(记['declarationListeners']):#快照

            回调()#调用



    def 冲刷(自身):#冲刷微任务批处理的登记变更订阅

        """先复位，好让监听器内部的变更重新排程。"""

        自身.已排冲刷=False#复位

        脏=list(自身.脏集)#快照

        自身.脏集.clear()#清空

        映射=getattr(自身,'_脏映射',{})#映射

        for 标识 in 脏:#每个脏

            记=映射.pop(标识,None)#取出

            if 记 is None:#无

                continue#跳

            for 回调 in list(记['listeners']):#通知

                回调()#调用



    # 英文方法别名：对齐上游 SlotCore 公开面，供未汉化调用方

    register=登记#登记

    isLive=仍存活#仍存活

    entries=条目们#条目们

    entriesOfSlot=槽位条目们#槽位条目们

    spec=规格#规格

    specDynamic=动态规格#动态规格

    snapshot=快照#快照

    declarationEpoch=声明世代#声明世代

    subscribe=订阅#订阅

    subscribeDeclaration=订阅声明#订阅声明

    getVersion=版本#版本

    onMutate=变更时#变更时

    reportEntryError=报告条目错误#报告条目错误

    onEntryError=条目错误时#条目错误时


