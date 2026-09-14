import threading#微任务近似

__all__=['槽位错误','槽位登记表','解析槽标签','空条目']#仅中文公开名

空条目=tuple()#空条目的稳定引用

class 槽位错误(Exception):
    """槽位登记表登记与声明失败。"""
    pass#无额外字段

def 解析槽标签(标签):
    """读时解析 SlotLabel。上游 `export type SlotLabel = string | (() => string)`：字面量或零参 thunk。"""
    if 标签 is None:#未声明
        return None#缺席
    if isinstance(标签,str):#字面量臂
        return 标签#值
    return 标签()#thunk 臂

def 是存储工厂(存储):
    """对齐 SlotCore.register：`typeof store === 'function'` 的独占工厂臂。"""
    return callable(存储)#工厂

def 条目优先级(条目):
    """options.priority；缺键为 0。上游 `?? 0`，0 是合法遮蔽秩不得被 || 吞掉。"""
    形=条目['options']#形状
    return 形['priority'] if 'priority' in 形 else 0#缺键才 0

def 条目顺序(条目):
    """options.order；缺键为 0。上游 `?? 0`，0 是合法 display 序。"""
    形=条目['options']#形状
    return 形['order'] if 'order' in 形 else 0#缺键才 0

def 列表排序键(甲):
    """list：priority 升序，同分 order。"""
    return (条目优先级(甲),条目顺序(甲))#键

def 优先级排序键(甲):
    """非 list：只按 priority 升序。"""
    return 条目优先级(甲)#键

class 槽位登记表:#纯槽位登记表
    """'root' 槽是唯一先验声明，构造时播种（single/root）。"""
    def __init__(自身):
        """构造时空无人观察，不 markDirty。"""
        自身.记录表={}#按键的登记记录；创建后永不删除
        自身.变更监听=set()#每次变更同步通知
        自身.句柄作用域={}#共享句柄→首次挂载作用域 + 活挂载计数
        自身.脏集=set()#待冲刷的脏记录
        自身.脏映射={}#id→记录
        自身.已排冲刷=False#是否已排微任务冲刷
        自身.已退位=set()#崩溃退位的条目 id
        自身.条目错误监听=set()#条目崩溃监听
        根=自身.取记录('root')#取得或创建 root
        根['spec']={'kind':'single','scope':'root'}#单占、根作用域
        根['declaredBy']='(built-in)'#框架内置
        根['declarationEpoch']=1#首次声明世代

    def 取记录(自身,键):
        """第一次碰到时创建空白记录。"""
        if 键 in 自身.记录表:#已有
            return 自身.记录表[键]#返回
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

    def 登记(自身,选项,组件):
        """返回拆除器；未声明/冲突/基数约束失败则抛错。选项为 dict。"""
        名=选项['name']#目标槽键
        记=自身.记录表[名] if 名 in 自身.记录表 else None#目标记录
        if 记 is None or 记['spec'] is None:#未声明
            raise 槽位错误('slot "'+str(名)+'" is not declared (a parent entry\'s children table must declare it)')#未声明
        规格=记['spec']#运行时规格
        优先级=选项['priority'] if 'priority' in 选项 else 0#?? 0；0 合法
        def 占用提示(占用者):
            """点名优先级与占用者。占用者为 dict。"""
            登记方=占用者['registrant'] if 'registrant' in 占用者 else None#登记方
            尾='' if 登记方 is None else ' (registered by '+str(登记方)+')'#尾
            return 'at priority '+str(优先级)+尾+' — register at a different priority to shadow it (lowest renders)'#提示
        种类=规格['kind']#基数
        条目表=list(记['entries'])#台账副本
        if 种类=='single':#单占
            for 已有 in 条目表:#扫
                if 条目优先级(已有)==优先级:#同优先级
                    raise 槽位错误('single slot "'+str(名)+'" already has a registration '+占用提示(已有))#冲突
        elif 种类=='keyed':#按键
            if 'key' not in 选项:#缺 key
                raise 槽位错误('keyed slot "'+str(名)+'" requires options.key')#缺 key
            键=选项['key']#字面键
            for 已有 in 条目表:#扫
                已形=已有['options']#形状
                已键=已形['key'] if 'key' in 已形 else None#已键
                if 已键==键 and 条目优先级(已有)==优先级:#同键同优先级
                    raise 槽位错误('keyed slot "'+str(名)+'" already has an entry for key "'+str(键)+'" '+占用提示(已有))#冲突
        elif 种类=='list':#列表
            if 'id' not in 选项:#缺 id
                raise 槽位错误('list slot "'+str(名)+'" requires options.id')#缺 id
            标识=选项['id']#id
            for 已有 in 条目表:#扫
                已形=已有['options']#形状
                已标识=已形['id'] if 'id' in 已形 else None#已 id
                if 已标识==标识 and 条目优先级(已有)==优先级:#同 id 同优先级
                    raise 槽位错误('list slot "'+str(名)+'" already has an entry with id "'+str(标识)+'" '+占用提示(已有))#冲突
        elif 种类=='chain':#链
            if 'select' not in 选项:#缺 select
                raise 槽位错误('chain slot "'+str(名)+'" requires options.select')#缺 select
        子表=选项['children'] if 'children' in 选项 else None#子槽声明
        if 子表 is not None:#有子；空 dict 在 JS 为真仍声明
            for 子键 in 子表.keys():#每个子键
                子记=自身.记录表[子键] if 子键 in 自身.记录表 else None#已有
                if 子记 is not None and 子记['spec'] is not None:#已被声明
                    声明者=子记['declaredBy'] if 'declaredBy' in 子记 and 子记['declaredBy'] is not None else 'an unknown entry'#声明者
                    raise 槽位错误('slot "'+str(子键)+'" is already declared (by '+str(声明者)+')')#一槽一声明者
        存储=选项['store'] if 'store' in 选项 else None#存储座位
        if 存储 is not None and 是存储工厂(存储) is False:#共享句柄
            钉=自身.句柄作用域[id(存储)] if id(存储) in 自身.句柄作用域 else None#已钉
            作用域=规格['scope']#本作用域
            if 钉 is not None and 钉['scope']!=作用域:#跨作用域
                raise 槽位错误('store handle mounted under "'+str(名)+'" (scope "'+str(作用域)+'") is already mounted under scope "'+str(钉['scope'])+'" — one handle, one scope')#一柄一作用域
            if 钉 is not None:#已钉
                钉['count']+=1#加计数
            else:#首次
                自身.句柄作用域[id(存储)]={'scope':作用域,'count':1,'handle':存储}#钉住
        形状={}#kind 形状字段
        if 'key' in 选项:#keyed
            形状['key']=选项['key']#键
        if 'id' in 选项:#list
            形状['id']=选项['id']#id
        if 'order' in 选项:#顺序
            形状['order']=选项['order']#order
        if 'label' in 选项:#标签
            形状['label']=选项['label']#label
        if 'priority' in 选项:#优先级
            形状['priority']=选项['priority']#priority
        条目={#本条登记
            'component':组件,#组件
            'options':形状,#形状
        }#条目结束
        条目['_id']=id(条目)#稳定身份（退位用）
        if 'select' in 选项:#链选择器
            条目['select']=选项['select']#select
        if 'inject' in 选项:#业务面
            条目['inject']=选项['inject']#inject
        if 子表 is not None:#子槽
            条目['children']=子表#children
        if 存储 is not None:#存储
            条目['store']=存储#store
        if 'locale' in 选项:#文案
            条目['locale']=选项['locale']#locale
        if 'registrant' in 选项:#诊断
            条目['registrant']=选项['registrant']#registrant
        下一批=条目表+[条目]#追加
        if 种类=='list':#list 再按 order
            下一批.sort(key=列表排序键)#优先级+order
        else:#其余只按优先级
            下一批.sort(key=优先级排序键)#优先级升序
        记['entries']=tuple(下一批)#写回台账
        自身.标脏(名,记)#标脏
        if 子表 is not None:#声明子槽；空 dict 在 JS 为真
            本批=[]#攒齐再发布
            登记方=选项['registrant'] if 'registrant' in 选项 else None#登记方
            尾='' if 登记方 is None or 登记方=='' else ' ('+str(登记方)+')'#|| 空串
            for 子键,子规格 in 子表.items():#每个子槽
                子记=自身.取记录(子键)#取得或创建
                子记['spec']=子规格#规格
                子记['declaredBy']='an entry in "'+str(名)+'"'+尾#声明者
                子记['parent']=名#父
                子记['declarationEpoch']=子记['declarationEpoch']+1#抬世代
                本批.append((子键,子记))#攒
            for 子键,子记 in 本批:#标脏
                自身.标脏(子键,子记)#变更
            for _,子记 in 本批:#声明寿命
                自身.通知声明(子记)#同步
        def 拆除():
            """幂等；级联后过期拆除器空操作。身份用 is。"""
            当前=list(记['entries'])#当前台账
            仍在=False#是否仍在
            for 甲 in 当前:#扫
                if 甲 is 条目:#同对象
                    仍在=True#在
                    break#停
            if 仍在 is False:#已不在
                return#空操作
            记['entries']=tuple(甲 for 甲 in 当前 if 甲 is not 条目)#拿掉
            自身.标脏(名,记)#标脏
            自身.拆除条目(条目)#拆除
        return 拆除#拆除器

    def 仍存活(自身,条目):
        """渲染机械的过期授权探测。身份用 is。"""
        for 记 in 自身.记录表.values():#扫
            for 甲 in 记['entries']:#台账
                if 甲 is 条目:#同对象
                    return True#活
        return False#死

    def 取条目列表(自身,键):
        """变更之间引用稳定。"""
        if 键 not in 自身.记录表:#无
            return 空条目#空
        return 自身.记录表[键]['entries']#数组引用

    def 取槽位条目(自身,键):
        """投影每格遮蔽胜者。chain 不遮蔽；每次调用新元组。"""
        if 键 not in 自身.记录表:#无
            return 空条目#空
        记=自身.记录表[键]#记录
        if 记['spec'] is None:#未声明
            return 空条目#空
        种类=记['spec']['kind']#基数
        if 种类=='chain':#链
            return 记['entries']#原样
        胜者=[]#每格第一个活条目
        已见=set()#已见格
        for 条目 in 记['entries']:#按优先级扫
            if 条目['_id'] in 自身.已退位:#已退位
                continue#跳过
            形状=条目['options']#形状
            if 种类=='keyed':#keyed
                格=形状['key'] if 'key' in 形状 else None#格
            elif 种类=='list':#list
                格=形状['id'] if 'id' in 形状 else None#格
            else:#single
                格=None#共用
            if 格 in 已见:#已有胜者
                continue#跳过
            已见.add(格)#记下
            胜者.append(条目)#胜者
        return tuple(胜者)#元组

    def 规格(自身,键):
        """未声明为 None。"""
        if 键 not in 自身.记录表:#无
            return None#无
        return 自身.记录表[键]['spec']#规格

    def 动态规格(自身,键):
        """渲染器动态键逃生口。"""
        return 自身.规格(键)#同规格

    def 快照(自身,根=None):
        """导出声明拓扑。不含组件或可执行钩。"""
        def 建树(名,已见):
            """环或未声明则 None。"""
            if 名 not in 自身.记录表:#无
                return None#无
            记=自身.记录表[名]#记录
            if 记['spec'] is None or 名 in 已见:#丢掉
                return None#无
            支=set(已见)#本支
            支.add(名)#已见
            活动=set()#胜者 id
            for 甲 in 自身.取槽位条目(名):#胜者
                活动.add(id(甲))#身份
            子节点=[]#子树
            for 子名,候选 in 自身.记录表.items():#所有记录
                if 候选['spec'] is not None and 候选['parent']==名:#活子
                    节=建树(子名,支)#建
                    if 节 is not None:#可用
                        子节点.append(节)#记入
            占用者=[]#占用者表
            for 条目 in 记['entries']:#每个登记
                形=条目['options']#形状
                行={'priority':形['priority'] if 'priority' in 形 else 0,'active':id(条目) in 活动}#?? 0
                if 'registrant' in 条目:#登记方
                    行['registrant']=条目['registrant']#带上
                if 'key' in 形:#keyed
                    行['key']=形['key']#键
                if 'id' in 形:#list
                    行['id']=形['id']#id
                if 'order' in 形:#order
                    行['order']=形['order']#order
                占用者.append(行)#记入
            节点={#活槽节点
                'name':名,#槽键
                'kind':记['spec']['kind'],#基数
                'scope':记['spec']['scope'],#作用域
                'occupants':占用者,#占用者
                'children':子节点,#子树
            }#节点结束
            if 记['declaredBy'] is not None:#声明者
                节点['declaredBy']=记['declaredBy']#带上
            return 节点#返回
        if 根 is not None:#指定根
            节=建树(根,set())#建
            return [] if 节 is None else [节]#不可用则空
        结果=[]#活根表
        for 名,记 in 自身.记录表.items():#所有
            if 记['spec'] is None:#未声明
                continue#跳
            父=记['parent']#父
            if 父 is not None:#有父
                父记=自身.记录表[父] if 父 in 自身.记录表 else None#父记录
                if 父记 is not None and 父记['spec'] is not None:#父仍活
                    continue#非根
            节=建树(名,set())#建
            if 节 is not None:#可用
                结果.append(节)#记入
        return 结果#返回

    def 声明世代(自身,键):
        """首次声明前为 0。"""
        if 键 not in 自身.记录表:#无
            return 0#0
        return 自身.记录表[键]['declarationEpoch']#世代

    def 订阅(自身,键,回调):
        """微任务批处理；允许声明前订阅。"""
        记=自身.取记录(键)#取得或创建
        记['listeners'].add(回调)#加入
        def 退订():
            """从集合拿掉。"""
            记['listeners'].discard(回调)#删
        return 退订#退订器

    def 订阅声明(自身,键,回调):
        """同步通知。"""
        记=自身.取记录(键)#取得或创建
        记['declarationListeners'].add(回调)#加入
        def 退订():
            """从集合拿掉。"""
            记['declarationListeners'].discard(回调)#删
        return 退订#退订器

    def 版本(自身,键):
        """未碰过的键为 0。"""
        if 键 not in 自身.记录表:#无
            return 0#0
        return 自身.记录表[键]['version']#版本

    def 变更时(自身,回调):
        """同步触发、不批处理。"""
        自身.变更监听.add(回调)#加入
        def 退订():
            """从集合拿掉。"""
            自身.变更监听.discard(回调)#删
        return 退订#退订器

    def 报告条目错误(自身,键,条目,错误,信息):
        """abdicate 时一次性退位；重复退位空操作。信息为 dict。"""
        退位=信息['abdicate'] is True if 'abdicate' in 信息 else False#是否退位
        if 退位 is True:#遮蔽基数
            标识=条目['_id']#身份
            if 标识 in 自身.已退位:#已退位
                return#空操作
            自身.已退位.add(标识)#记下
            if 键 in 自身.记录表:#有
                自身.标脏(键,自身.记录表[键])#抬版本
        for 回调 in list(自身.条目错误监听):#快照后通知
            回调(键,条目,错误,{'abdicated':退位})#同步

    def 条目错误时(自身,回调):
        """每次报告同步触发。"""
        自身.条目错误监听.add(回调)#加入
        def 退订():
            """从集合拿掉。"""
            自身.条目错误监听.discard(回调)#删
        return 退订#退订器

    def 拆除条目(自身,条目):
        """拆除存储挂载并塌缩子槽。条目为 dict。"""
        存储=条目['store'] if 'store' in 条目 else None#存储
        if 存储 is not None and 是存储工厂(存储) is False:#共享句柄
            钉=自身.句柄作用域[id(存储)] if id(存储) in 自身.句柄作用域 else None#已钉
            if 钉 is not None:#有
                钉['count']-=1#减
                if 钉['count']==0:#归零
                    del 自身.句柄作用域[id(存储)]#拿掉
        子表=条目['children'] if 'children' in 条目 else None#子槽
        if 子表 is None:#无子；空 dict 在 JS 为真仍塌缩
            return#完
        for 子键 in 子表.keys():#每个子槽
            if 子键 not in 自身.记录表:#无
                continue#跳
            子记=自身.记录表[子键]#子记录
            注定=list(子记['entries'])#将被拆除
            子记['spec']=None#清规格
            子记['declaredBy']=None#清声明者
            子记['parent']=None#清父
            子记['declarationEpoch']=子记['declarationEpoch']+1#抬世代
            子记['entries']=空条目#清空
            自身.标脏(子键,子记)#标脏
            自身.通知声明(子记)#声明寿命
            for 死 in 注定:#递归
                自身.拆除条目(死)#拆除

    def 标脏(自身,键,记):
        """版本同步抬升。"""
        记['version']=记['version']+1#抬版本
        for 回调 in list(自身.变更监听):#同步通知
            回调(键)#调用
        自身.脏集.add(id(记))#记下待冲刷（用 id 因 set 要可哈希）
        自身.脏映射[id(记)]=记#映射
        if 自身.已排冲刷 is True:#已排
            return#幂等
        自身.已排冲刷=True#记下
        def 微任务冲刷():
            """冲刷 subscribe 监听。"""
            自身.冲刷()#冲刷
        threading.Timer(0,微任务冲刷).start()#近似 queueMicrotask

    def 通知声明(自身,记):
        """快照后调用。"""
        for 回调 in list(记['declarationListeners']):#快照
            回调()#调用

    def 冲刷(自身):
        """先复位，好让监听器内部的变更重新排程。"""
        自身.已排冲刷=False#复位
        脏=list(自身.脏集)#快照
        自身.脏集.clear()#清空
        for 标识 in 脏:#每个脏
            if 标识 not in 自身.脏映射:#无
                continue#跳
            记=自身.脏映射.pop(标识)#取出
            for 回调 in list(记['listeners']):#通知
                回调()#调用
