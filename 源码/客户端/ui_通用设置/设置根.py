__all__=['绘制设置','设置根','设置壳存储','准备页面设置']

from nicegui import ui as 界面
from .文案 import 中文 as 设置文案
from ..ui_对话.客户端.文案 import 中文 as 对话文案
from ..ui_主题.客户端.文案 import 中文 as 主题文案
from ..ui_主题.客户端.外观行 import 外观行
from ..ui_主题.客户端.字体设置组 import 字体设置组
from ..ui_主题.主题设置 import 默认字号表,默认字体族,规范化字体族,字号规格,字体角色,字体族变量
from ..ui_账号设置.客户端.文案 import 中文 as 账号文案
from ..ui_账号设置.客户端.账号分区 import 账号分区
from ..ui_智能体循环设置.客户端.文案 import 中文 as 循环文案
from ..ui_智能体循环设置.客户端.智能体循环卡片 import 智能体循环卡片
from ..ui_命令设置.客户端.文案 import 中文 as 终端文案
from ..ui_命令设置.客户端.终端卡片 import 终端卡片
from ..ui_web搜索设置.客户端.文案 import 中文 as 搜索文案
from ..ui_web搜索设置.客户端.网页搜索卡片 import 网页搜索卡片

def 造翻译(词典):
    '把词表收成翻译函数。缺键时返回键本身。'
    def 翻译(键,参数=None):
        '按键取词，再替换花括号参数。'
        if 键 not in 词典:
            return 键
        文本=词典[键]
        if 参数 is None:
            return 文本
        for 名 in 参数:
            文本=文本.replace('{'+名+'}',str(参数[名]))
        return 文本
    return 翻译

def 空字段():
    '一张可编辑的设置字段。'
    return {'text':'','invalid':False,'overridden':False}

def 绘制设置(界面状态):
    '设置对话框。左侧是全部分区，右侧画出该分区自己的控件。'
    界面状态['开发者工具']=False
    界面状态['忙碌回车']='queue'
    界面状态['设置分区']='通用'
    界面状态['账号提示']=''
    if '字号' not in 界面状态:
        界面状态['字号']=14
    if '字号表' not in 界面状态:
        界面状态['字号表']={**默认字号表,'text':界面状态['字号']}
    if '字体族' not in 界面状态:
        界面状态['字体族']=dict(默认字体族)
    if '外观' not in 界面状态:
        界面状态['外观']='system'
    循环态={'maxParallelToolCalls':空字段(),'writable':True,'saving':False,'failed':False}
    终端态={'timeoutMs':空字段(),'maxOutputBytes':空字段(),'writable':True,'saving':False,'failed':False}
    搜索态={
        'apiKey':空字段(),'baseURL':空字段(),'maxUses':空字段(),
        'apiKeyConfigured':False,'apiKeyWritable':True,'writable':True,'saving':False,'failed':False,
    }
    分区表=(
        ('通用',设置文案['general.nav']),
        ('账号',账号文案['nav']),
        ('循环',循环文案['title']),
        ('终端',终端文案['title']),
        ('搜索',搜索文案['title']),
    )
    译主题=造翻译(主题文案)
    译账号=造翻译(账号文案)
    译循环=造翻译(循环文案)
    译终端=造翻译(终端文案)
    译搜索=造翻译(搜索文案)
    已排队={'是':False}
    with 界面.dialog() as 对话框:
        with 界面.card().classes('设置卡'):
            with 界面.row().classes('设置身'):
                导航=界面.column().classes('设置导航')
                with 界面.column().classes('设置右'):
                    with 界面.row().classes('设置头'):
                        def 关闭():
                            '关掉对话框，并丢掉未保存草稿。'
                            丢弃草稿(循环态)
                            丢弃草稿(终端态)
                            丢弃草稿(搜索态)
                            界面状态['设置打开']=False
                            对话框.close()
                        关闭标='<svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M2.5 2.5L13.5 13.5" stroke="currentColor" stroke-width="1"/><path d="M13.5 2.5L2.5 13.5" stroke="currentColor" stroke-width="1"/></svg>'
                        关闭钮=界面.button(on_click=关闭).props('flat dense no-caps aria-label="'+设置文案['close']+'"').classes('图标钮 内标 关闭钮')
                        with 关闭钮:
                            界面.html(关闭标,sanitize=False)
                    内容=界面.column().classes('设置内容')
    def 改字段(状态,键,文):
        '把输入写进该字段的草稿。'
        状态[键]['text']=文
        状态[键]['overridden']=True
    def 丢弃草稿(状态):
        '离开分区时丢掉未保存草稿。'
        for 值 in 状态.values():
            if isinstance(值,dict) and 'overridden' in 值:
                值['text']=''
                值['overridden']=False
                值['invalid']=False
    def 画通用():
        '通用：开发者工具、忙碌回车、外观和字号。'
        def 切换开发者(事件):
            '开关写入页面状态。'
            界面状态['开发者工具']=事件.value
        with 界面.row().classes('设置行'):
            with 界面.column().classes('设置行文'):
                界面.label(设置文案['developerTools.title']).classes('设置行题')
                界面.label(设置文案['developerTools.description']).classes('设置行述')
            界面.switch(value=界面状态['开发者工具'],on_change=切换开发者).props('aria-label="'+设置文案['developerTools.title']+'"')
        with 界面.row().classes('设置行 回车行'):
            with 界面.column().classes('设置行文'):
                界面.label(对话文案['settings.enter.title']).classes('设置行题')
                界面.label(对话文案['settings.enter.description']).classes('设置行述')
            当前回车=对话文案['settings.enter.queue'] if 界面状态['忙碌回车']=='queue' else 对话文案['settings.enter.steer']
            回车菜单=界面.column().classes('回车菜单')
            回车菜单.set_visibility(False)
            def 改回车(值,文):
                '记下 queue 或 steer，并收起菜单。'
                def 点():
                    界面状态['忙碌回车']=值
                    回车文.set_text(文)
                    回车菜单.set_visibility(False)
                return 点
            with 回车菜单:
                界面.button(对话文案['settings.enter.queue'],on_click=改回车('queue',对话文案['settings.enter.queue'])).props('flat no-caps align=left').classes('指令项')
                界面.button(对话文案['settings.enter.steer'],on_click=改回车('steer',对话文案['settings.enter.steer'])).props('flat no-caps align=left').classes('指令项')
            def 开关回车():
                '展开或收起忙碌回车菜单。'
                回车菜单.set_visibility(not 回车菜单.visible)
            回车钮=界面.button(on_click=开关回车).props('flat no-caps').classes('回车钮').style('color: var(--dsw-alias-label-primary) !important')
            with 回车钮:
                回车文=界面.label(当前回车)
                界面.html('<svg width="12" height="12" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M4 6L7.29289 9.29289C7.68342 9.68342 8.31658 9.68342 8.70711 9.29289L12 6" stroke="currentColor" stroke-width="1"/></svg>',sanitize=False)
        def 用外观(选):
            '把外观和三种字体交给选择器。'
            return 选({
                'preference':界面状态['外观'],
                'fontSize':界面状态['字号表']['text'],
                'fontSizes':界面状态['字号表'],
                'fontFamilies':界面状态['字体族'],
            })
        def 设主题(值):
            '写入外观。深色立刻改页面底色，再重画选中态。'
            界面状态['外观']=值
            应用外观()
            稍后重画()
        def 设字号(角色,值):
            '写入该角色的字号。正文同时刷新消息。'
            界面状态['字号表'][角色]=值
            if 角色=='text':
                界面状态['字号']=值
                if '刷新消息' in 界面状态:
                    界面状态['刷新消息']()
            应用外观()
            稍后重画()
        def 设字体(角色,值):
            '写入规范化后的字体列表。'
            界面状态['字体族'][角色]=规范化字体族(值)
            应用外观()
            稍后重画()
        外观行({'t':译主题,'useStore':用外观,'setTheme':设主题})
        字体设置组({'t':译主题,'useStore':用外观,'setFontSize':设字号,'setFontFamily':设字体})
    def 画循环():
        'Agent 循环的并行上限。'
        def 用卡(选):
            '整份循环快照。'
            return 选(循环态)
        def 编辑(键,文):
            '改并行上限草稿。'
            改字段(循环态,键,文)
        def 复位(键):
            '清空该字段草稿。'
            循环态[键]['text']=''
            循环态[键]['overridden']=False
        智能体循环卡片({
            't':译循环,'view':'form','useAgentLoopCard':用卡,
            'edit':编辑,'resetField':复位,'save':稍后重画,'discard':稍后重画,
        })
    def 画终端():
        '命令超时和输出上限。'
        def 用卡(选):
            '整份终端快照。'
            return 选(终端态)
        def 编辑(键,文):
            '改终端字段草稿。'
            改字段(终端态,键,文)
        def 复位(键):
            '清空该字段草稿。'
            终端态[键]['text']=''
            终端态[键]['overridden']=False
        终端卡片({
            't':译终端,'view':'form','useShellCard':用卡,
            'edit':编辑,'resetField':复位,'save':稍后重画,'discard':稍后重画,
        })
    def 画搜索():
        '网页搜索的密钥、地址和次数。'
        def 用卡(选):
            '整份搜索快照。'
            return 选(搜索态)
        def 编辑(键,文):
            '改搜索字段草稿。'
            改字段(搜索态,键,文)
        def 复位(键):
            '清空该字段草稿。'
            搜索态[键]['text']=''
            搜索态[键]['overridden']=False
        网页搜索卡片({
            't':译搜索,'view':'form','useWebSearchCard':用卡,
            'edit':编辑,'resetField':复位,'save':稍后重画,'discard':稍后重画,
        })
    def 应用外观():
        '按偏好给 body 打深色标记，并写下内容字号。令牌表和输入卡片读这两个值。'
        外观=界面状态['外观']
        字号=界面状态['字号表']['text']
        字体脚本=''
        for 角色 in 字体角色:
            字体脚本+="document.body.style.setProperty('"+字号规格[角色]['variable']+"','"+str(界面状态['字号表'][角色])+"px');"
            列表=界面状态['字体族'].get(角色) or ''
            if len(列表)>0:
                字体脚本+="document.body.style.setProperty('"+字体族变量(角色)+"',"+repr(列表)+");"
            else:
                字体脚本+="document.body.style.removeProperty('"+字体族变量(角色)+"');"
        脚本=(
            "var 外观="+repr(外观)+";"
            "var 深色=外观==='dark'||(外观==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);"
            "document.body.toggleAttribute('data-ds-dark-theme',深色);"
            "document.body.style.setProperty('--dsh-content-font-delta','"+str(字号-14)+"px');"
            "document.body.style.setProperty('--dsh-content-font-size-secondary','"+str(字号-1 if 字号<=14 else 字号-2)+"px');"
            +字体脚本
        )
        界面.run_javascript(脚本)
    def 重画():
        '按当前分区清空内容列再画。'
        内容.clear()
        导航.clear()
        with 导航:
            界面.label(设置文案['title']).classes('设置标题')
            导航列=界面.column().classes('设置导航列')
            with 导航列:
                for 标识,标签 in 分区表:
                    def 造点(某):
                        '选中该分区。等点击结束再重画，避免拆掉正在响应的按钮。'
                        def 点击():
                            '记下分区。换分区时丢掉未保存草稿。'
                            if 某!=界面状态['设置分区']:
                                丢弃草稿(循环态)
                                丢弃草稿(终端态)
                                丢弃草稿(搜索态)
                            界面状态['设置分区']=某
                            稍后重画()
                        return 点击
                    钮=界面.button(on_click=造点(标识)).props('flat align=left no-caps').classes('设置项').style('color: var(--dsw-alias-label-primary) !important')
                    with 钮:
                        if 标识=='账号':
                            界面.html('<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 8.25C9.51878 8.25 10.75 7.01878 10.75 5.5C10.75 3.98122 9.51878 2.75 8 2.75C6.48122 2.75 5.25 3.98122 5.25 5.5C5.25 7.01878 6.48122 8.25 8 8.25Z" stroke="currentColor" stroke-width="1.3"/><path d="M2.5 14.5C2.5 11.5 5.25 10.25 8 10.25C10.75 10.25 13.5 11.5 13.5 14.5" stroke="currentColor" stroke-width="1.3"/></svg>',sanitize=False)
                        else:
                            界面.html('<svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true"><path d="M8 9.75012C8.9665 9.75012 9.75 8.96662 9.75 8.00012C9.75 7.03362 8.9665 6.25012 8 6.25012C7.0335 6.25012 6.25 7.03362 6.25 8.00012C6.25 8.96662 7.0335 9.75012 8 9.75012Z" stroke="currentColor" stroke-width="1.3"/><path d="M13.0107 7.79377C12.9505 7.89401 12.9205 7.94413 12.9205 7.99951C12.9205 8.0549 12.9505 8.10502 13.0106 8.20528L13.9849 9.83006C14.045 9.93029 14.0751 9.9804 14.0751 10.0358C14.0751 10.0911 14.045 10.1413 13.9849 10.2415L13.0037 11.8777C12.9468 11.9726 12.9184 12.0201 12.8725 12.0461C12.8267 12.072 12.7713 12.072 12.6607 12.072H10.6704C10.5598 12.072 10.5045 12.072 10.4586 12.098C10.4128 12.1239 10.3843 12.1714 10.3274 12.2662L9.33825 13.9142C9.28133 14.009 9.25287 14.0564 9.20703 14.0823C9.16118 14.1083 9.10588 14.1083 8.99529 14.1083H7.00486C6.89426 14.1083 6.83896 14.1083 6.79312 14.0823C6.74727 14.0564 6.71881 14.009 6.6619 13.9142L5.67273 12.2662C5.61581 12.1714 5.58735 12.1239 5.54151 12.098C5.49566 12.072 5.44036 12.072 5.32977 12.072H3.33945C3.2288 12.072 3.17347 12.072 3.12761 12.0461C3.08176 12.0201 3.0533 11.9726 2.9964 11.8777L2.0152 10.2415C1.9551 10.1413 1.92505 10.0911 1.92505 10.0358C1.92505 9.9804 1.9551 9.93029 2.0152 9.83006L2.98951 8.20528C3.04963 8.10502 3.07969 8.0549 3.07969 7.99951C3.07968 7.94413 3.04961 7.89401 2.98946 7.79377L2.01529 6.17011C1.95514 6.06987 1.92507 6.01975 1.92507 5.96437C1.92506 5.90899 1.95512 5.85886 2.01524 5.7586L2.9964 4.1224C3.0533 4.0275 3.08176 3.98005 3.12761 3.95408C3.17347 3.92811 3.2288 3.92811 3.33945 3.92811H5.32977C5.44036 3.92811 5.49566 3.92811 5.54151 3.90216C5.58735 3.87621 5.61581 3.82879 5.67273 3.73397L6.6619 2.08599C6.71881 1.99116 6.74727 1.94375 6.79312 1.9178C6.83896 1.89185 6.89426 1.89185 7.00486 1.89185H8.99529C9.10588 1.89185 9.16118 1.89185 9.20703 1.9178C9.25287 1.94375 9.28133 1.99116 9.33825 2.08599L10.3274 3.73397C10.3843 3.82879 10.4128 3.87621 10.4586 3.90216C10.5045 3.92811 10.5598 3.92811 10.6704 3.92811H12.6607C12.7713 3.92811 12.8267 3.92811 12.8725 3.95408C12.9184 3.98005 12.9468 4.0275 13.0037 4.1224L13.9849 5.7586C14.045 5.85886 14.0751 5.90899 14.0751 5.96437C14.0751 6.01975 14.045 6.06987 13.9849 6.17011L13.0107 7.79377Z" stroke="currentColor" stroke-width="1.3" stroke-miterlimit="10"/></svg>',sanitize=False)
                        界面.label(标签).classes('设置项文')
                    if 标识==界面状态['设置分区']:
                        钮.classes(add='设置当前')
        with 内容:
            分区=界面状态['设置分区']
            if 分区=='通用':
                画通用()
                return
            if 分区=='账号':
                def 用账号(选):
                    '未登录快照。view 不能是 None，否则登录按钮会被组件自己禁用。'
                    return 选({'view':{'status':'signed-out'},'details':None,'failed':False})
                def 开始登录():
                    '记下说明。登录服务不在这个页面里。'
                    界面状态['账号提示']=账号文案['settingsSignedOutDescription']
                    稍后重画()
                账号分区({'t':译账号,'start':开始登录,'useAccount':用账号})
                if 界面状态['账号提示']!='':
                    界面.label(界面状态['账号提示'])
                return
            if 分区=='循环':
                画循环()
                return
            if 分区=='终端':
                画终端()
                return
            画搜索()
    槽=getattr(内容,'parent_slot',None)
    父=getattr(槽,'parent',None) if 槽 is not None else None
    稳定=父 if 父 is not None else 内容
    def 稍后重画():
        '只打标记。定时器在建页时挂在内容列外面。'
        已排队['是']=True
    def 拍():
        '有标记才重画。'
        if not 已排队['是']:
            return
        已排队['是']=False
        重画()
    with 稳定:
        界面.timer(0.05,拍)
    def 打开():
        '打开设置并画出当前分区。'
        界面状态['设置打开']=True
        应用外观()
        重画()
        对话框.open()
    界面状态['打开设置']=打开
    应用外观()


class 设置壳存储:
    '设置对话框的开合和当前分区。create 交回自身，槽位按属性读快照'

    def __init__(自身):
        '默认关着，没有选中分区'
        自身._状态={'open':False,'activeId':None}#状态
        自身._监听=[]#订阅
        自身.actions={#动作
            'open':自身._打开,#打开
            'close':自身._关闭,#关闭
            'select':自身._选择,#选分区
            'openSection':自身._打开分区,#打开并选中
        }#动作结束

    def getSnapshot(自身):
        '拷贝一份，避免调用方改到内部'
        return {'open':自身._状态['open'],'activeId':自身._状态['activeId']}#快照

    def subscribe(自身,回调):
        '登记变更'
        自身._监听.append(回调)#订
        def 拆():
            '退订'
            if 回调 in 自身._监听:#还在
                自身._监听.remove(回调)#去掉
        return 拆#拆除

    def _通知(自身):
        '广播给订阅者'
        for 回调 in list(自身._监听):#快照
            回调()#通知

    def _打开(自身):
        '打开对话框'
        自身._状态['open']=True#开
        自身._通知()#广播

    def _关闭(自身):
        '关掉并清掉选中分区'
        自身._状态['open']=False#关
        自身._状态['activeId']=None
        自身._通知()#广播

    def _选择(自身,标识):
        '只换分区'
        自身._状态['activeId']=标识#选
        自身._通知()#广播

    def _打开分区(自身,标识):
        '打开并选中这个分区'
        自身._状态['activeId']=标识#选
        自身._状态['open']=True#开
        自身._通知()#广播

    def create(自身):
        '根作用域只保留这一份'
        return 自身#共享


class 设置根:
    '侧栏底部的设置入口。打开后是分区导航和当前分区'

    样式表=(
        '.设置入口{width:100%;align-items:center;flex-wrap:nowrap}'
        '.设置罩{position:fixed;inset:0;z-index:1000;display:flex;align-items:center;justify-content:center;background:var(--dsw-alias-bg-mask-1,rgba(0,0,0,.24))}'
        '.设置面板{position:relative;display:flex;flex-direction:row;flex-wrap:nowrap;align-items:stretch;width:min(800px,calc(100vw - 48px));height:min(800px,calc(100vh - 48px));border-radius:var(--dsw-radius-panel,16px);overflow:hidden;background:var(--dsw-alias-bg-layer-2,#fff);color:var(--dsw-alias-label-primary);box-shadow:var(--dsw-elevation-prominent)}'
        '.设置导航{flex:none;display:flex;flex-direction:column;width:188px;box-sizing:border-box;overflow:auto}'
        '.设置内容{flex:1 1 auto;min-width:0;overflow:auto}'
    )
    样式已登记=False

    def __init__(自身,属性):
        '记下 props 并画出'
        自身.属性=属性 if isinstance(属性,dict) else {}#合成 props
        自身.根=None#可清空的列
        自身._已订=False#只订一次
        自身.渲染()#槽位只调用构造

    def 文(自身,键):
        '设置文案。缺译时返回键'
        译=自身.属性['t'] if 't' in 自身.属性 else None#座位
        if callable(译):
            try:
                return 译(键)#词
            except Exception:
                return '文案没有读到'
        return 键#键

    def 快照(自身):
        '读开合状态'
        用=自身.属性['useStore'] if 'useStore' in 自身.属性 else None#钩
        if callable(用):
            值=用(lambda 态:态)#整份
            if isinstance(值,dict):#是快照
                return 值#用
        return {'open':False,'activeId':None}#关

    def 画槽(自身,名,拥有方=None,选项=None):
        '有 renderSlot 才画'
        画=自身.属性['renderSlot'] if 'renderSlot' in 自身.属性 else None#座位
        if callable(画) is not True:#没装
            return#跳过
        方={} if 拥有方 is None else 拥有方#属主
        if 选项 is None:#无
            画(名,方)#画
            return
        画(名,方,选项)#带选项

    def 渲染(自身):
        '入口行；开着时再盖一层对话框。对话框用固定定位，不占网格格。'
        if 设置根.样式已登记 is not True:
            界面.add_css(设置根.样式表, shared=True)
            设置根.样式已登记=True
        属性=自身.属性#props
        宽=属性['wide'] if 'wide' in 属性 else True#宽轨
        动作=属性['actions'] if 'actions' in 属性 and isinstance(属性['actions'],dict) else {}#动作
        快照=自身.快照()#开合
        开着=快照.get('open') is True#是否开
        分区=[]#导航行
        用分区=属性['useSections'] if 'useSections' in 属性 else None#分区钩
        if callable(用分区):
            值=用分区(lambda 行:行)#整表
            if isinstance(值,list):#是列表
                分区=值#用
        当前=快照.get('activeId')#选中
        if 当前 is None and len(分区)>0 and isinstance(分区[0],dict):#落到第一项
            当前=分区[0].get('id')#第一
        if 自身.根 is None:#新建
            自身.根=界面.column().classes('设置壳')#壳
        自身.根.clear()
        with 自身.根:#壳
            def 点开():
                '打开设置'
                if 'open' in 动作:
                    动作['open']()#开
            with 界面.row().classes('设置入口'):
                自身.画槽('settings.launcher',{'wide':宽,'settingsOpen':开着,'openSettings':动作.get('open')})
                if 宽:
                    界面.button(自身.文('trigger'),on_click=点开).props('flat no-caps')
                else:
                    设置钮=界面.button(on_click=点开).props('flat dense round')
                    设置钮.tooltip(自身.文('trigger'))
                    with 设置钮:
                        界面.icon('settings', size='18px')
                自身.画槽('settings.trigger',{'wide':宽})
            if 开着:#对话框
                with 界面.element('div').classes('设置罩'):#罩
                    with 界面.element('div').classes('设置面板'):#面板
                        with 界面.column().classes('设置导航'):#导航
                            自身.画槽('settings.header',{})#标题
                            for 行 in 分区:#逐分区
                                if not isinstance(行,dict):#不是行
                                    continue#跳
                                标识=行.get('id')#id
                                标签=行.get('label') or 标识#标签
                                def 点选(钉=标识):
                                    '换分区'
                                    if 'select' in 动作 and 钉 is not None:
                                        动作['select'](钉)#选
                                界面.button(str(标签) if 标签 is not None else '',on_click=点选).props('flat no-caps'+(' aria-current=true' if 标识==当前 else ''))#项
                        with 界面.column().classes('设置内容'):#正文
                            with 界面.row():#头
                                自身.画槽('settings.action',{})#动作
                                def 点关():
                                    '关闭'
                                    if 'close' in 动作:
                                        动作['close']()#关
                                界面.button(on_click=点关).props('flat dense icon=close')#关
                                自身.画槽('settings.close',{})#关闭名
                            if 当前 is not None:
                                自身.画槽('settings.section',{'close':动作.get('close')},{'only':当前})#正文
        if 自身._已订 is not True:#还没订
            用=属性['useStore'] if 'useStore' in 属性 else None#钩
            订=getattr(用,'_subscribe',None) if 用 is not None else None#订阅
            if callable(订):#能订
                def 变更():
                    '开合或分区变了就重画。控件已经不在页面上时，把失败留在页面上。'
                    根=自身.根
                    if 根 is None:
                        return
                    try:
                        自身.渲染()
                    except Exception as 错误:
                        名=type(错误).__name__
                        原文=str(错误.args[0]) if len(错误.args)>0 else ''
                        界面.label(名 if 原文=='' else 名+'：'+原文)
                订(变更)#订上
                自身._已订=True#只订一次

    def __call__(自身):
        '再画一次'
        return 自身.渲染()

def 准备页面设置():
    '没有插件登记表时，侧栏底部仍用这一份开合状态和五个分区。每次重画新建控件，状态留在这里。'
    壳=设置壳存储()
    主题={
        'preference':'system',
        'fontSize':默认字号表['text'],
        'fontSizes':dict(默认字号表),
        'fontFamilies':dict(默认字体族),
    }
    循环态={'maxParallelToolCalls':空字段(),'writable':True,'saving':False,'failed':False}
    终端态={'timeoutMs':空字段(),'maxOutputBytes':空字段(),'writable':True,'saving':False,'failed':False}
    搜索态={
        'apiKey':空字段(),'baseURL':空字段(),'maxUses':空字段(),
        'apiKeyConfigured':False,'apiKeyWritable':True,'writable':True,'saving':False,'failed':False,
    }
    账号提示={'文':''}
    译主题=造翻译(主题文案)
    译账号=造翻译(账号文案)
    译循环=造翻译(循环文案)
    译终端=造翻译(终端文案)
    译搜索=造翻译(搜索文案)
    分区=[
        {'id':'general','label':设置文案['general.nav']},
        {'id':'account','label':账号文案['nav']},
        {'id':'loop','label':循环文案['title']},
        {'id':'shell','label':终端文案['title']},
        {'id':'search','label':搜索文案['title']},
    ]
    def 用设置(投影):
        '开合和当前分区'
        return 投影(壳.getSnapshot())
    用设置._subscribe=壳.subscribe
    def 用主题(投影):
        '外观和三种字体'
        return 投影(主题)
    def 用分区(投影):
        '导航行'
        return 投影(分区)
    def 刷新壳():
        '分区控件改了状态后重画对话框'
        壳._通知()
    def 应用外观():
        '按偏好给 body 打深色标记，并写下内容字号'
        字号=主题['fontSizes']['text']
        字体脚本=''
        for 角色 in 字体角色:
            字体脚本+="document.body.style.setProperty('"+字号规格[角色]['variable']+"','"+str(主题['fontSizes'][角色])+"px');"
            列表=主题['fontFamilies'].get(角色) or ''
            if len(列表)>0:
                字体脚本+="document.body.style.setProperty('"+字体族变量(角色)+"',"+repr(列表)+");"
            else:
                字体脚本+="document.body.style.removeProperty('"+字体族变量(角色)+"');"
        脚本=(
            "var 外观="+repr(主题['preference'])+";"
            "var 深色=外观==='dark'||(外观==='system'&&window.matchMedia('(prefers-color-scheme: dark)').matches);"
            "document.body.toggleAttribute('data-ds-dark-theme',深色);"
            "document.body.style.setProperty('--dsh-content-font-delta','"+str(字号-14)+"px');"
            "document.body.style.setProperty('--dsh-content-font-size-secondary','"+str(字号-1 if 字号<=14 else 字号-2)+"px');"
            +字体脚本
        )
        界面.run_javascript(脚本)
    def 设主题(值):
        '写入外观并重画选中态'
        主题['preference']=值
        应用外观()
        刷新壳()
    def 设字号(角色,值):
        '写入该角色的字号'
        主题['fontSizes'][角色]=值
        if 角色=='text':
            主题['fontSize']=值
        应用外观()
        刷新壳()
    def 设字体(角色,值):
        '写入规范化后的字体列表'
        主题['fontFamilies'][角色]=规范化字体族(值)
        应用外观()
        刷新壳()
    def 改字段(状态,键,文):
        '把输入写进该字段的草稿'
        if 键 not in 状态 or not isinstance(状态[键],dict):
            return
        状态[键]['text']=文
        状态[键]['overridden']=True
    def 复位字段(状态,键):
        '清空该字段草稿并重画'
        if 键 not in 状态 or not isinstance(状态[键],dict):
            return
        状态[键]['text']=''
        状态[键]['overridden']=False
        状态[键]['invalid']=False
        刷新壳()
    def 画分区(标识):
        '当前分区的控件。标识来自导航行。'
        if 标识=='general':
            外观行({'t':译主题,'useStore':用主题,'setTheme':设主题})
            字体设置组({'t':译主题,'useStore':用主题,'setFontSize':设字号,'setFontFamily':设字体})
            return
        if 标识=='account':
            def 用账号(选):
                '未登录快照。view 缺席时登录按钮会被组件自己禁用。'
                return 选({'view':{'status':'signed-out'},'details':None,'failed':False})
            def 开始登录():
                '这个页面没有登录服务，只留下说明'
                账号提示['文']=账号文案['settingsSignedOutDescription'] if 'settingsSignedOutDescription' in 账号文案 else ''
                刷新壳()
            账号分区({'t':译账号,'start':开始登录,'useAccount':用账号})
            if 账号提示['文']!='':
                界面.label(账号提示['文'])
            return
        if 标识=='loop':
            智能体循环卡片({
                't':译循环,'view':'form','useAgentLoopCard':lambda 选:选(循环态),
                'edit':lambda 键,文:改字段(循环态,键,文),
                'resetField':lambda 键:复位字段(循环态,键),
                'save':刷新壳,'discard':刷新壳,
            })
            return
        if 标识=='shell':
            终端卡片({
                't':译终端,'view':'form','useShellCard':lambda 选:选(终端态),
                'edit':lambda 键,文:改字段(终端态,键,文),
                'resetField':lambda 键:复位字段(终端态,键),
                'save':刷新壳,'discard':刷新壳,
            })
            return
        if 标识=='search':
            网页搜索卡片({
                't':译搜索,'view':'form','useWebSearchCard':lambda 选:选(搜索态),
                'edit':lambda 键,文:改字段(搜索态,键,文),
                'resetField':lambda 键:复位字段(搜索态,键),
                'save':刷新壳,'discard':刷新壳,
            })
    def 画出(转发槽,宽=True):
        '新建一颗设置壳，开合状态与上面的分区共用'
        def 设置槽(名,拥有方=None,选项=None):
            '分区正文在这里画。其余槽交给页面。'
            if 名=='settings.section':
                只=选项['only'] if isinstance(选项,dict) and 'only' in 选项 else None
                画分区(只)
                return True
            if callable(转发槽):
                方={} if 拥有方 is None else 拥有方
                if 选项 is None:
                    return 转发槽(名,方)
                return 转发槽(名,方,选项)
            return None
        return 设置根({
            'wide':宽 is True,
            't':造翻译(设置文案),
            'useStore':用设置,
            'actions':壳.actions,
            'useSections':用分区,
            'renderSlot':设置槽,
        })
    return 画出
