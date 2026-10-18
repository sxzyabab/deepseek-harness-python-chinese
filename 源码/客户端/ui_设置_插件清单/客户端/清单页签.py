import os
from urllib.parse import quote as 编码
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 常规描边,描边图标,图标下箭头描边常规
from ...ui_基础界面组件.状态点 import 状态点
from ...ui_基础界面组件.标签 import 标签
from ...ui_基础界面组件.菜单 import 菜单
from .文案 import 中文

__all__=['插件清单页签']

阶段文案键={
    'pending':'pending',
    'loading':'loadingPhase',
    'active':'active',
    'failed':'failed',
    'unloading':'unloading',
}
骨架格=(0,1,2,3)
阶段点态={
    'pending':'idle',
    'loading':'ongoing',
    'unloading':'ongoing',
}
标签调={
    'disabled':'neutral',
    'conditional':'warning',
    'preset':'info',
    'failed':'danger',
}
样式模块='pluginInventory'

def 阶段文案(阶段):
    '没有阶段时是未运行，其余用中文表原文'
    if 阶段 is None:
        return 中文['unobserved']
    return 中文[阶段文案键[阶段]]

def 入口副标题(入口标识):
    '去掉组合标记 include:，只去开头一次'
    if 入口标识.startswith('include:'):
        return 入口标识[len('include:'):]
    return 入口标识

def 标识补充标题(入口标识,标题):
    '有入口，且去掉 include: 后仍和标题不同'
    if 入口标识 is None:
        return False
    return 入口副标题(入口标识)!=标题

def 卡片无障碍名(标题,入口标识,状态文):
    '标题、完整入口、启用状态。入口没有额外信息时不念入口'
    if 标识补充标题(入口标识,标题) is True:
        return 标题+', '+入口标识+', '+状态文
    return 标题+', '+状态文

def 插件文案(行,解析文案):
    '对象标题交给解析。字面标题和缺标题都缩短模块名'
    元=行.get('meta')
    标题=None
    if isinstance(元,dict) and 'title' in 元:
        标题=元['title']
    if isinstance(标题,dict):
        显示=解析文案(标题)
    else:
        名=行['moduleName'] if 标题 is None else 标题
        if 名.startswith('@'):
            斜杠=名.find('/')
            if 斜杠>=0:
                名=名[斜杠+1:]
        if 名.startswith('cordis:'):
            名=名[len('cordis:'):]
        if 名.startswith('cordis-plugin-'):
            名=名[len('cordis-plugin-'):]
        if 名.startswith('dsh-host-'):
            名=名[len('dsh-host-'):]
        elif 名.startswith('dsh-client-'):
            名=名[len('dsh-client-'):]
        elif 名.startswith('dsh-'):
            名=名[len('dsh-'):]
        显示=名
    描述=None
    if isinstance(元,dict) and 'description' in 元 and 元['description'] is not None:
        原文=解析文案(元['description'])
        if 原文:
            描述=原文
    return {'title':显示,'description':描述}

def 匹配(行,查询词,解析文案):
    '空查询全中。模块名、入口、标题、说明有一处包含即中'
    if len(查询词)==0:
        return True
    文案=插件文案(行,解析文案)
    for 值 in (行['moduleName'],行['entryId'],文案['title'],文案['description']):
        if isinstance(值,str) and 查询词 in 值.lower():
            return True
    return False

def 预设选项文案(预设,预设名):
    '加载失败和默认预设带中文后缀，其余用显示名'
    名=预设名(预设)
    if 'broken' in 预设 and 预设['broken'] is not None:
        return 中文['presetOptionBroken'].replace('{name}',名)
    if 预设['isDefault'] is True:
        return 中文['presetOptionDefault'].replace('{name}',名)
    return 名

def 有阶段点(阶段):
    'pending、loading、unloading 才自带状态点'
    return 阶段=='pending' or 阶段=='loading' or 阶段=='unloading'

class 阶段点:
    '进行中的根 Fiber 阶段。点本身不带名字，名字在外层'
    def __init__(自身,属性):
        '记下阶段'
        自身.属性=属性
        自身.根=None

    def 渲染(自身):
        '画出带中文名的阶段点'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        文=阶段文案(属性['phase'])
        盒=模块节点(文档,'span',样式模块,'phaseDot')
        盒.setAttribute('role','img')
        盒.setAttribute('aria-label',文)
        盒.setAttribute('title',文)
        盒.appendChild(状态点({'window':窗口,'state':阶段点态[属性['phase']]}).渲染())
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(盒)
        自身.根=盒
        return 自身.根

class 状态标签:
    '偏离默认启用才画胶囊。已启用不画'
    def __init__(自身,属性):
        '记下种类和中文'
        自身.属性=属性
        自身.根=None

    def 渲染(自身):
        '已启用返回空，其余交给共享标签'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        if 属性['kind']=='enabled':
            自身.根=None
            return None
        标=标签({
            'window':属性['window'],
            'tone':标签调[属性['kind']],
            'children':属性['label'],
        })
        自身.根=标.渲染()
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根

class 卡片事实:
    '展开后的装载身份，以及带标签的事实'
    def __init__(自身,属性):
        '记下模块、入口和事实行'
        自身.属性=属性
        自身.根=None

    def 渲染(自身,父):
        '入口标识在前，事实表在后，都挂进父节点'
        属性=自身.属性
        文档=属性['window'].document
        入口=属性['entryId']
        if 入口 is not None:
            码=模块节点(文档,'code',样式模块,'entryValue')
            码.setAttribute('data-loader-entry','')
            码.textContent=入口
            父.appendChild(码)
        表=模块节点(文档,'dl',样式模块,'details')

        def 加行(标签文,值):
            '一行标签和值。代码值用 code'
            格=文档.createElement('div')
            名=文档.createElement('dt')
            名.textContent=标签文
            值节=文档.createElement('dd')
            if isinstance(值,tuple) and 值[0]=='code':
                条件=文档.createElement('code')
                条件.textContent=值[1]
                值节.appendChild(条件)
            else:
                值节.textContent='' if 值 is None else 值
            格.appendChild(名)
            格.appendChild(值节)
            表.appendChild(格)

        加行(属性['moduleLabel'],属性['moduleName'])
        for 标签文,值 in 属性['facts']:
            加行(标签文,值)
        父.appendChild(表)
        自身.根=表
        return 表

class 插件卡片:
    '一张可展开的插件卡。尾部状态由调用方传入'
    def __init__(自身,属性):
        '记下这一张卡的数据'
        自身.属性=属性
        自身.根=None

    def 渲染(自身):
        '标题行、说明、入口芯片，展开后是事实'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        入口=属性['entryId']
        开=属性['expanded']==属性['rowKey']
        安全键=编码(属性['rowKey'],safe="-_.!~*'()")
        详情标识='plugin-details-'+安全键
        说明标识='plugin-desc-'+安全键
        卡=模块节点(文档,'li',样式模块,'card')
        if 入口 is not None:
            卡.setAttribute('data-plugin-entry',入口)
        卡.setAttribute('data-plugin-module',属性['moduleName'])
        if 属性['failed'] is True:
            卡.setAttribute('data-failed','true')
        if 开 is True:
            卡.setAttribute('data-open','true')

        def 点卡(事件):
            '展开或收起这一张'
            属性['onToggle'](属性['rowKey'])

        钮=模块节点(文档,'button',样式模块,'cardContent')
        钮.type='button'
        钮.setAttribute('aria-expanded','true' if 开 is True else 'false')
        钮.setAttribute('aria-controls',详情标识)
        钮.setAttribute('aria-label',属性['ariaLabel'])
        描述=属性['description']
        if 描述 is not None:
            钮.setAttribute('aria-describedby',说明标识)
        钮.addEventListener('click',点卡)
        行=模块节点(文档,'span',样式模块,'cardMainRow')
        题=模块节点(文档,'strong',样式模块,'cardTitle')
        题.setAttribute('title',属性['moduleName'])
        题.textContent=属性['title']
        行.appendChild(题)
        尾盒=模块节点(文档,'span',样式模块,'cardTrailing')
        for 尾 in 属性['trailing']:
            if 尾 is not None:
                尾盒.appendChild(尾)
        箭头=图标下箭头描边常规({'window':窗口,'className':'chevron','size':12})
        尾盒.appendChild(标样式模块(箭头,样式模块))
        行.appendChild(尾盒)
        钮.appendChild(行)
        if 描述 is not None:
            说明=模块节点(文档,'span',样式模块,'cardDescription')
            说明.id=说明标识
            说明.textContent=描述
            钮.appendChild(说明)
        if 标识补充标题(入口,属性['title']) is True:
            元行=模块节点(文档,'span',样式模块,'cardMeta')
            短=模块节点(文档,'code',样式模块,'cardIdentity')
            短.setAttribute('title',入口)
            短.textContent=入口副标题(入口)
            元行.appendChild(短)
            钮.appendChild(元行)
        卡.appendChild(钮)
        元错=属性['metadataError']
        if 元错 is not None:
            错=模块节点(文档,'p',样式模块,'brokenNote')
            错.setAttribute('role','status')
            错.setAttribute('data-package-meta-error','')
            错.textContent=元错
            卡.appendChild(错)
        if 开 is True:
            详=模块节点(文档,'div',样式模块,'cardDetails')
            详.id=详情标识
            卡片事实({
                'window':窗口,
                'moduleName':属性['moduleName'],
                'moduleLabel':属性['moduleLabel'],
                'entryId':入口,
                'facts':属性['facts'],
            }).渲染(详)
            卡.appendChild(详)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(卡)
        自身.根=卡
        return 自身.根

class 插件清单页签:
    '只读插件清单。会话预设在前，全局平面在后'
    def __init__(自身,属性):
        '记下 props。有窗口就先画读取中，再拉清单'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.请求=0
        自身.查询=''
        自身.展开=None
        自身.所选预设=None
        自身.切换器开=False
        自身.预设展开=None
        自身.全局展开=None
        自身.状态={'status':'loading'}
        自身.存活=True
        自身.世代=0
        自身.根=None
        自身.菜单=None
        自身.已订=False
        自身.退订=None
        自身.要拉=False
        自身.查询词=''
        自身.区号='插件分区'+str(id(自身))
        if 'window' in 自身.属性:
            自身.拉取()

    def 更新(自身,属性):
        '换成新的 props。list 换了就重新拉取'
        旧=None
        if isinstance(自身.属性,dict):
            旧=自身.属性.get('list')
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 自身.属性.get('list') is not 旧:
            自身.状态={'status':'loading'}
            自身.要拉=True

    def 拆除(自身):
        '这一代的清单结果作废，并退订本页同步'
        自身.存活=False
        自身.世代=自身.世代+1
        退=自身.退订
        自身.退订=None
        自身.已订=False
        if callable(退):
            退()
        if 自身.菜单 is not None:
            自身.菜单.属性['open']=False
            自身.菜单.渲染()
            自身.菜单=None

    def 拉取(自身):
        '调用 list。这一代被拆掉就不再改状态'
        自身.世代=自身.世代+1
        这一代=自身.世代
        if 'window' in 自身.属性:
            自身.画出()
        try:
            快照=自身.属性['list']()
        except Exception:
            if 自身.世代!=这一代 or 自身.存活 is not True:
                return
            自身.状态={'status':'error'}
            if 'window' in 自身.属性:
                自身.画出()
            return
        if 自身.世代!=这一代 or 自身.存活 is not True:
            return
        自身.状态={'status':'ready','snapshot':快照}
        if 'window' in 自身.属性:
            自身.画出()

    def 重试(自身):
        '先回到读取中，再拉一次清单'
        自身.状态={'status':'loading'}
        自身.请求=自身.请求+1
        自身.拉取()

    def 切换行(自身,行键):
        '同一张卡再点则收起'
        if 自身.展开==行键:
            自身.展开=None
        else:
            自身.展开=行键
        自身.渲染()

    def 条目匹配(自身,条目):
        '全局条目是否命中当前查询'
        return 匹配(条目,自身.查询词,自身.属性['resolveText'])

    def 行匹配(自身,行):
        '预设行是否命中当前查询'
        return 匹配(行,自身.查询词,自身.属性['resolveText'])

    def 画全局行(自身,条目,提供方):
        '一张全局卡。失败优先。未启用且有预设提供时标成预设中启用'
        窗口=自身.属性['window']
        入口=条目['entryId']
        if 入口 is None:
            键='global:null'
        else:
            键='global:'+str(入口)
        文案=插件文案(条目,自身.属性['resolveText'])
        阶段=条目['fiberPhase']
        失败=阶段=='failed'
        启用=条目['enabled'] is True
        if 失败 is True:
            状态文=中文['failedTag']
            种类='failed'
        elif 提供方 is not None:
            状态文=中文['presetEnabledTag']
            种类='preset'
        elif 启用 is True:
            状态文=中文['enabledTag']
            种类='enabled'
        else:
            状态文=中文['disabledTag']
            种类='disabled'
        尾=[]
        if 启用 is True and 有阶段点(阶段) is True:
            尾.append(阶段点({'window':窗口,'phase':阶段}).渲染())
        标=状态标签({'window':窗口,'kind':种类,'label':状态文}).渲染()
        if 标 is not None:
            尾.append(标)
        if 提供方 is not None:
            名字=[]
            for 预设 in 提供方:
                名字.append(自身.属性['presetName'](预设))
            事实=[
                (中文['configuration'],中文['presetProvidedDetail']),
                (中文['enabledIn'],' · '.join(名字)),
            ]
        else:
            if 启用 is True:
                配置文=中文['enabledTag']
            else:
                配置文=中文['disabledTag']
            事实=[(中文['configuration'],配置文)]
            if 启用 is True:
                事实.append((中文['runtime'],阶段文案(阶段)))
        元=条目.get('meta')
        元错=None
        if isinstance(元,dict) and 'error' in 元 and 元['error'] is not None:
            元错=中文['metadataError'].replace('{error}',str(元['error']))
        卡=插件卡片({
            'window':窗口,
            'rowKey':键,
            'moduleName':条目['moduleName'],
            'title':文案['title'],
            'description':文案['description'],
            'metadataError':元错,
            'entryId':入口,
            'trailing':尾,
            'ariaLabel':卡片无障碍名(文案['title'],入口,状态文),
            'failed':失败,
            'expanded':自身.展开,
            'onToggle':自身.切换行,
            'moduleLabel':中文['moduleLabel'],
            'facts':事实,
        })
        return 卡.渲染()

    def 渲染(自身):
        '有待拉取就先拉，否则按当前状态重画'
        if 'window' not in 自身.属性:
            return None
        if 自身.要拉 is True:
            自身.要拉=False
            自身.拉取()
            return 自身.根
        return 自身.画出()

    def 画出(自身):
        '按当前状态画出整页'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '插件清单页签样式',
            os.path.join(os.path.dirname(__file__),'清单页签.module.css'),
            样式模块,
        )
        自身.查询词=自身.查询.strip().lower()

        def 全量(快照):
            '整份本页同步快照'
            return 快照

        同步=属性['useClientSync'](全量)
        清单=自身.状态['snapshot'] if 自身.状态['status']=='ready' else None
        预设表=[]
        条目表=[]
        选中=None
        搜索中=len(自身.查询词)>0
        启用表={}
        过滤失败=[]
        过滤普通=[]
        全局数=0
        选中行=[]
        其它预设=[]
        其它数=0
        预设开=False
        全局开=False
        全无=False
        if 清单 is not None:
            原始预设=清单.get('agentPresets')
            预设表=原始预设 if 原始预设 is not None else []
            原始条目=清单.get('entries')
            条目表=原始条目 if 原始条目 is not None else []
            for 预设 in 预设表:
                if 预设['id']==自身.所选预设:
                    选中=预设
                    break
            if 选中 is None:
                for 预设 in 预设表:
                    if 预设['isDefault'] is True:
                        选中=预设
                        break
                if 选中 is None and len(预设表)>0:
                    选中=预设表[0]
            for 预设 in 预设表:
                for 行 in 预设['rows']:
                    if 行['enabled'] is not True:
                        continue
                    模块=行['moduleName']
                    已有=启用表.get(模块)
                    if 已有 is None:
                        启用表[模块]=[预设]
                    else:
                        重复=False
                        for 项 in 已有:
                            if 项 is 预设:
                                重复=True
                                break
                        if 重复 is not True:
                            已有.append(预设)
            失败条目=[]
            普通条目=[]
            for 条目 in 条目表:
                if 条目['fiberPhase']=='failed':
                    失败条目.append(条目)
                else:
                    普通条目.append(条目)
            for 条目 in 失败条目:
                if 自身.条目匹配(条目) is True:
                    过滤失败.append(条目)
            for 条目 in 普通条目:
                if 自身.条目匹配(条目) is True:
                    过滤普通.append(条目)
            全局数=len(过滤失败)+len(过滤普通)
            if 选中 is not None:
                for 行 in 选中['rows']:
                    if 自身.行匹配(行) is True:
                        选中行.append(行)
            if 搜索中 is True:
                for 预设 in 预设表:
                    if 预设 is 选中:
                        continue
                    有=False
                    for 行 in 预设['rows']:
                        if 自身.行匹配(行) is True:
                            有=True
                            break
                    if 有 is True:
                        其它预设.append(预设)
            for 预设 in 其它预设:
                for 行 in 预设['rows']:
                    if 自身.行匹配(行) is True:
                        其它数=其它数+1
            预设开=搜索中 is True or (自身.预设展开 if 自身.预设展开 is not None else True)
            全局开=搜索中 is True or (自身.全局展开 if 自身.全局展开 is not None else False)
            全无=搜索中 is True and 全局数==0 and len(选中行)==0 and len(其它预设)==0
        起点=None
        终点=None
        if 自身.根 is not None:
            旧框=自身.根.querySelector('input[type="search"]')
            if 旧框 is not None and 文档.activeElement is 旧框:
                起点=旧框.selectionStart
                终点=旧框.selectionEnd
        if 自身.菜单 is not None:
            自身.菜单.属性['open']=False
            自身.菜单.渲染()
            自身.菜单=None
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        if 父 is None and 'parent' in 属性:
            父=属性['parent']
        根=模块节点(文档,'div',样式模块,'section')
        if 自身.状态['status']=='loading':
            根.setAttribute('aria-busy','true')
        else:
            根.setAttribute('aria-busy','false')
        自身.根=根
        if 同步['syncing'] is True:
            同步行=模块节点(文档,'p',样式模块,'status statusWithDot')
            同步行.setAttribute('role','status')
            同步行.appendChild(状态点({'window':窗口,'state':'ongoing'}).渲染())
            同步行.appendChild(文档.createTextNode(中文['clientSyncing']))
            根.appendChild(同步行)
        失败列=同步['failures']
        if len(失败列)>0:
            败=模块节点(文档,'div',样式模块,'failure')
            败.setAttribute('data-client-sync-failure','')
            败题=模块节点(文档,'p',样式模块,'statusWithDot')
            败题.setAttribute('role','alert')
            败题.appendChild(状态点({'window':窗口,'state':'error'}).渲染())
            败题.appendChild(文档.createTextNode(中文['clientSyncFailed']))
            败.appendChild(败题)
            列=文档.createElement('ul')
            for 失败 in 失败列:
                项=文档.createElement('li')
                项.textContent=str(失败['id'])+': '+str(失败['message'])
                列.appendChild(项)
            败.appendChild(列)

            def 点本页(事件):
                '重试本页同步，不改宿主启用'
                属性['retryClient']()

            本页钮=文档.createElement('button')
            本页钮.type='button'
            本页钮.disabled=同步['syncing'] is True
            本页钮.textContent=中文['clientSyncRetry']
            本页钮.addEventListener('click',点本页)
            败.appendChild(本页钮)
            根.appendChild(败)
        if 自身.状态['status']=='loading':
            格=模块节点(文档,'div',样式模块,'cards')
            格.setAttribute('role','status')
            隐=模块节点(文档,'span',样式模块,'visuallyHidden')
            隐.textContent=中文['loading']
            格.appendChild(隐)
            份数=0
            while 份数<len(骨架格):
                份数=份数+1
                骨=模块节点(文档,'div',样式模块,'skeletonCard')
                骨.setAttribute('aria-hidden','true')
                条=模块节点(文档,'span',样式模块,'skeletonBar')
                骨.appendChild(条)
                条二=模块节点(文档,'span',样式模块,'skeletonBar')
                骨.appendChild(条二)
                格.appendChild(骨)
            根.appendChild(格)
        if 自身.状态['status']=='error':
            错块=模块节点(文档,'div',样式模块,'failure')
            错题=模块节点(文档,'p',样式模块,'statusWithDot')
            错题.setAttribute('role','alert')
            错题.appendChild(状态点({'window':窗口,'state':'error'}).渲染())
            错题.appendChild(文档.createTextNode(中文['error']))
            错块.appendChild(错题)

            def 点重试(事件):
                '回到读取中再拉清单'
                自身.重试()

            重试钮=文档.createElement('button')
            重试钮.type='button'
            重试钮.textContent=中文['retry']
            重试钮.addEventListener('click',点重试)
            错块.appendChild(重试钮)
            根.appendChild(错块)
        if 清单 is not None:
            目录=模块节点(文档,'div',样式模块,'catalog')
            搜=模块节点(文档,'label',样式模块,'search')
            搜标=描边图标(
                {'window':窗口},
                '0 0 16 16',
                [
                    'M6.58727 11.8586C9.55061 11.8586 11.9529 9.45637 11.9529 6.49304C11.9529 3.5297 9.55061 1.12744 6.58727 1.12744C3.62394 1.12744 1.22168 3.5297 1.22168 6.49304C1.22168 9.45637 3.62394 11.8586 6.58727 11.8586Z',
                    'M10.2991 10.3933L14.7783 14.8725',
                ],
                16,
                常规描边,
            )
            搜.appendChild(搜标)
            隐搜=模块节点(文档,'span',样式模块,'visuallyHidden')
            隐搜.textContent=中文['search']
            搜.appendChild(隐搜)
            框=文档.createElement('input')
            框.type='search'
            框.value=自身.查询
            框.placeholder=中文['search']
            框.setAttribute('aria-label',中文['search'])

            def 改查询(事件):
                '按输入过滤两组卡片'
                自身.查询=事件.target.value
                自身.渲染()

            框.addEventListener('input',改查询)
            搜.appendChild(框)
            目录.appendChild(搜)
            if len(条目表)==0 and len(预设表)==0:
                空=模块节点(文档,'p',样式模块,'status')
                空.textContent=中文['empty']
                目录.appendChild(空)
            if 全无 is True:
                无=模块节点(文档,'p',样式模块,'status')
                无.textContent=中文['emptySearch']
                目录.appendChild(无)
            if 选中 is not None:
                def 点预设组(事件):
                    '按当前展开结果翻转。搜索期间实际仍展开'
                    自身.预设展开=not 预设开
                    自身.渲染()

                def 点切换(事件):
                    '打开或关上预设菜单'
                    自身.切换器开=自身.切换器开 is not True
                    自身.渲染()

                def 选定(标识):
                    '关掉菜单并切到这个预设'
                    自身.切换器开=False
                    自身.所选预设=标识
                    自身.渲染()

                def 关闭菜单():
                    '菜单要求关闭。已经关着就不再重画'
                    if 自身.切换器开 is not True:
                        return
                    自身.切换器开=False
                    自身.渲染()

                区=模块节点(文档,'section',样式模块,'group')
                区.setAttribute('data-plugin-scope','preset')
                区.setAttribute('data-preset-id',str(选中['id']))
                题行=模块节点(文档,'div',样式模块,'groupTitleRow')
                组钮=模块节点(文档,'button',样式模块,'groupToggle')
                组钮.type='button'
                组钮.setAttribute('aria-expanded','true' if 预设开 is True else 'false')
                组钮.setAttribute('aria-controls',自身.区号+'-preset')
                组钮.addEventListener('click',点预设组)
                组箭头=图标下箭头描边常规({'window':窗口,'className':'chevron','size':12})
                组钮.appendChild(标样式模块(组箭头,样式模块))
                组题=模块节点(文档,'span',样式模块,'groupTitle')
                组题.textContent=中文['presetTitle']
                组钮.appendChild(组题)
                题行.appendChild(组钮)
                右=模块节点(文档,'div',样式模块,'headerEnd')
                锚=模块节点(文档,'button',样式模块,'switcher')
                锚.type='button'
                锚.setAttribute('aria-haspopup','menu')
                锚.setAttribute('aria-expanded','true' if 自身.切换器开 is True else 'false')
                锚.setAttribute('aria-label',中文['switcherLabel'])
                锚.addEventListener('click',点切换)
                锚字=模块节点(文档,'span',样式模块,'switcherLabel')
                锚字.textContent=预设选项文案(选中,属性['presetName'])
                锚.appendChild(锚字)
                锚箭头=图标下箭头描边常规({'window':窗口,'className':'chevron'})
                锚.appendChild(标样式模块(锚箭头,样式模块))
                条目=[]
                for 预设 in 预设表:
                    条目.append({
                        'id':预设['id'],
                        'label':预设选项文案(预设,属性['presetName']),
                    })
                菜单件=菜单({
                    'window':窗口,
                    'open':自身.切换器开 is True,
                    'onClose':关闭菜单,
                    'items':条目,
                    'selectedId':选中['id'],
                    'onSelect':选定,
                    'align':'end',
                    'portal':True,
                    'anchor':锚,
                })
                右.appendChild(菜单件.渲染())
                自身.菜单=菜单件
                题行.appendChild(右)
                区.appendChild(题行)
                副=模块节点(文档,'p',样式模块,'groupSub')
                副.textContent=中文['presetSubtitle']
                区.appendChild(副)
                if 预设开 is True:
                    体=模块节点(文档,'div',样式模块,'groupBody')
                    体.id=自身.区号+'-preset'
                    if 'broken' in 选中 and 选中['broken'] is not None:
                        坏=模块节点(文档,'p',样式模块,'brokenNote')
                        坏.setAttribute('role','alert')
                        坏.textContent=选中['broken']
                        体.appendChild(坏)
                    if len(选中行)>0:
                        网格=模块节点(文档,'ul',样式模块,'cards')
                        for 下标,行 in enumerate(选中行):
                            行键='preset:'+str(选中['id'])+':'+str(下标)
                            行文=插件文案(行,属性['resolveText'])
                            阶段=行['fiberPhase']
                            失败=阶段=='failed'
                            if 失败 is True:
                                状态文=中文['failedTag']
                                种类='failed'
                            elif 行['enabled'] is True:
                                状态文=中文['enabledTag']
                                种类='enabled'
                            elif 行['enabled'] is False:
                                状态文=中文['disabledTag']
                                种类='disabled'
                            else:
                                状态文=中文['conditionalTag']
                                种类='conditional'
                            尾=[]
                            if 行['enabled'] is True and 有阶段点(阶段) is True:
                                尾.append(阶段点({'window':窗口,'phase':阶段}).渲染())
                            标=状态标签({'window':窗口,'kind':种类,'label':状态文}).渲染()
                            if 标 is not None:
                                尾.append(标)
                            事实=[
                                (中文['fromPreset'],属性['presetName'](选中)),
                                (中文['configuration'],状态文),
                            ]
                            if 阶段 is not None:
                                事实.append((中文['runtime'],阶段文案(阶段)))
                            if 'condition' in 行 and 行['condition'] is not None:
                                事实.append((中文['condition'],('code',行['condition'])))
                            元=行.get('meta')
                            元错=None
                            if isinstance(元,dict) and 'error' in 元 and 元['error'] is not None:
                                元错=中文['metadataError'].replace('{error}',str(元['error']))
                            网格.appendChild(插件卡片({
                                'window':窗口,
                                'rowKey':行键,
                                'moduleName':行['moduleName'],
                                'title':行文['title'],
                                'description':行文['description'],
                                'metadataError':元错,
                                'entryId':行['entryId'],
                                'trailing':尾,
                                'ariaLabel':卡片无障碍名(行文['title'],行['entryId'],状态文),
                                'failed':失败,
                                'expanded':自身.展开,
                                'onToggle':自身.切换行,
                                'moduleLabel':中文['moduleLabel'],
                                'facts':事实,
                            }).渲染())
                        体.appendChild(网格)
                    if 其它数>0:
                        提示=模块节点(文档,'p',样式模块,'hint')
                        提示.appendChild(文档.createTextNode(
                            中文['matchesInOtherPresets'].replace('{count}',str(其它数)),
                        ))
                        for 预设 in 其它预设:
                            def 点跳(事件,标识=预设['id']):
                                '切到这个预设'
                                自身.所选预设=标识
                                自身.渲染()

                            链=模块节点(文档,'button',样式模块,'jumpLink')
                            链.type='button'
                            链.textContent=属性['presetName'](预设)
                            链.addEventListener('click',点跳)
                            提示.appendChild(链)
                        体.appendChild(提示)
                    区.appendChild(体)
                目录.appendChild(区)
            if len(条目表)>0:
                def 点全局组(事件):
                    '按当前展开结果翻转。搜索期间实际仍展开'
                    自身.全局展开=not 全局开
                    自身.渲染()

                全区=模块节点(文档,'section',样式模块,'group')
                全区.setAttribute('data-plugin-scope','global')
                全题行=模块节点(文档,'div',样式模块,'groupTitleRow')
                全钮=模块节点(文档,'button',样式模块,'groupToggle')
                全钮.type='button'
                全钮.setAttribute('aria-expanded','true' if 全局开 is True else 'false')
                全钮.setAttribute('aria-controls',自身.区号+'-global')
                全钮.addEventListener('click',点全局组)
                全箭头=图标下箭头描边常规({'window':窗口,'className':'chevron','size':12})
                全钮.appendChild(标样式模块(全箭头,样式模块))
                全题=模块节点(文档,'span',样式模块,'groupTitle')
                全题.textContent=中文['globalTitle']
                全钮.appendChild(全题)
                全题行.appendChild(全钮)
                全区.appendChild(全题行)
                全副=模块节点(文档,'p',样式模块,'groupSub')
                全副.textContent=中文['globalSubtitle']
                全区.appendChild(全副)
                if 全局开 is True and 全局数>0:
                    全网格=模块节点(文档,'ul',样式模块,'cards')
                    全网格.id=自身.区号+'-global'
                    for 条目 in 过滤失败:
                        全网格.appendChild(自身.画全局行(条目,None))
                    for 条目 in 过滤普通:
                        提供=None
                        if 条目['enabled'] is not True:
                            提供=启用表.get(条目['moduleName'])
                        全网格.appendChild(自身.画全局行(条目,提供))
                    全区.appendChild(全网格)
                目录.appendChild(全区)
            根.appendChild(目录)
        if 父 is not None:
            父.appendChild(根)
        if 起点 is not None:
            新框=根.querySelector('input[type="search"]')
            if 新框 is not None:
                新框.focus()
                if 终点 is not None:
                    新框.setSelectionRange(起点,终点)
        if 自身.已订 is not True:
            钩=属性.get('useClientSync')
            订=getattr(钩,'_subscribe',None) if 钩 is not None else None
            if callable(订):
                自身.已订=True

                def 变更():
                    '本页同步变了就重画。根离开页面就退订'
                    if 自身.根 is None or 自身.根.parentNode is None:
                        退=自身.退订
                        自身.退订=None
                        自身.已订=False
                        if callable(退):
                            退()
                        return
                    自身.渲染()

                自身.退订=订(变更)
        return 根

    def __call__(自身,属性=None):
        '再画一次'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
