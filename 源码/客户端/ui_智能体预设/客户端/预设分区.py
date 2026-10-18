from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块,模块节点
from ...ui_基础界面组件.icons import 图标加号16,图标浏览16
from ...ui_基础界面组件.按钮 import 按钮
from ...ui_基础界面组件.标签 import 标签
from ...ui_基础界面组件.提示泡 import 提示泡
from ...ui_基础界面组件.模态 import 模态
from .文案 import 中文,取中文,是否内置预设,预设展示文本
from .设置存储 import 需要编码工具
from .预设指南 import 圈定阅读焦点,预设指南对话框

__all__=['卡片说明','预设分区']

样式模块='agent-preset-section'#样式隔离
指南表={#只有这些出厂预设有帮助
    'standard':{'name':'presetStandardName','intro':'guideStandardIntro','explanation':'guideStandardExplanation','usage':'guideStandardUsage'},
    'ptc':{'name':'presetPtcName','intro':'guidePtcIntro','explanation':'guidePtcExplanation','usage':'guidePtcUsage'},
    'minimal':{'name':'presetMinimalName','intro':'guideMinimalIntro','explanation':'guideMinimalExplanation','usage':'guideMinimalUsage'},
    'cordis':{'name':'presetCordisName','intro':'guideCordisIntro','explanation':'guideCordisExplanation','usage':'guideCordisUsage'},
}#结束

class 卡片说明:
    '说明超过四行才出提示。气泡不超过卡片附近的宽度'
    def __init__(自身,属性):
        '记下说明文字'
        自身.属性=属性#props
        自身.根=None#提示的锚
        自身.截断=False#是否被夹断
        自身.观察=None#宽度变化

    def 渲染(自身):
        '空 title 挡住按钮自己的原生提示'
        属性=自身.属性#props
        窗口=属性['window']#窗口
        文档=窗口.document#文档
        if 自身.观察 is not None:#拆旧观察
            自身.观察.disconnect()#停
            自身.观察=None#空
        旧=自身.根#上一份
        父=旧.parentNode if 旧 is not None else None#还在卡片里
        if 旧 is not None:#拆旧
            旧.remove()#拿掉
        说明=模块节点(文档,'span',样式模块,'cardDesc')#说明
        说明.title=''#不要原生提示
        说明.textContent=属性['text']#全文仍在
        泡=提示泡({#夹断了才显示
            'window':窗口,
            'label':属性['text'],
            'side':'bottom',
            'delayMs':400,
            'disabled':自身.截断 is not True,
            'maxWidth':360,
            'children':说明,
        })
        自身.根=泡.渲染()#锚就是说明
        if 父 is not None and 自身.根 is not None and 自身.根.parentNode is None:#量完后挂回卡片
            父.appendChild(自身.根)#挂回

        def 测量():
            '内容高度超过盒子才算被夹断'
            截断=说明.scrollHeight>说明.clientHeight#比较
            if 截断!=自身.截断:#变了
                自身.截断=截断#记下
                自身.渲染()#提示开关跟着变

        def 排上():
            '挂上页面后再量。宽度跟着设置页变'
            测量()#先量一次
            观察类=getattr(窗口,'ResizeObserver',None)#没有就不跟着缩
            if 观察类 is None:#没有
                return#停
            def 变了(*_忽略):
                '宽度变了再量'
                测量()#再量
            自身.观察=观察类(变了)#观察
            自身.观察.observe(说明)#看这个说明
        窗口.setTimeout(排上,0)#等父级挂上
        return 自身.根#根

class 预设分区:
    '设置里的预设页：名册、默认、帮助、组装查看，以及创造模式入口'
    def __init__(自身,属性):
        '记下 props 并画出'
        自身.属性=属性#props
        自身.根=None#分区
        自身.指南=None#打开的帮助
        自身.指南实例=None#帮助对话框
        自身.查看触发=None#查看按钮，关掉后焦点回去
        自身.已拆=False#卸下时关过查看器
        自身.上次加载=None#上次 load
        自身.已订=False#是否已订阅
        自身.退订列=[]#退订
        自身.绘制中=False#防止重入
        自身.待重画=False#绘制中又脏了
        自身.渲染()#首画

    def 渲染(自身):
        '内置和自定义分两块。创造模式入口留在自定义组，组空着也在'
        if 自身.绘制中:#嵌套
            自身.待重画=True#等
            return 自身.根#旧根
        自身.绘制中=True#占住
        try:#整次绘制
            属性=自身.属性#props
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()#窗口
            文档=窗口.document#文档
            注入模块样式文件(#样式
                文档,
                '预设分区样式',
                os.path.join(os.path.dirname(__file__),'预设分区.module.css'),
                样式模块,
            )
            加载=属性.get('load')#读名册
            if 加载 is not None and 加载 is not 自身.上次加载:#挂上时读一次
                自身.上次加载=加载#记下
                加载()#读完再画

            def 读状态(值):
                '整份分区快照'
                return 值#原样

            def 读开发(值):
                '开发者工具是否开着'
                return 值#布尔

            状态=属性['useAgentPresetSection'](读状态)#分区
            开发=属性['useDeveloperTools'](读开发)#开发者工具
            旧=自身.根#上一份
            父=旧.parentNode if 旧 is not None else 属性.get('parent')#挂点
            if 旧 is not None:#拆旧
                旧.remove()#拿掉
            分区=模块节点(文档,'section',样式模块,'section')#页
            题=模块节点(文档,'h2',样式模块,'title')#标题
            题.textContent=中文['nav']#Agent 预设
            分区.appendChild(题)#放进
            导=模块节点(文档,'p',样式模块,'intro')#导语
            导.textContent=中文['sectionIntro']#导语
            分区.appendChild(导)#放进
            if 状态['error'] is not None:#有失败句
                误=模块节点(文档,'p',样式模块,'error')#错误
                误.setAttribute('role','alert')#提示
                误.textContent=状态['error']#句子
                分区.appendChild(误)#放进
            开始=属性.get('startCreatorDraft')#创造模式入口
            有创造=False#名册里有没有创造模式
            if 开始 is not None:#有会话流
                for 行 in 状态['rows']:#找
                    if 行.get('id')=='cordis':#创造模式
                        有创造=True#有
                        break#停
            创造钮=None#入口按钮
            if 有创造:#画入口
                创造钮=模块节点(文档,'button',样式模块,'creatorButton')#虚线入口
                创造钮.type='button'#按钮
                创造钮.disabled=状态['saving'] is True#保存时不可点
                加=图标加号16({'window':窗口,'size':14})#加号
                if 加 is not None:#有
                    创造钮.appendChild(加)#放进
                创造钮.appendChild(文档.createTextNode(中文['creatorDraft']))#让 Agent 帮我创建预设模式

                def 点创造(事件):
                    '暂存创造模式并关掉设置'
                    开始()#开一场
                    关=属性.get('close')#关设置
                    if 关 is not None:#有
                        关()#关
                创造钮.addEventListener('click',点创造)#点
            for 内置 in (True,False):#先内置，再自定义
                行列表=[]#这一组
                for 行 in 状态['rows']:#过滤
                    if 是否内置预设(行) is 内置 and (开发 or 需要编码工具(行) is not True):#工具关着藏起 PTC 和极简
                        行列表.append(行)#留下
                入口=None if 内置 else 创造钮#入口只在自定义组
                if len(行列表)==0 and 入口 is None:#这组什么都没有
                    continue#不画
                组=模块节点(文档,'section',样式模块,'group')#一组
                组头=模块节点(文档,'h3',样式模块,'groupHead')#组名
                组头.textContent=中文['builtInGroup'] if 内置 else 中文['customGroup']#内置或自定义
                组.appendChild(组头)#放进
                if len(行列表)>0:#有卡片
                    列表=模块节点(文档,'ul',样式模块,'cards')#卡片网格
                    for 行 in 行列表:#每张卡片
                        展示=预设展示文本(行,取中文)#中文名
                        帮助=指南表.get(行['id']) if 内置 else None#只有系统内置才有帮助
                        if 行.get('broken') is not None:#加载失败
                            动作=中文['brokenBadge']#加载失败
                        elif 行.get('isDefault'):#已是默认
                            动作=中文['inUse']#新任务默认
                        else:#可以设为默认
                            动作=中文['setDefault']#设为新任务默认
                        类名='card'#卡片
                        if 行.get('broken') is not None:#坏了
                            类名=类名+' cardBroken'#红边
                        if 行.get('isDefault'):#默认
                            类名=类名+' cardActive'#选中
                        项=模块节点(文档,'li',样式模块,类名)#一张
                        项.setAttribute('data-agent-preset-id',行['id'])#标识
                        主=模块节点(文档,'button',样式模块,'cardMain')#点卡片设默认
                        主.type='button'#按钮
                        主.setAttribute('aria-pressed','true' if 行.get('isDefault') else 'false')#是否默认
                        主.disabled=行.get('isDefault') is True or (行.get('broken') is None and 状态['saving'] is True)#默认或保存中
                        主.setAttribute('aria-disabled','true' if 行.get('broken') is not None else 'false')#坏了仍可聚焦
                        主.setAttribute('aria-label',动作+'：'+展示['name'])#动作和名字
                        主.title=动作#悬停

                        def 点卡片(事件,标识=行['id'],坏了=行.get('broken') is not None):
                            '坏掉的不能设为默认'
                            if 坏了 is not True:#健康
                                属性['makeDefault'](标识)#设默认
                        主.addEventListener('click',点卡片)#点
                        头=模块节点(文档,'span',样式模块,'cardHead')#头
                        身份=模块节点(文档,'span',样式模块,'cardIdentity')#名字和标记
                        名=模块节点(文档,'span',样式模块,'cardName')#名字
                        名.title=展示['name']#全文
                        名.textContent=展示['name']#名字
                        身份.appendChild(名)#放进
                        if 行.get('broken') is not None:#失败徽章
                            徽=模块节点(文档,'span',样式模块,'brokenBadge')#徽章
                            徽.appendChild(文档.createTextNode(中文['brokenBadge']))#加载失败
                            尖=模块节点(文档,'span',样式模块,'brokenTip')#原因
                            尖.setAttribute('aria-hidden','true')#读屏另有一条
                            尖.textContent=行['broken']#宿主报的原因
                            徽.appendChild(尖)#放进
                            身份.appendChild(徽)#放进
                        if 行.get('isDefault'):#默认标记
                            语气='solid'#实心
                            标记文=中文['inUse']#新任务默认
                        else:#组标记
                            语气='outline'#描边
                            标记文=中文['builtInGroup'] if 内置 else 中文['customGroup']#组名
                        记=标签({'window':窗口,'tone':语气,'children':标记文})#胶囊
                        记节点=记.渲染()#画出
                        if 记节点 is not None:#有
                            身份.appendChild(记节点)#放进
                        头.appendChild(身份)#放进
                        码=模块节点(文档,'code',样式模块,'cardId')#标识
                        码.title=行['id']#全文
                        码.textContent=行['id']#标识
                        头.appendChild(码)#放进
                        主.appendChild(头)#放进
                        述=展示['description'] if 展示.get('description') is not None else 中文['noDescription']#说明
                        说明=卡片说明({'window':窗口,'text':述})#四行以内的说明
                        说明节点=说明.渲染()#画出
                        if 说明节点 is not None:#有
                            主.appendChild(说明节点)#放进
                        if 行.get('broken') is not None:#读屏用的原因
                            因=模块节点(文档,'span',样式模块,'cardBrokenReason')#视觉上藏起
                            因.setAttribute('role','alert')#读出来
                            因.textContent=行['broken']#原因
                            主.appendChild(因)#放进
                        项.appendChild(主)#放进
                        脚=模块节点(文档,'div',样式模块,'cardFoot')#底部动作
                        if 帮助 is not None:#有帮助
                            帮=模块节点(文档,'div',样式模块,'cardHelp')#两个文字按钮
                            for 页名,键名 in (('explanation','modeExplanation'),('usage','howToUse')):#说明和用法
                                助=按钮({#文字按钮
                                    'window':窗口,
                                    'variant':'ghost',
                                    'className':'helpButton',
                                    'children':中文[键名],
                                })
                                助节点=助.渲染()#画出
                                if 助节点 is not None:#有
                                    助节点.setAttribute('aria-label',中文[键名]+'：'+展示['name'])#名字
                                    标样式模块(助节点,样式模块)#本页字号
                                    def 开帮助(事件,内容=帮助,页=页名):
                                        '打开对应的一页，不改默认预设'
                                        自身.指南={'content':内容,'page':页}#打开
                                        自身.指南实例=None#换一份
                                        自身.渲染()#重画
                                    助节点.addEventListener('click',开帮助)#点
                                    帮.appendChild(助节点)#放进
                            脚.appendChild(帮)#放进
                        看=模块节点(文档,'button',样式模块,'iconButton')#查看组装
                        看.type='button'#按钮
                        看.setAttribute('data-tip',中文['view'])#查看配置
                        看.setAttribute('aria-label',中文['view']+'：'+展示['name'])#名字
                        览=图标浏览16({'window':窗口})#浏览
                        if 览 is not None:#有
                            看.appendChild(览)#放进
                        def 点查看(事件,标识=行['id']):
                            '记住按钮，读完组装后焦点还能回来'
                            自身.查看触发=事件.currentTarget#按钮
                            属性['view'](标识)#打开
                        看.addEventListener('click',点查看)#点
                        脚.appendChild(看)#放进
                        项.appendChild(脚)#放进
                        列表.appendChild(项)#一张
                    组.appendChild(列表)#放进
                if 入口 is not None:#创造模式入口
                    组.appendChild(入口)#放在卡片后面
                分区.appendChild(组)#一组
            if 自身.指南 is not None:#帮助开着
                if 自身.指南实例 is None or 自身.指南实例.属性.get('guide') is not 自身.指南['content']:#换了一份
                    def 关指南():
                        '关掉帮助'
                        自身.指南=None#关
                        自身.指南实例=None#拆
                        自身.渲染()#重画
                    自身.指南实例=预设指南对话框({#打开时的那一页
                        'window':窗口,
                        'guide':自身.指南['content'],
                        'initialPage':自身.指南['page'],
                        'onClose':关指南,
                    })
                else:#同一份，跟着分区重画
                    自身.指南实例.渲染()#重画
                if 自身.指南实例.根 is not None:#有
                    分区.appendChild(自身.指南实例.根)#放进
            查看=状态['view']#组装查看器
            if 查看 is not None:#开着
                命中=None#名册行
                for 行 in 状态['rows']:#找
                    if 行['id']==查看['id']:#就是这份
                        命中=行#记下
                        break#停
                标题名=查看['title'] if 命中 is None else 预设展示文本(命中,取中文)['name']#标题

                def 关查看():
                    '关掉查看器，焦点回到查看按钮'
                    属性['closeView']()#关
                    if 自身.查看触发 is not None:#有按钮
                        自身.查看触发.focus()#回去

                def 查看按键(事件):
                    'Escape 只关查看器。Tab 留在里面'
                    if 事件.key=='Escape':#关闭
                        事件.preventDefault()#不关设置
                        事件.stopPropagation()#停
                        关查看()#关
                    else:#其它键
                        圈定阅读焦点(事件)#圈住
                预=模块节点(文档,'pre',样式模块,'viewerCode')#组装
                预.textContent=查看['content']#原文
                脚钮=按钮({'window':窗口,'variant':'outline','children':中文['close'],'onClick':关查看})#关闭
                脚节点=脚钮.渲染()#画出
                框=模态({#查看器
                    'window':窗口,
                    'open':True,
                    'onClose':关查看,
                    'closeLabel':中文['close'],
                    'title':中文['view']+' · '+标题名,
                    'className':'dialog',
                    'children':预,
                    'footer':脚节点,
                })
                框节点=框.渲染()#画出
                if 框节点 is not None:#有
                    卡=框节点.querySelector('.dialog')#卡片
                    if 卡 is not None:#有
                        标样式模块(卡,样式模块)#宽度
                    框节点.addEventListener('keydown',查看按键,True)#捕获
                    分区.appendChild(框节点)#放进
                    if 脚节点 is not None:#打开时聚焦关闭
                        def 聚焦关():
                            '等挂上后再聚焦'
                            脚节点.focus()#聚焦
                        窗口.setTimeout(聚焦关,0)#下一拍
            自身.根=分区#记下
            if 父 is not None:#挂回
                父.appendChild(自身.根)#挂上
            if 自身.已订 is not True:#订阅一次
                def 变更():
                    '快照变了就重画。页被拿掉时关掉还开着的查看器'
                    if 自身.绘制中:#还在画
                        自身.待重画=True#等
                        return#停
                    根=自身.根#当前
                    if 根 is not None and 根.parentNode is None:#已拿掉
                        for 退 in 自身.退订列:#先退订
                            退()#拆
                        自身.退订列=[]#空
                        自身.已订=False#可再订
                        if 自身.已拆 is not True:#只关一次
                            自身.已拆=True#记下
                            关=自身.属性.get('closeView')#关查看器
                            if 关 is not None:#有
                                关()#关
                        return#停
                    自身.渲染()#重画
                自身.退订列=[]#收集
                for 钩 in (属性.get('useAgentPresetSection'),属性.get('useDeveloperTools')):#两份
                    if 钩 is not None and hasattr(钩,'_subscribe') and callable(钩._subscribe):#有订阅
                        自身.退订列.append(钩._subscribe(变更))#订
                自身.已订=True#已订
        finally:#放开
            自身.绘制中=False#结束
        if 自身.待重画:#又脏了
            自身.待重画=False#清
            return 自身.渲染()#再画
        return 自身.根#根
