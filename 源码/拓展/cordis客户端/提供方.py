from .接口目录 import 查询服务目录,查询事件目录#目录查询
from .槽目录 import 客户端槽目录#槽目录（现场投影用；无 slots 不回退查询槽目录）

__all__=[#仅中文公开名
    '客户端内置巡检','列出客户端巡检提供方','门面钉死槽键','压缩槽树','巡检现场槽','说明',
]#公开面结束

说明='Slots.listSubTree / Theme.listTokens 需现场 slots/theme；其余为静态目录。'#说明

空输入={'type':'object','properties':{},'additionalProperties':False}#空
任意输出={'description':'JSON data owned by this inspect provider.'}#任意

客户端内置巡检=[#闭包符号
    {'name':'ctx','description':'Restricted Cordis Context. Prefer ctx.获取服务(name) with an undefined check; use inject only for hard dependencies.','signatures':['ctx.获取服务(name: string): unknown | undefined','ctx.监听(name: string, listener: Function): () => void','ctx.提供服务(name: string, value: unknown): () => void','ctx.副作用(callback: Function, label?: string): () => void']},
    {'name':'React','description':'React runtime exposed without JSX transformation.','signatures':['React.createElement(type, props, ...children): ReactElement','React.useState(initial)','React.useEffect(effect, deps)']},
    {'name':'host','description':'Package-private JSON RPC from Client to this Package\'s Host half.','signatures':['host.call(method: string, args?: JsonValue): Promise<JsonValue>']},
    {'name':'styles','description':'Package-owned stylesheet insertion cleaned up with the Client run.','signatures':['styles.insert(css: string): () => void']},
    {'name':'console','description':'Package-tagged browser logging.','signatures':['console.log(...values): void','console.error(...values): void']},
]#结束

门面钉死槽键={#门面钉死
    'tool.view.cordis':{#业务视图
        'description':'fixed by the dynamic Client Guard',#说明
        'values':[{'value':'self','description':'The only accepted key. The Guard binds it to this Package\'s pluginId and packageId.'}],#键
    },#结束
}#结束

def 精确输入(字段,说明文):#可选精确名
    """单字段对象。"""
    return {'type':'object','properties':{字段:{'type':'string','description':说明文}},'additionalProperties':False}#模式

def 读精确(输入,字段):#读字符串字段
    """仅字符串。"""
    if 输入 is None or isinstance(输入,list) or not isinstance(输入,dict):#非对象
        return None#无
    值=输入.get(字段)#取
    return 值 if isinstance(值,str) else None#串

def 登记(标识,说明文,方法,查询,输入模式=None,输出模式=None):#单方法提供方
    """组装登记。"""
    if 输入模式 is None:#缺省
        输入模式=空输入#空
    if 输出模式 is None:#缺省
        输出模式=任意输出#任意
    def 执行(请求方法,输入,_上下文=None):#查询
        """未知方法则抛。"""
        if 请求方法!=方法:#未知
            raise Exception(f'未知的 {标识} 巡检方法 "{请求方法}"')#抛
        return 查询(输入)#委托
    return {#登记
        'manifest':{#清单
            'id':标识,#id
            'description':说明文,#说明
            'methods':[{'name':方法,'description':说明文,'inputSchema':输入模式,'outputSchema':输出模式}],#方法
        },#清单
        'query':执行,#查询
    }#结束

def 压缩槽树(节点,目录图=None):#压缩现场树节点
    """有目录则附用途；工厂节点只留身份与子树。"""
    if 目录图 is None:#缺省
        目录图={槽['key']:槽 for 槽 in 客户端槽目录}#图
    类型=节点.get('type') if isinstance(节点,dict) else getattr(节点,'type',None)#节点类型
    名=节点.get('name') if isinstance(节点,dict) else getattr(节点,'name',None)#名
    if 类型=='factory':#工厂节点
        子=节点.get('children') if isinstance(节点,dict) else getattr(节点,'children',[]) or []#子
        return {'type':'factory','name':名,'scope':节点.get('scope') if isinstance(节点,dict) else getattr(节点,'scope',None),'children':[压缩槽树(c,目录图) for c in 子]}#工厂压缩
    条目=目录图.get(名)#目录
    钉死=门面钉死槽键.get(条目['key']) if 条目 else None#门面钉死键
    出={#压缩
        'type':类型,#槽类型
        'name':名,#名
        'kind':节点.get('kind') if isinstance(节点,dict) else getattr(节点,'kind',None),#基数
        'scope':节点.get('scope') if isinstance(节点,dict) else getattr(节点,'scope',None),#作用域
    }#基
    if 条目 is not None:#有目录
        出['purpose']=条目.get('summary')#用途
        出['replaceRisk']=条目.get('replaceRisk')#风险
        选项=条目.get('registerOptions') or []#选项
        if 选项:#有
            出['registration']=[{'name':o.get('name'),'type':o.get('type'),'required':o.get('requirement')=='required'} for o in 选项]#摘要
        if 条目.get('keyDomain'):#键域
            出['keyDomain']=钉死['description'] if 钉死 else 条目.get('keyDomain')#域
            if 钉死:#允许键
                出['allowedKeys']=[dict(v) for v in 钉死['values']]#键
    子=节点.get('children') if isinstance(节点,dict) else getattr(节点,'children',[]) or []#子
    出['children']=[压缩槽树(c,目录图) for c in 子]#递归
    return 出#节点

def 巡检槽目录条目(条目):#inspectSlotCatalog
    """目录条目完整投影。"""
    钉死=门面钉死槽键.get(条目.get('key'))#门面钉死键
    出={#投影
        'description':条目.get('doc'),#完整约定
        'registration':[{#选项
            'name':o.get('name'),'type':o.get('type'),
            'required':o.get('requirement')=='required','description':o.get('doc'),
        } for o in (条目.get('registerOptions') or [])],#map
        'ownerProps':list(条目.get('ownerProps') or []),#所有者 props
        'ownerPropsReferences':list(条目.get('ownerPropsReferences') or []),#引用
        'standardProps':list(条目.get('standardProps') or []),#标准
        'keyDomain':钉死['description'] if 钉死 else 条目.get('keyDomain'),#键域
        'hookContext':条目.get('hookContext'),#钩子
        'slotInject':条目.get('slotInject'),#注入面
        'replaceRisk':条目.get('replaceRisk'),#风险
    }#基
    if 钉死:#允许键
        出['allowedKeys']=[dict(v) for v in 钉死['values']]#键
    return 出#投影

def 巡检现场槽(节点,目录图=None):#inspectLiveSlot
    """现场槽完整约定 + 占用者；工厂节点返回身份与登记者。"""
    if 目录图 is None:#缺省
        目录图={槽['key']:槽 for 槽 in 客户端槽目录}#图
    类型=节点.get('type') if isinstance(节点,dict) else getattr(节点,'type',None)#节点类型
    名=节点.get('name') if isinstance(节点,dict) else getattr(节点,'name',None)#名
    if 类型=='factory':#工厂详情
        出={'type':'factory','name':名,'scope':节点.get('scope') if isinstance(节点,dict) else getattr(节点,'scope',None)}#身份
        登记者=节点.get('registrant') if isinstance(节点,dict) else getattr(节点,'registrant',None)#登记者
        if 登记者 is not None:#有
            出['registrant']=登记者#带上
        return 出#工厂
    条目=目录图.get(名)#目录
    出={#完整
        'type':类型,#槽类型
        'name':名,#名
        'kind':节点.get('kind') if isinstance(节点,dict) else getattr(节点,'kind',None),#基数
        'scope':节点.get('scope') if isinstance(节点,dict) else getattr(节点,'scope',None),#作用域
    }#基
    声明=节点.get('declaredBy') if isinstance(节点,dict) else getattr(节点,'declaredBy',None)#声明者
    if 声明 is not None:#有
        出['declaredBy']=声明#带
    占用=节点.get('occupants') if isinstance(节点,dict) else getattr(节点,'occupants',[]) or []#占用
    出['occupants']=[dict(o) if isinstance(o,dict) else o for o in 占用]#拷
    if 条目 is not None:#目录约定
        出['catalog']=巡检槽目录条目(条目)#投影
    return 出#完整

def 列出客户端巡检提供方(上下文=None):#内置提供方
    """静态目录 + 现场 slots/theme（无 slots 服务则抛，不静默回退目录）。"""
    服务输入=精确输入('service','Exact Service key. Omit it for the compact Service and method-signature directory.')#服务
    事件输入=精确输入('event','Exact Event name. Omit it for the compact Event and listener-signature directory.')#事件
    服务输出={'description':'Compact Service directory, or one exact Service contract with only its referenced type declarations.'}#出
    事件输出={'description':'Compact Event directory, or one exact Event contract with only its referenced type declarations.'}#出
    子树输入={'type':'object','properties':{'root':{'type':'string','description':'Exact live Slot key or factory:<name>. When supplied, selected contains that declaration.'}},'additionalProperties':False}#子树
    子树输出={'description':'Compact topology trees. An exact Slot includes its catalog and occupants; an exact Factory includes identity, scope, and registrant.'}#出

    def 查服务(输入):#服务查询
        """按键。"""
        return 查询服务目录(读精确(输入,'service'))#目录

    def 查事件(输入):#事件查询
        """按名。"""
        return 查询事件目录(读精确(输入,'event'))#目录

    def 查内置(_输入):#内置符号
        """符号表。"""
        return {'builtins':list(客户端内置巡检),'referencedTypes':[]}#表

    def 槽查询(输入):#Slots.listSubTree
        """现场快照；无 slots 对齐上游抛错。"""
        根=读精确(输入,'root')#根
        槽服务=上下文.获取服务('slots') if 上下文 is not None else None#服务
        if 槽服务 is None:#服务未跑
            raise Exception('客户端 Slots 服务未在运行')#抛——勿回退目录
        if not hasattr(槽服务,'snapshot'):#无快照面
            raise Exception('客户端 Slots 服务未在运行')#抛
        树列表=槽服务.snapshot(根)#快照
        选=树列表[0] if 树列表 else None#选中
        结果={'trees':[压缩槽树(树) for 树 in 树列表],'referencedTypes':[]}#树
        if 根 is not None:#请求根
            结果['requestedRoot']={'name':根,'available':len(树列表)>0}#是否存在
        if 根 is not None and 选 is not None:#完整投影
            结果['selected']=巡检现场槽(选)#inspectLiveSlot
        return 结果#结果

    def 主题查询(_输入):#Theme
        """导出令牌。"""
        主题=上下文.获取服务('theme') if 上下文 is not None else None#主题
        if 主题 is None:#无
            raise Exception('客户端 Theme 服务未在运行')#抛
        return {'tokens':主题.exportInspectTokens(),'referencedTypes':[]}#令牌

    def 槽执行(方法,输入,_上下文=None):#Slots.query
        """仅 listSubTree。"""
        if 方法!='listSubTree':#未知
            raise Exception(f'未知的 Slots 巡检方法 "{方法}"')#抛
        return 槽查询(输入)#委托

    return [#登记表
        登记('Service','Progressive Client Service discovery: compact capability/signature directory, then one exact coding contract.','listService',查服务,服务输入,服务输出),#服务
        登记('Event','Progressive Client Event discovery: compact listener directory, then one exact event contract.','listEvents',查事件,事件输入,事件输出),#事件
        登记('Builtin','Plain-JavaScript symbols available to a dynamic Client half.','listBuiltins',查内置),#内置
        {#Slots
            'manifest':{'id':'Slots','description':'Progressive live Slot inspection with explicit Slot and Factory topology nodes.','methods':[{'name':'listSubTree','description':'Return compact live Slot and Factory trees, plus available detail for one exact root.','inputSchema':子树输入,'outputSchema':子树输出}]},
            'query':槽执行,#查询
        },#Slots
        登记('Theme','Current theme token names and light/dark override requirements.','listTokens',主题查询),#Theme
    ]#全部
