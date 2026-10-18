from ..异常 import 错误#未知巡检方法
from .槽名录 import 客户端槽api#编译期槽目录


__all__=['登记提供方','读精确','压缩槽树','查看活动槽','空输入','任意输出','服务输入','事件输入','服务输出','事件输出','子树输入','子树输出','客户端内建巡检']


空输入={'type':'object','properties':{},'additionalProperties':False}#无参数
任意输出={'description':'JSON data owned by this inspect provider.'}#未特化的输出


def 精确输入(字段,说明):
    '只接受一个可选字符串字段'
    return {'type':'object','properties':{字段:{'type':'string','description':说明}},'additionalProperties':False}


服务输入=精确输入('service','Exact Service key. Omit it for the compact Service and method-signature directory.')#服务查询
事件输入=精确输入('event','Exact Event name. Omit it for the compact Event and listener-signature directory.')#事件查询
服务输出={'description':'Compact Service directory, or one exact Service contract with only its referenced type declarations.'}#服务结果
事件输出={'description':'Compact Event directory, or one exact Event contract with only its referenced type declarations.'}#事件结果
子树输出={'description':'Compact topology trees. An exact Slot includes its catalog and occupants; an exact Factory includes identity, scope, and registrant.'}#子树结果
子树输入={#子树查询
    'type':'object',
    'properties':{
        'root':{
            'type':'string',
            'description':'Exact live Slot key or factory:<name>. When supplied, selected contains that declaration.',
        },
    },
    'additionalProperties':False,
}
客户端内建巡检=[#求值器和门面暴露的符号
    {
        'name':'ctx',
        'description':'Restricted Cordis Context. Prefer ctx.get(name) with an undefined check; use inject only for hard dependencies.',
        'signatures':[
            'ctx.get(name: string): unknown | undefined',
            'ctx.on(name: string, listener: Function): () => void',
            'ctx.provide(name: string, value: unknown): () => void',
            'ctx.effect(callback: Function, label?: string): () => void',
        ],
    },
    {
        'name':'React',
        'description':'React runtime exposed without JSX transformation.',
        'signatures':['React.createElement(type, props, ...children): ReactElement','React.useState(initial)','React.useEffect(effect, deps)'],
    },
    {
        'name':'host',
        'description':"Package-private JSON RPC from Client to this Package's Host half.",
        'signatures':['host.call(method: string, args?: JsonValue): Promise<JsonValue>'],
    },
    {
        'name':'styles',
        'description':'Package-owned stylesheet insertion cleaned up with the Client run.',
        'signatures':['styles.insert(css: string): () => void'],
    },
    {
        'name':'console',
        'description':'Package-tagged browser logging.',
        'signatures':['console.log(...values): void','console.error(...values): void'],
    },
]
槽目录={项['key']:项 for 项 in 客户端槽api}#键到目录行
门面槽键={#动态门面改写过的键域
    'tool.view.cordis':{
        'description':'fixed by the dynamic Client Guard',
        'values':[{
            'value':'self',
            'description':"The only accepted key. The Guard binds it to this Package's pluginId and packageId.",
        }],
    },
}


def 登记提供方(标识,说明,方法,查询,输入模式=None,输出模式=None):
    '一份提供方登记。查询名对不上就抛'
    if 输入模式 is None:#默认空对象
        输入模式=空输入
    if 输出模式 is None:#默认任意输出
        输出模式=任意输出
    def 查询方法(请求名,输入,上下文=None):
        '只接受登记的那一个方法'
        if 请求名!=方法:#未知方法
            raise 错误('unknown '+标识+' inspect method "'+请求名+'"')
        return 查询(输入)
    return {#登记
        'manifest':{
            'id':标识,
            'description':说明,
            'methods':[{
                'name':方法,
                'description':说明,
                'inputSchema':输入模式,
                'outputSchema':输出模式,
            }],
        },
        'query':查询方法,
    }


def 读精确(输入,字段):
    '对象上的可选字符串。没有或类型不对就是没有'
    if 输入 is None or not isinstance(输入,dict):#不是对象
        return None
    值=输入.get(字段)#字段
    if isinstance(值,str):#字符串
        return 值
    return None


def 压缩槽树(节点):
    '目录上的用途、登记项和键域。工厂只留名字、范围和子节点'
    if 节点.get('type')=='factory':#工厂
        return {#工厂节点
            'type':节点['type'],
            'name':节点['name'],
            'scope':节点['scope'],
            'children':[压缩槽树(子) for 子 in 节点.get('children') or []],
        }
    目录=槽目录.get(节点.get('name'))#编译期目录
    守卫=None if 目录 is None else 门面槽键.get(目录['key'])#门面改写
    结果={#槽节点
        'type':节点['type'],
        'name':节点['name'],
        'kind':节点['kind'],
        'scope':节点['scope'],
    }
    if 目录 is not None:#有目录
        结果['purpose']=目录['summary']#用途
        结果['replaceRisk']=目录['replaceRisk']#替换风险
        if len(目录['registerOptions'])>0:#有登记项
            结果['registration']=[{#登记项
                'name':选项['name'],
                'type':选项['type'],
                'required':选项['requirement']=='required',
            } for 选项 in 目录['registerOptions']]
        if 目录['keyDomain']!='':#有键域
            结果['keyDomain']=守卫['description'] if 守卫 is not None else 目录['keyDomain']#键域
            if 守卫 is not None:#门面允许的键
                结果['allowedKeys']=[dict(项) for 项 in 守卫['values']]
    结果['children']=[压缩槽树(子) for 子 in 节点.get('children') or []]#子节点
    return 结果


def 查看活动槽(节点):
    '一个精确根的详情。工厂带登记者，槽带占用者和目录'
    if 节点.get('type')=='factory':#工厂
        结果={'type':节点['type'],'name':节点['name'],'scope':节点['scope']}#工厂
        if 节点.get('registrant') is not None:#有登记者
            结果['registrant']=节点['registrant']#登记者
        return 结果
    目录=槽目录.get(节点.get('name'))#目录
    结果={#槽
        'type':节点['type'],
        'name':节点['name'],
        'kind':节点['kind'],
        'scope':节点['scope'],
        'occupants':[dict(占用) for 占用 in 节点.get('occupants') or []],
    }
    if 节点.get('declaredBy') is not None:#谁声明的
        结果['declaredBy']=节点['declaredBy']#声明者
    if 目录 is not None:#目录详情
        守卫=门面槽键.get(目录['key'])#门面键
        详情={#目录
            'description':目录['doc'],
            'registration':[{
                'name':选项['name'],
                'type':选项['type'],
                'required':选项['requirement']=='required',
                'description':选项['doc'],
            } for 选项 in 目录['registerOptions']],
            'ownerProps':list(目录['ownerProps']),
            'ownerPropsReferences':list(目录['ownerPropsReferences']),
            'standardProps':list(目录['standardProps']),
            'keyDomain':守卫['description'] if 守卫 is not None else 目录['keyDomain'],
            'hookContext':目录['hookContext'],
            'slotInject':目录['slotInject'],
            'replaceRisk':目录['replaceRisk'],
        }
        if 守卫 is not None:#允许的键
            详情['allowedKeys']=[dict(项) for 项 in 守卫['values']]
        结果['catalog']=详情#目录
    return 结果
