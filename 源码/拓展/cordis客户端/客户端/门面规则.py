from ....依赖.cordis.上下文 import 是上下文#服务返回值不能是上下文
from ..异常 import 错误,拒绝门面#门面拒绝


__all__=['动态上下文门面','拒绝上下文返回','上下文动词','定时器动词']


上下文动词=frozenset([#门面动词。线协议原名
    'effect','on','once','provide','timeout','interval','setTimeout','setInterval','throttle','debounce',
])
定时器动词=frozenset([#要先 inject timer
    'timeout','interval','setTimeout','setInterval','throttle','debounce',
])
动词对照={#上下文上的真实方法
    'effect':'副作用',
    'on':'监听',
    'once':'监听一次',
    'provide':'提供服务',
    'timeout':'timeout',
    'interval':'interval',
    'setTimeout':'setTimeout',
    'setInterval':'setInterval',
    'throttle':'throttle',
    'debounce':'debounce',
}


def 拒绝上下文返回(值,服务名,环境):
    '服务返回上下文就拒绝，否则原样返回'
    if 是上下文(值):#不能把别的上下文交出去
        拒绝门面(环境,
            'service "'+服务名+'" returned a cordis Context, which the dynamic facade does not expose. '
            'Operate through your own plugin ctx and the services you declared — never another context.',
        )
    return 值


class 动态上下文:
    '动态插件看到的上下文。动词、已声明服务，以及 slots 与 theme 的额外规则'
    def __init__(自身,上下文,环境):
        '记下真实上下文和这一包的账本'
        自身.上下文=上下文#插件纤程的上下文
        自身.环境=环境#包、账本、认领、优先级、报告
        自身.已声明=set(上下文.纤程.依赖表.keys())#inject
        自身.页面助手=None#求值时填上，用来调用留在页面上的函数

    def 拒绝读取(自身,属性):
        '没声明，或根本没有这个名字'
        if 自身.上下文.获取服务(属性,False) is not None:#服务在，只是没声明
            拒绝门面(自身.环境,
                'service "'+属性+'" is not declared by your plugin. Declare it on the plugin you return: '
                +"{ inject: ['"+属性+"', …], apply(ctx) { … } } — a plain `function` has no declaration site, "
                +'so use the object form. The runtime then parks the package if the provider unloads.',
            )
        拒绝门面(自身.环境,
            'dynamic ctx does not expose "'+属性+'". Available: ctx.on / ctx.provide / timer helpers after injecting timer, and any service your '
            +'returned plugin declared in inject (slots and theme are the usual UI seats). Framework internals are withheld '
            +'by design.',
        )

    def 询问(自身,属性):
        '这个键在门面上是否可见'
        if 属性=='get':#可选查找
            return True
        if 属性 in 上下文动词 and (属性 not in 定时器动词 or 'timer' in 自身.已声明):#动词
            return True
        return 属性 in 自身.已声明

    def 读取(自身,属性):
        'Proxy get 的结果。kind 为 call、service 或 value'
        if 属性=='get' or 属性 in 上下文动词:#动词
            return {'kind':'call'}
        if 属性 not in 自身.已声明:#没声明
            自身.拒绝读取(属性)#抛
        return {'kind':'service','name':属性}

    def 写入(自身,属性,_值):
        '门面只读'
        拒绝门面(自身.环境,'dynamic ctx is read-only; cannot assign "'+str(属性)+'"')

    def 调用(自身,属性,参数):
        '按动词、get、slots、theme 或普通服务方法调用'
        if 参数 is None:#没带
            参数=[]#空
        if 属性=='get':#可选查找
            return 自身.读服务(参数[0] if 参数 else '',False)
        if 属性 in 上下文动词:#生命周期动词
            if 属性 in 定时器动词 and 'timer' not in 自身.已声明:#定时器没声明
                自身.拒绝读取('timer')#抛
            方法=getattr(自身.上下文,动词对照[属性])#真实方法
            return 方法(*参数)
        if 属性.startswith('slots.'):#槽
            return 自身.槽调用(属性[len('slots.'):],参数)
        if 属性.startswith('theme.'):#主题
            return 自身.主题调用(属性[len('theme.'):],参数)
        if 属性.startswith('service.'):#普通服务
            余下=属性[len('service.'):]#名字.方法
            点=余下.find('.')#分隔
            名字=余下 if 点<0 else 余下[:点]#服务名
            方法名=余下[点+1:] if 点>=0 else ''#方法
            return 自身.服务调用(名字,方法名,参数)
        自身.拒绝读取(属性)#没有这个动词

    def 读服务(自身,名字,必须声明):
        '取服务。页面要的是 kind 描述，Python 调用拿到座位对象'
        if 必须声明 and 名字 not in 自身.已声明:#没声明
            自身.拒绝读取(名字)#抛
        服务=拒绝上下文返回(自身.上下文.获取服务(名字,False),名字,自身.环境)#先拒上下文
        if 服务 is None or isinstance(服务,(str,int,float,bool)):#没有或标量
            return {'kind':'value','value':服务}
        if 名字=='slots':#槽座位
            return 槽座位(自身)
        if 名字=='theme':#主题座位
            return 主题座位(自身)
        return 服务座位(自身,名字,服务)

    def 解开(自身,组件):
        '页面函数按编号留在页面上，这里包成渲染器能调用的函数'
        if isinstance(组件,dict) and '__函数' in 组件 and 自身.页面助手 is not None:#页面函数
            编号=组件['__函数']#编号
            助手=自身.页面助手#助手
            def 包装(属性=None,当前=编号):
                '把属性交回页面上的组件'
                return 助手.调用回调(当前,属性)
            return 包装
        return 组件

    def 槽服务(自身):
        '调用方上下文上的槽服务'
        return 自身.上下文.获取服务('slots',False)

    def 槽调用(自身,方法名,参数):
        'register 和 registerFactory 改写选项并认领，其余方法原样转发'
        槽=自身.槽服务()#槽
        if 方法名 not in ('register','registerFactory'):#普通方法
            方法=getattr(槽,方法名)#方法
            if not callable(方法):#不是函数
                return 拒绝上下文返回(方法,'slots',自身.环境)
            return 拒绝上下文返回(方法(*[自身.解开(项) for 项 in 参数]),'slots',自身.环境)
        原始=参数[0] if len(参数)>0 else None#选项
        组件=自身.解开(参数[1] if len(参数)>1 else None)#组件
        if not isinstance(原始,dict):#没有选项对象
            拒绝门面(自身.环境,'slots.register(options, component) needs an options object with a `name`')
        选项=dict(原始)#拷一份再改
        槽名=选项.get('name')#槽名
        if not isinstance(槽名,str) or 槽名=='':#缺名字
            拒绝门面(自身.环境,'slots.'+方法名+' options need a string `name`')
        if 方法名=='registerFactory':#工厂不分配优先级
            拆除=槽.registerFactory(选项,组件)#登记
            自身.环境['账本'].append({'slot':'factory:'+槽名,'priority':None})#记账
            自身.环境['认领'](组件)#认领
            return 拆除
        if 槽名=='tool.view.cordis':#业务视图只接受 self
            if 选项.get('key')!='self':#别的 key
                拒绝门面(自身.环境,'tool.view.cordis only accepts key "self"; the runtime binds it to this Package')
            选项['key']=自身.环境['包']['pluginId']+'.'+自身.环境['包']['packageId']#钉死到这个包
        规格=槽.spec(槽名)#运行时规格
        优先级=选项.get('priority')#调用方写的
        if 规格 is None or 规格.get('kind')!='chain':#遮蔽型分配优先级
            优先级=自身.环境['分配优先级']()#后登记更前
            选项['priority']=优先级#写回
        拆除=槽.register(选项,组件)#登记成功后才记账
        自身.环境['账本'].append({'slot':槽名,'priority':优先级})#记账
        自身.环境['认领'](组件)#认领
        return 拆除

    def 主题调用(自身,方法名,参数):
        'overrideTokens 的来源钉死为包标识，其余方法原样转发'
        主题=自身.上下文.获取服务('theme',False)#主题
        if 方法名!='overrideTokens' and 方法名!='覆盖令牌':#普通方法
            真实名=方法名#页面上的名字
            if not hasattr(主题,真实名) and 方法名=='exportInspectTokens':#中文实现
                真实名='导出检视令牌'
            方法=getattr(主题,真实名)#方法
            if not callable(方法):#不是函数
                return 拒绝上下文返回(方法,'theme',自身.环境)
            return 拒绝上下文返回(方法(*参数),'theme',自身.环境)
        源=参数[0] if len(参数)>0 else None#第一参
        令牌=参数[1] if len(参数)>1 else None#第二参
        if 令牌 is None and isinstance(源,dict):#把令牌图当成了第一参
            拒绝门面(自身.环境,
                'theme.overrideTokens(source, tokens) takes two arguments; source is replaced with your package id, '
                +"so pass any string first and the token map second: overrideTokens('mine', { '--dsw-alias-…': { light: '…', dark: '…' } })",
            )
        钉死=自身.环境['包']['pluginId']+'.'+自身.环境['包']['packageId']#包标识
        拆除=主题.覆盖令牌(钉死,令牌)#来源不被信任
        def 执行体():
            '卸载时拆掉这一层'
            return 拆除
        自身.上下文.副作用(执行体,'cordis-client-runner: dynamic theme override layer')#跟调用方纤程
        return 拆除

    def 服务调用(自身,名字,方法名,参数):
        '普通服务。返回值若是上下文则拒绝'
        if 名字 not in 自身.已声明:#没声明
            自身.拒绝读取(名字)#抛
        服务=拒绝上下文返回(自身.上下文.获取服务(名字,False),名字,自身.环境)#服务
        if 方法名=='':#读服务本身
            return 服务
        方法=getattr(服务,方法名,None)#方法
        if not callable(方法):#属性或没有这个名字
            return 拒绝上下文返回(方法,名字,自身.环境)
        return 拒绝上下文返回(方法(*[自身.解开(项) for 项 in 参数]),名字,自身.环境)

    def __getattr__(自身,属性):
        'Python 侧按门面规则读'
        if 属性.startswith('_'):#私有
            raise AttributeError(属性)
        if 属性=='slots' and 'slots' in 自身.已声明:#槽
            return 槽座位(自身)
        if 属性=='theme' and 'theme' in 自身.已声明:#主题
            return 主题座位(自身)
        结果=自身.读取(属性)#规则
        if isinstance(结果,dict) and 结果.get('kind')=='call':#动词
            def 包装(*参数,当前=属性):
                '转发这个动词'
                return 自身.调用(当前,参数)
            return 包装
        if isinstance(结果,dict) and 结果.get('kind')=='service':#服务
            return 自身.读服务(结果['name'],True)
        if isinstance(结果,dict) and 结果.get('kind')=='value':#值
            return 结果.get('value')
        return 结果


class 槽座位:
    'slots.register 会改写优先级并认领'
    def __init__(自身,门面):
        '记下门面'
        自身.门面=门面#门面
    def __getattr__(自身,属性):
        '转到槽调用'
        def 包装(*参数,当前=属性):
            '调用槽方法'
            return 自身.门面.槽调用(当前,参数)
        return 包装


class 主题座位:
    'theme.overrideTokens 的来源钉死为包标识'
    def __init__(自身,门面):
        '记下门面'
        自身.门面=门面#门面
    def __getattr__(自身,属性):
        '转到主题调用'
        def 包装(*参数,当前=属性):
            '调用主题方法'
            return 自身.门面.主题调用(当前,参数)
        return 包装


class 服务座位:
    '普通服务。方法返回上下文则拒绝'
    def __init__(自身,门面,名字,服务):
        '记下服务'
        自身.门面=门面#门面
        自身.名字=名字#服务名
        自身.服务=服务#真实服务
    def __getattr__(自身,属性):
        '转到服务调用'
        def 包装(*参数,当前=属性):
            '调用服务方法'
            return 自身.门面.服务调用(自身.名字,当前,参数)
        return 包装


def 动态上下文门面(上下文,环境):
    '动态插件 apply 拿到的门面'
    return 动态上下文(上下文,环境)
