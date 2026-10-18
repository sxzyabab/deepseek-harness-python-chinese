from ...模块.客户端.通告 import 取握手窗口
from ...ui_基础界面组件.icons import 图标
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.模态 import 模态
from ...ui_基础界面组件.分段控制 import 分段控制
from ...ui_对话.异常 import 挂上
from .文案 import 中文
from .存储 import 推导密钥引用,协议选项,推理档位选项,提供方可用
from .提供方编辑器 import 提供方编辑器
from .自定义提供方卡片 import 自定义提供方卡片
from .编辑器页脚 import 建,清空子,采集焦点,还原焦点,样式模块

__all__=['模型分区','密钥已配','目标自','提供方文案']

def 密钥已配(行):
    '档案点了引用就看那条凭据，否则看页面推导出来的引用'
    if 行.get('apiKeyEnv') is not None:
        凭据=行.get('credential')
        return isinstance(凭据,dict) and 凭据.get('configured') is True
    派生=行.get('derivedCredential')
    return isinstance(派生,dict) and 派生.get('configured') is True

def 目标自(行):
    '编辑器要的身份。托管引用只在约定引用已配置且可写时带上'
    条目=行['entry']
    托管=推导密钥引用(条目['provider'])
    目标={
        'provider':条目['provider'],
        'displayName':条目['displayName'],
        'settingsNs':条目['settingsNs'],
        'settingsPath':条目['settingsPath'],
    }
    凭据=行.get('credential')
    if 行.get('apiKeyEnv')==托管 and isinstance(凭据,dict) and 凭据.get('configured') is True and 凭据.get('writable') is True:
        目标['credentialRef']=托管
    if 条目.get('declared') is True:
        目标['declared']=True
    if 条目.get('defaultBaseURL') is not None:
        目标['defaultBaseURL']=条目['defaultBaseURL']
    if 条目.get('baseURLEnv') is not None:
        目标['baseURLEnv']=条目['baseURLEnv']
    if 条目.get('nativeAuth') is not None:
        目标['nativeAuth']=条目['nativeAuth']
    return 目标

def 提供方文案(模板,目标):
    '把 {provider} 换成显示名；和路由相同就只写路由'
    if 目标['provider']==目标['displayName']:
        标签=目标['provider']
    else:
        标签=目标['displayName']+' ('+目标['provider']+')'
    return 模板.replace('{provider}',标签)

class 模型分区:
    '模型设置页：提供方行、一次一张编辑卡、添加和删除确认'
    def __init__(自身,属性):
        '记下注入面。添加和删除的本地状态从关开始'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.编辑中=None
        自身.添加开=False
        自身.添加方式='catalog'
        自身.已访问=set()
        自身.目录忙=False
        自身.自定义忙=False
        自身.删除目标=None
        自身.删除中=False
        自身.删除失败=None
        自身.已保存=None
        自身.已关装卡=set()
        自身.快照门=None
        自身.添加编号='models-add-'+str(id(自身))
        自身.目录编辑器=None
        自身.自定义实例=None
        自身.行编辑器=None
        自身.装卡={}
        自身.根=None
        自身.绘制中=False
        自身.待重画=False
        自身.已订=False
        自身.退订=None
        自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '整页。快照变了重画，焦点按 data-dsh-focus 放回'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        try:
            自身.画出()
        finally:
            自身.绘制中=False
        if 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

    def 画出(自身):
        '按快照画行、添加卡和删除确认'
        属性=自身.属性
        if 属性.get('controller') is None or 属性.get('useSnapshot') is None or 属性.get('operations') is None or 属性.get('schema') is None or 属性.get('t') is None:
            return 自身.根
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        快照钩=属性['useSnapshot']
        def 全量(快照):
            '整份页面快照'
            return 快照
        快照=快照钩(全量)
        if 快照.get('status')=='idle':
            属性['controller'].加载()
            快照=快照钩(全量)
        行表=[]
        for 行 in 快照.get('rows') or []:
            if 行['entry']['provider']=='deepseek-account':
                条目=dict(行['entry'])
                条目['displayName']=中文['deepSeekAccount']
                新行=dict(行)
                新行['entry']=条目
                行表.append(新行)
            else:
                行表.append(行)
        状态=dict(快照)
        状态['rows']=行表
        if 自身.快照门 is None:
            自身.快照门=状态.get('status')=='ready'
        if 状态.get('status')=='ready' and 自身.快照门 is False:
            自身.快照门=True
        if 状态.get('status')=='error' and 自身.快照门 is True:
            自身.快照门=False
        焦点=None
        if 自身.根 is None:
            自身.根=建(文档,'div','section')
            父=属性.get('parent')
            if 父 is not None:
                父.appendChild(自身.根)
        else:
            焦点=采集焦点(文档,自身.根)
            清空子(自身.根)
        if 状态.get('status')=='error':
            文=状态.get('error')
            if 文 is None:
                文=''
            错=建(文档,'p','error')
            错.textContent=中文['loadFailed']+': '+str(文)
            自身.根.appendChild(错)
            重=建(文档,'button','secondaryButton')
            重.type='button'
            重.textContent=中文['retry']
            def 点重(事件):
                '再拉一次目录'
                属性['controller'].加载()
                自身.渲染()
            重.addEventListener('click',点重)
            自身.根.appendChild(重)
            自身.订上()
            还原焦点(文档,焦点)
            return
        if 自身.快照门 is not True and 状态.get('status')!='ready':
            题=建(文档,'h2','title')
            题.textContent=中文['title']
            自身.根.appendChild(题)
            导=建(文档,'p','intro')
            导.textContent=中文['intro']
            自身.根.appendChild(导)
            自身.订上()
            还原焦点(文档,焦点)
            return
        已存身份=自身.已保存
        if 已存身份 is not None:
            找到=None
            for 行 in 状态['rows']:
                if 行['entry']['provider']==已存身份['provider']:
                    找到=行
                    break
            if 找到 is not None:
                已存身份={
                    'provider':找到['entry']['provider'],
                    'displayName':找到['entry']['displayName'],
                }
        任一可用=False
        for 行 in 状态['rows']:
            if 提供方可用(行):
                任一可用=True
                break
        已配置=[]
        可配=[]
        可添加=[]
        空间=状态.get('namespaces')
        if isinstance(空间,dict) is False:
            空间={}
        for 行 in 状态['rows']:
            if 行.get('configured') is True:
                已配置.append(行)
            if 行['entry']['settingsNs'] in 空间:
                可配.append(行)
            命名空间=空间.get(行['entry']['settingsNs'])
            if 命名空间 is not None and 行.get('configured') is not True:
                可添加.append({'row':行,'namespace':命名空间})
        派=空间.get('llm-pi-ai')
        协议=协议选项(派,属性['schema'])
        推理=推理档位选项(派,属性['schema'])
        目录提供=len(可配)>0
        目录可加=len(可添加)>0
        自定义提供=派 is not None
        自定义可加=len(协议)>0
        两种=目录提供 and 自定义提供
        if 两种:
            方式=自身.添加方式
        elif 自定义提供:
            方式='custom'
        else:
            方式='catalog'
        锁=自身.目录忙 or 自身.自定义忙
        草稿=None
        if 自身.添加开 and 目录提供:
            留=None
            if 自身.编辑中 is not None:
                留=空间.get(自身.编辑中.get('settingsNs'))
            if 自身.编辑中 is not None and 留 is not None:
                草稿={'target':自身.编辑中,'namespace':留}
            elif len(可添加)>0:
                草稿={'target':目标自(可添加[0]['row']),'namespace':可添加[0]['namespace']}
        添加行=None
        if 草稿 is not None:
            for 行 in 状态['rows']:
                if 行['entry']['provider']==草稿['target']['provider']:
                    添加行=行
                    break
        题=建(文档,'h2','title')
        题.textContent=中文['title']
        自身.根.appendChild(题)
        导=建(文档,'p','intro')
        导.textContent=中文['intro']
        自身.根.appendChild(导)
        if 状态.get('writable') is not True and 状态.get('status')=='ready':
            注=建(文档,'p','notice')
            注.textContent=中文['readOnly']
            自身.根.appendChild(注)
        if 已存身份 is not None:
            存=建(文档,'p','savedNotice')
            存.setAttribute('role','status')
            存.setAttribute('aria-live','polite')
            存.textContent=提供方文案(中文['savedProvider'],已存身份)
            自身.根.appendChild(存)
        列表=建(文档,'ul','rows')
        for 行 in 已配置:
            目标=目标自(行)
            命名空间=空间.get(目标['settingsNs'])
            if 命名空间 is None:
                continue
            项=None
            需要装=任一可用 is False and 行['entry']['provider']!='deepseek-account' and len(行['entry']['settingsPath'])==0 and (isinstance(行.get('credential'),dict) is False or 行['credential'].get('configured') is not True)
            if 需要装 and 行['entry']['provider'] not in 自身.已关装卡:
                项=建(文档,'li','setupCard')
                if 行['entry'].get('error') is not None:
                    错=建(文档,'p','error')
                    错.setAttribute('role','alert')
                    错.textContent=str(行['entry']['error'])
                    项.appendChild(错)
                挂上(项,自身.取编辑器('装-'+目标['provider'],{
                    'window':窗口,
                    'provider':目标['provider'],
                    'displayName':目标['displayName'],
                    'settingsPath':目标['settingsPath'],
                    'namespace':命名空间,
                    'schema':属性['schema'],
                    'operations':属性['operations'],
                    'readOnly':状态.get('writable') is not True,
                    'credential':行.get('credential'),
                    'credentialChecks':行.get('credentialChecks'),
                    'defaultBaseURL':目标.get('defaultBaseURL'),
                    'baseURLEnv':目标.get('baseURLEnv'),
                    'nativeAuth':目标.get('nativeAuth'),
                    'declared':True if 目标.get('declared') is True else None,
                    'onClose':自身.关装(目标),
                }))
                槽=属性.get('renderSlot')
                if 槽 is not None:
                    挂上(项,槽(
                        'settings.models.provider-card',
                        {'provider':行['entry'],'configured':行.get('configured'),'keyConfigured':密钥已配(行)},
                        {'entryKey':行['entry']['settingsNs']},
                    ))
                列表.appendChild(项)
                continue
            开着=自身.添加开 is not True and 自身.编辑中 is not None and 自身.编辑中.get('provider')==行['entry']['provider']
            凭据已配=isinstance(行.get('credential'),dict) and 行['credential'].get('configured') is True
            凭据缺=凭据已配 is not True and 行.get('apiKeyEnv') is not None and isinstance(行.get('credential'),dict) and 行['credential'].get('configured') is False
            项=建(文档,'li','rowCard')
            头=建(文档,'div','rowHead')
            身份=建(文档,'span','rowIdentity')
            名=建(文档,'span','rowName')
            名.textContent=行['entry']['displayName']
            身份.appendChild(名)
            if 行['entry'].get('declared') is True:
                签=建(文档,'span','rowTag')
                签.textContent=中文['customTag']
                身份.appendChild(签)
            if 行['entry']['provider']=='deepseek-account':
                态=建(文档,'span','accountStatus')
                点=建(文档,'span','credentialDot credentialDotConfigured')
                点.setAttribute('aria-hidden','true')
                态.appendChild(点)
                态.appendChild(文档.createTextNode(中文['accountSignedIn']))
                身份.appendChild(态)
            elif 凭据已配:
                点=建(文档,'span','credentialDot credentialDotConfigured')
                点.setAttribute('role','img')
                点.setAttribute('aria-label',中文['credentialConfigured'])
                点.title=中文['credentialConfigured']
                身份.appendChild(点)
            elif 凭据缺:
                点=建(文档,'span','credentialDot credentialDotMissing')
                点.setAttribute('role','img')
                点.setAttribute('aria-label',中文['credentialMissing'])
                点.title=中文['credentialMissing']
                身份.appendChild(点)
            头.appendChild(身份)
            动作=建(文档,'span','rowActions')
            if 行['entry']['provider']!='deepseek-account':
                编=建(文档,'button','secondaryButton')
                编.type='button'
                编.setAttribute('aria-label',提供方文案(中文['editProvider'],目标))
                编.disabled=开着 is not True and 状态.get('status')!='ready'
                def 点编(事件,开着=开着,目标=目标):
                    '一次只开一张卡'
                    if 开着 is not True and 属性['controller'].存储.getSnapshot().get('status')!='ready':
                        return
                    自身.已保存=None
                    自身.添加开=False
                    if 开着:
                        自身.编辑中=None
                        自身.行编辑器=None
                    else:
                        自身.编辑中=目标
                    自身.渲染()
                编.addEventListener('click',点编)
                编.textContent=中文['edit']
                动作.appendChild(编)
            if 行.get('removable') is True:
                删=建(文档,'button','dangerButton')
                删.type='button'
                删.setAttribute('aria-label',提供方文案(中文['removeProvider'],目标))
                删.disabled=状态.get('writable') is not True or 状态.get('status')!='ready'
                def 点删(事件,目标=目标):
                    '打开删除确认'
                    if 属性['controller'].存储.getSnapshot().get('status')!='ready':
                        return
                    自身.已保存=None
                    自身.删除失败=None
                    自身.删除目标=目标
                    自身.渲染()
                删.addEventListener('click',点删)
                删.textContent=中文['remove']
                动作.appendChild(删)
            头.appendChild(动作)
            项.appendChild(头)
            if 行['entry'].get('error') is not None:
                错=建(文档,'p','error')
                错.setAttribute('role','alert')
                错.textContent=str(行['entry']['error'])
                项.appendChild(错)
            槽=属性.get('renderSlot')
            if 槽 is not None:
                挂上(项,槽(
                    'settings.models.provider-card',
                    {'provider':行['entry'],'configured':行.get('configured'),'keyConfigured':密钥已配(行)},
                    {'entryKey':行['entry']['settingsNs']},
                ))
            if 开着:
                挂上(项,自身.取编辑器('行',{
                    'window':窗口,
                    'provider':目标['provider'],
                    'displayName':目标['displayName'],
                    'settingsPath':目标['settingsPath'],
                    'namespace':命名空间,
                    'schema':属性['schema'],
                    'operations':属性['operations'],
                    'readOnly':状态.get('writable') is not True,
                    'credential':行.get('credential'),
                    'credentialChecks':行.get('credentialChecks'),
                    'defaultBaseURL':目标.get('defaultBaseURL'),
                    'baseURLEnv':目标.get('baseURLEnv'),
                    'nativeAuth':目标.get('nativeAuth'),
                    'declared':True if 目标.get('declared') is True else None,
                    'onClose':自身.关编辑(目标),
                }))
            列表.appendChild(项)
        自身.根.appendChild(列表)
        加区=建(文档,'div','addBlock')
        if 自身.添加开:
            卡=建(文档,'div','addCard')
            式=建(文档,'div','addModes')
            if 两种:
                def 换式(下一):
                    '记住来过的方式，草稿都留着'
                    自身.添加方式=下一
                    自身.已访问.add(下一)
                    自身.渲染()
                选项=[
                    {'value':'catalog','label':中文['addCatalog'],'disabled':目录可加 is not True},
                    {'value':'custom','label':中文['addCustom'],'disabled':自定义可加 is not True},
                ]
                if 目录可加 is not True:
                    选项[0]['title']=中文['addCatalogExhausted']
                if 自定义可加 is not True:
                    选项[1]['title']=中文['addCustomUnavailable']
                挂上(式,分段控制({
                    'window':窗口,
                    'id':自身.添加编号,
                    'label':中文['addMode'],
                    'value':方式,
                    'disabled':锁,
                    'options':选项,
                    'onChange':换式,
                }))
            else:
                头=建(文档,'div','editorHeader')
                题=建(文档,'span','editorTitle')
                题.textContent=中文['addCatalog'] if 方式=='catalog' else 中文['addCustom']
                头.appendChild(题)
                式.appendChild(头)
            注=建(文档,'p','advancedHint')
            注.textContent=中文['addCatalogHint'] if 方式=='catalog' else 中文['addCustomHint']
            式.appendChild(注)
            卡.appendChild(式)
            目录挂=方式=='catalog' or 'catalog' in 自身.已访问
            if 目录挂 and 草稿 is not None:
                面=建(文档,'div','addPanel')
                面.id=自身.添加编号+'-catalog-panel'
                if 两种:
                    面.setAttribute('role','tabpanel')
                    面.setAttribute('aria-labelledby',自身.添加编号+'-catalog')
                if 方式!='catalog':
                    面.setAttribute('hidden','')
                字段=建(文档,'div','field')
                标=建(文档,'span','fieldLabel')
                标.textContent=中文['provider']
                字段.appendChild(标)
                选=建(文档,'select','input selectInput')
                选.value=草稿['target']['provider']
                选.setAttribute('aria-label',中文['provider'])
                选.disabled=自身.目录忙
                for 候选 in 可添加:
                    项=文档.createElement('option')
                    项.value=候选['row']['entry']['provider']
                    项.textContent=候选['row']['entry']['displayName']
                    选.appendChild(项)
                def 改选(事件):
                    '换一个还没配置的目录提供方'
                    选中=None
                    for 候选 in 可添加:
                        if 候选['row']['entry']['provider']==事件.target.value:
                            选中=候选
                            break
                    if 选中 is None:
                        return
                    自身.编辑中=目标自(选中['row'])
                    自身.目录编辑器=None
                    自身.渲染()
                选.addEventListener('change',改选)
                字段.appendChild(选)
                面.appendChild(字段)
                编辑属性={
                    'window':窗口,
                    'provider':草稿['target']['provider'],
                    'displayName':草稿['target']['displayName'],
                    'hideTitle':True,
                    'namespace':草稿['namespace'],
                    'schema':属性['schema'],
                    'settingsPath':草稿['target']['settingsPath'],
                    'operations':属性['operations'],
                    'readOnly':状态.get('writable') is not True,
                    'defaultBaseURL':草稿['target'].get('defaultBaseURL'),
                    'baseURLEnv':草稿['target'].get('baseURLEnv'),
                    'nativeAuth':草稿['target'].get('nativeAuth'),
                    'onClose':自身.关编辑(草稿['target']),
                    'onBusyChange':自身.目录忙变,
                }
                if 添加行 is not None and 添加行.get('credentialChecks') is not None:
                    编辑属性['credentialChecks']=添加行['credentialChecks']
                挂上(面,自身.取编辑器('目录',编辑属性))
                if 添加行 is not None and 属性.get('renderSlot') is not None:
                    挂上(面,属性['renderSlot'](
                        'settings.models.provider-card',
                        {'provider':添加行['entry'],'configured':添加行.get('configured'),'keyConfigured':密钥已配(添加行)},
                        {'entryKey':添加行['entry']['settingsNs']},
                    ))
                卡.appendChild(面)
            自定义挂=方式=='custom' or 'custom' in 自身.已访问
            if 自定义挂 and 派 is not None:
                面=建(文档,'div','addPanel')
                面.id=自身.添加编号+'-custom-panel'
                if 两种:
                    面.setAttribute('role','tabpanel')
                    面.setAttribute('aria-labelledby',自身.添加编号+'-custom')
                if 方式!='custom':
                    面.setAttribute('hidden','')
                已占=[]
                for 行 in 状态['rows']:
                    已占.append(行['entry']['provider'])
                卡属性={
                    'window':窗口,
                    'taken':已占,
                    'protocols':协议,
                    'reasoningLevels':推理,
                    'revision':派.get('revision'),
                    'operations':属性['operations'],
                    'readOnly':状态.get('writable') is not True,
                    'onClose':自身.关自定义,
                    'onBusyChange':自身.自定义忙变,
                }
                if 自身.自定义实例 is None:
                    自身.自定义实例=自定义提供方卡片(卡属性)
                else:
                    自身.自定义实例.更新(卡属性)
                    自身.自定义实例.渲染()
                挂上(面,自身.自定义实例)
                卡.appendChild(面)
            加区.appendChild(卡)
        elif 目录提供 or 自定义提供:
            行=建(文档,'div','addActions')
            钮=建(文档,'button','addButton')
            钮.type='button'
            钮.disabled=状态.get('writable') is not True or 状态.get('status')!='ready' or (目录可加 is not True and 自定义可加 is not True)
            挂上(钮,图标('plus-16',{'window':窗口,'size':14}))
            钮.appendChild(文档.createTextNode(中文['add']))
            def 点加(事件):
                '打开添加卡，目录还有空位就先显示目录'
                if 属性['controller'].存储.getSnapshot().get('status')!='ready':
                    return
                最初='catalog' if 目录可加 else 'custom'
                自身.已保存=None
                if len(可添加)>0:
                    自身.编辑中=目标自(可添加[0]['row'])
                else:
                    自身.编辑中=None
                自身.添加方式=最初
                自身.已访问=set([最初])
                自身.添加开=True
                自身.渲染()
            钮.addEventListener('click',点加)
            行.appendChild(钮)
            加区.appendChild(行)
        自身.根.appendChild(加区)
        if 属性.get('renderSlot') is not None:
            挂上(自身.根,属性['renderSlot']('settings.models.footer',{}))
        自身.根.appendChild(自身.删除框(窗口,文档))
        自身.订上()
        还原焦点(文档,焦点)

    def 取编辑器(自身,种类,属性):
        '同一种卡重画时留着草稿。提供方换了就新建'
        if 种类=='目录':
            持有=自身.目录编辑器
        elif 种类=='行':
            持有=自身.行编辑器
        else:
            持有=自身.装卡.get(种类)
        if 持有 is not None and 持有.属性.get('provider')==属性.get('provider'):
            持有.更新(属性)
            持有.渲染()
            return 持有
        新建=提供方编辑器(属性)
        if 种类=='目录':
            自身.目录编辑器=新建
        elif 种类=='行':
            自身.行编辑器=新建
        else:
            自身.装卡[种类]=新建
        return 新建

    def 关添加(自身):
        '关掉添加卡，并丢掉它的编辑器'
        自身.编辑中=None
        自身.添加开=False
        自身.目录忙=False
        自身.自定义忙=False
        自身.目录编辑器=None
        自身.自定义实例=None

    def 关编辑(自身,目标):
        '行编辑或目录添加关掉。有变更就等刷新后再报已保存'
        def 关(已变,目标=目标):
            '先收卡，再按是否写过决定要不要公告'
            自身.关添加()
            自身.行编辑器=None
            if 已变:
                自身.属性['controller'].加载()
                自身.已保存=目标
            自身.渲染()
        return 关

    def 关装(自身,目标):
        '装卡关掉后这一会话改回普通行'
        def 关(已变,目标=目标):
            '记下已关，不碰旁边还开着的草稿'
            自身.已关装卡.add(目标['provider'])
            键='装-'+目标['provider']
            if 键 in 自身.装卡:
                del 自身.装卡[键]
            if 已变:
                自身.属性['controller'].加载()
                自身.已保存=目标
            自身.渲染()
        return 关

    def 关自定义(自身,已变):
        '自定义卡关掉。创建成功就重拉目录'
        自身.关添加()
        if 已变:
            自身.属性['controller'].加载()
        自身.渲染()

    def 目录忙变(自身,忙):
        '目录卡在写或在问端点。没变就不再画，避免重入'
        新=忙 is True
        if 自身.目录忙==新:
            return
        自身.目录忙=新
        自身.渲染()

    def 自定义忙变(自身,忙):
        '自定义卡在写或在问端点。没变就不再画，避免重入'
        新=忙 is True
        if 自身.自定义忙==新:
            return
        自身.自定义忙=新
        自身.渲染()

    def 删除框(自身,窗口,文档):
        '删除确认。进行中不能关掉'
        目标=自身.删除目标
        def 关掉():
            '删除在飞时不关'
            if 自身.删除中:
                return
            自身.删除目标=None
            自身.删除失败=None
            自身.渲染()
        def 确认():
            '先卸托管凭据，再 unset 档案'
            if 自身.删除目标 is None or 自身.删除中:
                return
            自身.删除中=True
            自身.删除失败=None
            自身.渲染()
            操作=自身.属性['operations']
            失败=None
            if 自身.删除目标.get('credentialRef') is not None:
                失败=操作['卸凭据'](自身.删除目标['credentialRef'])
            if 失败 is None:
                写出=操作['写设置'](
                    自身.删除目标['settingsNs'],
                    [{'op':'unset','path':list(自身.删除目标['settingsPath'])}],
                    None,
                )
                if 写出['kind']!='written':
                    失败=写出['message']
                else:
                    自身.属性['controller'].加载()
            自身.删除中=False
            if 失败 is not None:
                自身.删除失败=失败
            else:
                自身.删除目标=None
            自身.渲染()
        说明=''
        标题=''
        if 目标 is not None:
            标题=提供方文案(中文['deleteTitle'],目标)
            if 目标.get('credentialRef') is None:
                说明=提供方文案(中文['deleteDescription'],目标)
            else:
                说明=提供方文案(中文['deleteDescriptionWithCredential'],目标)
        体=None
        if 自身.删除失败 is not None:
            体=建(文档,'p','error')
            体.textContent=自身.删除失败
        取消=按钮({
            'window':窗口,
            'variant':'outline',
            'disabled':自身.删除中,
            'onClick':关掉,
            'children':中文['cancel'],
        }).渲染()
        取消.setAttribute('data-modal-autofocus','')
        确认文=''
        if 目标 is not None:
            确认文=提供方文案(中文['deleting'] if 自身.删除中 else 中文['deleteConfirm'],目标)
        确定=按钮({
            'window':窗口,
            'variant':'outline',
            'className':'deleteConfirm',
            'disabled':自身.删除中,
            'onClick':确认,
            'children':确认文,
        }).渲染()
        确定.setAttribute('data-dsh-css',样式模块)
        脚=文档.createElement('div')
        脚.appendChild(取消)
        脚.appendChild(确定)
        罩=模态({
            'window':窗口,
            'open':目标 is not None,
            'onClose':关掉,
            'title':标题,
            'closeLabel':中文['close'],
            'description':说明,
            'className':'deleteDialog',
            'children':体,
            'footer':脚,
        }).渲染()
        if 罩 is not None:
            卡=罩.querySelector('.deleteDialog')
            if 卡 is not None:
                卡.setAttribute('data-dsh-css',样式模块)
            return 罩
        return 文档.createElement('span')

    def 订上(自身):
        '快照变了就重画。节点不在页面上就退订'
        if 自身.已订:
            return
        钩=自身.属性.get('useSnapshot')
        订=getattr(钩,'_subscribe',None) if 钩 is not None else None
        if callable(订) is not True:
            return
        def 变更():
            '绘制中只记一笔。根已经离开页面就退订'
            if 自身.绘制中:
                自身.待重画=True
                return
            if 自身.根 is None or 自身.根.parentNode is None:
                if 自身.退订 is not None:
                    退=自身.退订
                    自身.退订=None
                    自身.已订=False
                    退()
                return
            自身.渲染()
        自身.退订=订(变更)
        自身.已订=True
