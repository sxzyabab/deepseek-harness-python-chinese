from ...模块.客户端.通告 import 取握手窗口
import re
from ..语言设置 import (
    语言标识模式,
    语言标识表,
    语言偏好字段,
    语言设置命名空间,
)
from ..异常 import 本地化错误,抛非法语言标识,抛回退未登记
from ..词表 import 中文,英文,设置中文,设置英文
from ...存储 import 声明存储
from . import 语言行

__all__=[
    '语言行',
    '依赖','应用','语言运行时',
    '回退语言','公共命名空间','设置命名空间',
]

回退语言='en'#浏览器未点名已登记语言时打开这里，缺键也落到这里
公共命名空间='common'#跨功能公共词表
设置命名空间='settings.locale'#语言行自己的文案命名空间
依赖=['slots','remote','configForms']#槽位、远端和配置表单
占位模式=re.compile(r'\{([A-Za-z0-9_]+)\}')#模板 {name}
内置元数据={
    'zh':{'label':'中文','fallback':'en'},
    'en':{'label':'English'},
}
内置语言=tuple({'id':标识,**内置元数据[标识]} for 标识 in 语言标识表)


def 语言键(值):
    'BCP 47 风格 id 的大小写不敏感键'
    return 值.lower()


def 解析初始语言(语言表,语言顺序=None):
    '浏览器自己的语言优先于回退语言。壳没有给顺序、也没有页面时用回退语言'
    if 语言顺序 is None:
        顺序=[]
        try:
            导航=取握手窗口().navigator
            浏览器语言=导航.languages
            单标签=导航.language
        except Exception as 没有页面:
            #没有接上页面时读不到 navigator，按上游非浏览器处理
            浏览器语言=None
            单标签=None
            del 没有页面
        if isinstance(浏览器语言,(list,tuple)):
            for 项 in 浏览器语言:
                if isinstance(项,str):
                    顺序.append(项)
        if isinstance(单标签,str):
            顺序.append(单标签)
        语言顺序=顺序
    for 标签 in 语言顺序:
        请求=语言键(标签)
        for 定义 in 语言表:
            if 语言键(定义['id'])==请求:
                return 定义['id']
        主标签=请求.split('-')[0]
        for 定义 in 语言表:
            if 语言键(定义['id']).split('-')[0]==主标签:
                return 定义['id']
    return 回退语言


class 语言运行时:
    '词表注册表加语言偏好。查找先走当前语言的回退链，再走 common，最后露出键'
    def __init__(自身,上下文,宿主=None,引导=None):
        '种下随包语言。有宿主就订阅并采纳，不把临时语言写回去'
        自身.上下文=上下文
        自身.宿主=宿主
        自身.引导=引导
        自身.词表表={}
        自身.绑定表={}
        自身.目录={}
        自身.回退链表={}
        自身.监听者=set()
        for 语言 in 内置语言:
            自身.目录[语言键(语言['id'])]=语言
        语言表=自身.语言列表()
        顺序=None if 引导 is None else 引导['languages']
        自身.临时=解析初始语言(语言表,顺序)
        自身.偏好=None if 引导 is None else 引导['preference']
        自身.快照={
            'active':自身.解析当前(),
            'locales':语言表,
            'revision':0,
        }
        if 宿主 is not None:
            def 订阅采纳():
                '宿主变更时采纳，拆除时退订'
                def 采纳宿主():
                    '不把选择写回去'
                    自身.采纳(宿主)
                return 宿主.subscribe(采纳宿主)
            上下文.副作用(订阅采纳,'locale: settings scope adoption')
            自身.采纳(宿主)

    def getLocale(自身):
        '读取当前不可变语言快照'
        return 自身.快照

    def resolveText(自身,文本):
        '纯字符串原样返回。映射从回退链末端往当前语言叠，空字符串也算有译文'
        if isinstance(文本,str):
            return 文本
        结果=文本['en']
        链=自身.回退链(自身.快照['active'])
        下标=len(链)-1
        while 下标>=0:
            键=语言键(链[下标])
            if 键 in 文本 and 文本[键] is not None:
                结果=文本[键]
            下标=下标-1
        return 结果

    def getSnapshot(自身):
        'LocaleFace 的 getSnapshot，变更前引用不变'
        return 自身.快照

    def subscribe(自身,回调):
        '每次快照变更都通知，返回退订'
        自身.监听者.add(回调)
        def 退订():
            '取消这次订阅'
            自身.监听者.discard(回调)
        return 退订

    def setLocale(自身,标识):
        '切换当前语言。屏幕上已经是这个语言时也要写成显式偏好'
        命中=自身.目录.get(语言键(标识))
        if 命中 is None:
            raise 本地化错误('locale "'+标识+'" is not registered')
        自身.偏好=命中['id']
        if 自身.快照['active']!=命中['id']:
            自身.发布(命中['id'],True)
        if 自身.宿主 is not None:
            自身.宿主.set(语言偏好字段,命中['id'])

    def addLanguage(自身,登记):
        '加一种可选语言。回退必须已登记，并且最终到达英文'
        if 语言标识模式.fullmatch(登记['id']) is None:
            抛非法语言标识(登记['id'])
        if 登记['label'].strip()=='':
            raise 本地化错误('locale label must not be empty')
        if 语言标识模式.fullmatch(登记['fallback']) is None:
            raise 本地化错误(
                'locale fallback "'+登记['fallback']+'" is not a BCP 47-style tag',
            )
        候选={
            'id':登记['id'],
            'label':登记['label'],
            'fallback':登记['fallback'],
        }
        键=语言键(候选['id'])
        if 键 in 自身.目录:
            raise 本地化错误('locale "'+候选['id']+'" is already registered')
        回退=自身.目录.get(语言键(候选['fallback']))
        if 回退 is None:
            抛回退未登记(候选['fallback'])
        语言={
            'id':候选['id'],
            'label':候选['label'],
            'fallback':回退['id'],
        }
        自身.目录[键]=语言
        try:
            自身.断言回退链(语言['id'])
        except Exception as 错误:
            del 自身.目录[键]
            raise 错误
        自身.发布目录()
        def 拆除():
            '卸掉这一次登记的定义。已经换过定义就不动'
            if 自身.目录.get(键) is not 语言:
                return
            del 自身.目录[键]
            自身.发布目录()
        return 拆除

    def 采纳(自身,宿主):
        '采纳已接受的持久选择。分区还没到就保持现状'
        分区=宿主.getSnapshot()['value']
        if 分区 is None:
            return
        自身.偏好=分区.get('preference')
        目标=自身.解析当前()
        if 自身.快照['active']==目标:
            return
        自身.发布(目标,True)

    def 发布目录(自身):
        '重算浏览器回退，并发布当前目录'
        自身.回退链表.clear()
        语言表=自身.语言列表()
        顺序=None if 自身.引导 is None else 自身.引导['languages']
        自身.临时=解析初始语言(语言表,顺序)
        当前=自身.解析当前()
        自身.发布(当前,当前!=自身.快照['active'],语言表)

    def 解析当前(自身):
        '显式偏好只有目录里还有它时才生效'
        if 自身.偏好 is None:
            return 自身.临时
        命中=自身.目录.get(语言键(自身.偏好))
        if 命中 is None:
            return 自身.临时
        return 命中['id']

    def 语言列表(自身):
        '按登记顺序交出目录'
        return tuple(自身.目录.values())

    def 断言回退链(自身,起点):
        '新语言的整条回退必须到达英文'
        见过=set()
        当前=自身.目录.get(语言键(起点))
        while 当前 is not None:
            键=语言键(当前['id'])
            if 键 in 见过:
                raise 本地化错误('locale fallback cycle includes "'+当前['id']+'"')
            见过.add(键)
            if 键==语言键(回退语言):
                return
            回退标识=当前.get('fallback')
            if 回退标识 is None:
                raise 本地化错误(
                    'locale "'+当前['id']+'" fallback chain does not reach "'+回退语言+'"',
                )
            下一=自身.目录.get(语言键(回退标识))
            if 下一 is None:
                抛回退未登记(回退标识)
            当前=下一

    def 回退链(自身,起点):
        '查找链。中间语言卸掉时直接落到英文'
        起点键=语言键(起点)
        已缓存=自身.回退链表.get(起点键)
        if 已缓存 is not None:
            return 已缓存
        链=[]
        见过=set()
        当前=自身.目录.get(起点键)
        while 当前 is not None and 语言键(当前['id']) not in 见过:
            键=语言键(当前['id'])
            见过.add(键)
            链.append(当前['id'])
            回退标识=当前.get('fallback')
            if 回退标识 is None:
                当前=None
            else:
                当前=自身.目录.get(语言键(回退标识))
        if 语言键(回退语言) not in 见过:
            链.append(回退语言)
        定稿=tuple(链)
        自身.回退链表[起点键]=定稿
        return 定稿

    def register(自身,命名空间,语言或词表,词表=None):
        '一次登记一个命名空间。重复的命名空间和语言抛错，拆除只卸这一次写入'
        if isinstance(语言或词表,str):
            对表=[(语言或词表,词表)]
        else:
            对表=list(语言或词表.items())
        for 对 in 对表:
            if 语言标识模式.fullmatch(对[0]) is None:
                抛非法语言标识(对[0])
        语言表=自身.词表表.get(命名空间)
        if 语言表 is None:
            语言表={}
            自身.词表表[命名空间]=语言表
        for 语言,条目 in 对表:
            if 语言键(语言) in 语言表:
                raise 本地化错误(
                    'locale namespace "'+命名空间+'" already has locale "'+语言+'"',
                )
        for 语言,条目 in 对表:
            语言表[语言键(语言)]=条目
        自身.发布(自身.快照['active'],False)
        def 拆除():
            '幂等卸掉这一次写入的语言'
            拥有=自身.词表表.get(命名空间)
            if 拥有 is None:
                return
            删过=False
            for 语言,条目 in 对表:
                键=语言键(语言)
                if 拥有.get(键) is 条目:
                    del 拥有[键]
                    删过=True
            if 删过:
                自身.发布(自身.快照['active'],False)
        return 拆除

    def bind(自身,命名空间):
        '同一命名空间始终返回同一个翻译函数'
        已有=自身.绑定表.get(命名空间)
        if 已有 is not None:
            return 已有
        def 译(键,参数=None):
            '调用时读取当前语言'
            return 自身.翻译(命名空间,键,参数)
        自身.绑定表[命名空间]=译
        return 译

    def 翻译(自身,命名空间,键,参数=None):
        '条目命名空间，然后 common，最后露出键本身'
        链=自身.回退链(自身.快照['active'])
        模板=自身.查找(命名空间,键,链)
        if 模板 is None and 命名空间!=公共命名空间:
            模板=自身.查找(公共命名空间,键,链)
        if 模板 is None:
            模板=键
        if 参数 is None:
            return 模板
        结果=[]
        位置=0
        for 匹配 in 占位模式.finditer(模板):
            结果.append(模板[位置:匹配.start()])
            名=匹配.group(1)
            if 名 in 参数:
                结果.append(str(参数[名]))
            else:
                结果.append(匹配.group(0))
            位置=匹配.end()
        结果.append(模板[位置:])
        return ''.join(结果)

    def 查找(自身,命名空间,键,链):
        '沿回退链找模板。空字符串也算命中'
        语言表=自身.词表表.get(命名空间)
        for 语言 in 链:
            词表=None if 语言表 is None else 语言表.get(语言键(语言))
            if 词表 is not None and 键 in 词表:
                return 词表[键]
        return None

    def 发布(自身,当前,语言已变,语言表=None):
        '推进修订并通知订阅者。只有当前语言变了才发 locale/change'
        if 语言表 is None:
            语言表=自身.快照['locales']
        自身.快照={
            'active':当前,
            'locales':语言表,
            'revision':自身.快照['revision']+1,
        }
        if 语言已变:
            自身.上下文.广播('locale/change',自身.快照)
        for 回调 in list(自身.监听者):
            try:
                回调()
            except Exception as 错误:
                try:
                    取握手窗口().console.error('locale subscriber crashed:',错误)
                except Exception as 控制台失败:
                    print('locale subscriber crashed:',错误,控制台失败)


def 应用(上下文,配置=None):
    '提供语言服务，登记中英文案表，并把语言行放进常规设置'
    桥=None
    try:
        桥=__DSH_LOCALE__
    except NameError:
        桥=None
    if 桥 is None:
        try:
            候选=getattr(取握手窗口(),'__DSH_LOCALE__',None)
        except Exception as 没有页面:
            #页面上没有桥时跳过
            候选=None
            del 没有页面
        if 候选 is not None and 候选 is not ...:
            桥=候选
    引导=None
    if 桥 is not None:
        try:
            值=桥.read()
        except Exception as 错误:
            if 上下文.纤程.编号 is None:
                return
            raise 错误
        if 上下文.纤程.编号 is None:
            return
        if (
            not isinstance(值,dict)
            or 'languages' not in 值
            or not isinstance(值['languages'],list)
            or 'preference' not in 值
            or (值['preference'] is not None and not isinstance(值['preference'],str))
        ):
            raise TypeError('locale: invalid native initialization data')
        for 项 in 值['languages']:
            if not isinstance(项,str):
                raise TypeError('locale: invalid native initialization data')
        引导={'languages':值['languages'],'preference':值['preference']}
    宿主=上下文.configForms.get(语言设置命名空间)
    语言=语言运行时(上下文,宿主,引导)
    语言.register(公共命名空间,{'zh':中文,'en':英文})
    语言.register(设置命名空间,{'zh':设置中文,'en':设置英文})
    上下文.提供服务('locale',语言)
    if 桥 is not None:
        def 交给壳(快照):
            '把当前语言交给壳，不另写偏好'
            桥.onChange(快照['active'])
        上下文.监听('locale/change',交给壳)
        桥.onChange(语言.getSnapshot()['active'])
    上下文.slots.installLocale(语言)
    def 初始():
        '空选项，修订 -1，这样修订 0 仍算变更'
        return {'active':'','options':[],'revision':-1}
    def 同步动作(草稿,当前,选项,修订):
        '旧修订丢弃，否则写入'
        if 修订<=草稿['revision']:
            return
        草稿['active']=当前
        草稿['options']=选项
        草稿['revision']=修订
    存储=声明存储({
        'init':初始,
        'actions':{'sync':同步动作},
    })
    已绑=[None]
    def 同步():
        '文档语言和语言行仓库一起跟上快照'
        快照=语言.getSnapshot()
        try:
            文档=取握手窗口().document
            语言名='zh-CN' if 快照['active']=='zh' else 快照['active']
            根=文档.documentElement
            if 根.lang!=语言名:
                根.lang=语言名
        except Exception as 没有页面:
            #没有页面时跳过文档语言，语言仓库照常写
            del 没有页面
        动作=已绑[0]
        if 动作 is None:
            return
        动作['sync'](
            快照['active'],
            [{'id':项['id'],'label':项['label']} for 项 in 快照['locales']],
            快照['revision'],
        )
    def 挂同步():
        '语言行和文档语言跟着快照，拆除时退订'
        return 语言.subscribe(同步)
    上下文.副作用(挂同步,'locale: language row and document synchronization')
    同步()
    def 注入面(动作):
        '保存仓库动作，并立刻对齐当前快照'
        已绑[0]=动作
        同步()
        def 写入语言(标识):
            '写入偏好'
            语言.setLocale(标识)
        return {'setLocale':写入语言}
    def 登记行():
        '把语言行登记进常规条目槽'
        return 上下文.slots.register({
            'name':'settings.general.item',
            'id':'language',
            'order':0,
            'store':存储,
            'locale':设置命名空间,
            'inject':注入面,
        },语言行.语言行)
    上下文.slots.inject('settings.general.item',登记行)

inject=依赖
apply=应用
