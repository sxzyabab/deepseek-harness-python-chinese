from ....基础设施.通用工具 import 路径转正斜杠

__all__=['会话根','工作区标签','派生阶段']#仅中文公开名

from nicegui import ui as 界面
from ...ui_基础界面组件.鱼标 import 鱼标
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败

def 恒等翻译(键,参数=None):
    '无宿主文案时用本包中文词典，没有则返回键本身。'
    if 键 not in 对话文案:#词典没有
        return 键#键
    文本=对话文案[键]#词条
    if 参数 is None:#无参数
        return 文本#原文
    for 名 in 参数:#替换占位
        文本=文本.replace('{'+名+'}',str(参数[名]))#替换
    return 文本#译完

def 空渲染槽(*位置参数,**关键字参数):
    '未注入槽渲染时不画'
    return None#不画

def 工作区标签(工作目录):
    '分隔符-only 路径回显原 cwd'
    if 工作目录 is None or 工作目录=='':#空
        return 工作目录#原样
    段=路径转正斜杠(工作目录).rstrip('/').split('/')#分段
    基=段[-1] if len(段)>0 else ''#末段；判 length
    return 基 if 基!='' else 工作目录#空则原路径

def 派生阶段(会话标识,作曲阶段,打开态,摘要空白):
    '沉降：有会话且 blank+loading 且摘要未证 blank'
    沉降=会话标识 is not None and 作曲阶段=='blank' and 打开态=='loading' and 摘要空白 is not True#沉降
    英雄=会话标识 is None or (作曲阶段=='blank' and (打开态=='open' or 摘要空白 is True))#英雄
    if 沉降 is True:#沉降优先
        return 'settling'#沉降
    if 英雄 is True:#英雄
        return 'hero'#英雄
    return 'active'#活动

def 取打开态(快照):
    'openState'
    return 快照['openState'] if 'openState' in 快照 else None#打开

def 取作曲阶段(快照):
    'composerPhase'
    return 快照['composerPhase'] if 'composerPhase' in 快照 else None#相位

def 取未决(快照):
    'pending。空列表保留'
    列=快照['pending'] if 'pending' in 快照 else None#未决
    return 列 if 列 is not None else []#空则空表

def 取自身(快照):
    '快照原样'
    return 快照#原样

def 取阻断(值):
    '阻断原样'
    return 值#原样

class 会话根:#常驻会话骨架
    '英雄铬、composer 定位与会话链同树挂载'
    def __init__(自身,属性=None):
        '记下合成 props 与本地选择器态'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.选择器开=False#工作区菜单
        自身.待选工作区标识=None#刚挑的工作区
        自身.席位高度=0#composer 席高度
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 切换选择器(自身):
        '翻转工作区选择器'
        自身.选择器开=not 自身.选择器开#翻转

    def 关闭选择器(自身):
        '关闭'
        自身.选择器开=False#关

    def 挑选工作区(自身,工作区标识):
        '关菜单、记下待选并调用 selectWorkspace'
        自身.选择器开=False#关
        自身.待选工作区标识=工作区标识#待选
        选定=自身.属性['selectWorkspace'] if 'selectWorkspace' in 自身.属性 else None#回调
        if 选定 is not None:#有
            选定(工作区标识)#打开空白会话

    def 清理待选(自身,会话工作区标识,工作区相位,待选仍在):
        '会话落盘或列表就绪且已删则清'
        if 自身.待选工作区标识 is None:#无待选
            return#无事
        if 会话工作区标识==自身.待选工作区标识 or (工作区相位=='ready' and 待选仍在 is False):#已落或消失
            自身.待选工作区标识=None#清

    def 记录席位高度(自身,高度):
        '供回到底部按钮 clearance'
        自身.席位高度=高度#记下

    def 渲染(自身):
        '与上游 JSX 同构的阶段/区/栏调度'
        属性=自身.属性#props
        翻译=属性['t'] if 't' in 属性 else 恒等翻译#文案
        用会话=属性['useSession'] if 'useSession' in 属性 else None#会话钩
        取会话列表=属性['useSessions'] if 'useSessions' in 属性 else None#列表钩
        用工作区=属性['useWorkspaces'] if 'useWorkspaces' in 属性 else None#工作区钩
        用输入=属性['useInput'] if 'useInput' in 属性 else None#输入钩
        用阻断=属性['useComposerBlock'] if 'useComposerBlock' in 属性 else None#阻断钩
        渲染槽=属性['renderSlot'] if 'renderSlot' in 属性 else 空渲染槽#单槽
        渲染链=属性['renderSlotChain'] if 'renderSlotChain' in 属性 else 空渲染槽#链
        会话标识=属性['sessionId'] if 'sessionId' in 属性 else None#会话 id
        打开态=用会话(取打开态) if 用会话 is not None else None#打开态
        作曲阶段=用会话(取作曲阶段) if 用会话 is not None else None#composer 相位
        未决=用会话(取未决) if 用会话 is not None else []#未决交互
        会话=用会话(取自身) if 用会话 is not None else None#整快照
        输入态=用输入(取自身) if 用输入 is not None else None#输入机
        def 取cwd(表):
            'byId[sessionId].cwd。表为 dict'
            if 会话标识 is None:#无会话
                return None#无
            册=表['byId'] if 'byId' in 表 else None#byId
            摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
            return 摘要['cwd'] if 摘要 is not None and 'cwd' in 摘要 else None#cwd
        def 取blank(表):
            'byId[sessionId].blank'
            if 会话标识 is None:#无会话
                return None#无
            册=表['byId'] if 'byId' in 表 else None#byId
            摘要=册[会话标识] if 册 is not None and 会话标识 in 册 else None#摘要
            return 摘要['blank'] if 摘要 is not None and 'blank' in 摘要 else None#blank
        工作目录=取会话列表(取cwd) if 取会话列表 is not None else None#cwd
        摘要空白=取会话列表(取blank) if 取会话列表 is not None else None#blank
        工作区=用工作区(取自身) if 用工作区 is not None else {'items':[],'phase':'loading'}#工作区表
        作曲阻断=用阻断(取阻断) if 用阻断 is not None else None#阻断值
        条目=工作区['items'] if 'items' in 工作区 and 工作区['items'] is not None else []#工作区列表
        会话工作区=None#所属
        if 会话标识 is not None:#有会话
            for 项 in 条目:#找所属
                标识列表=项['sessionIds'] if 'sessionIds' in 项 and 项['sessionIds'] is not None else []#会话集
                if 会话标识 in 标识列表:#命中
                    会话工作区=项#记下
                    break#停
        待选工作区=None#待选对象
        for 项 in 条目:#找待选
            if ('workspaceId' in 项) and 项['workspaceId']==自身.待选工作区标识:#命中
                待选工作区=项#记下
                break#停
        会话工作区标识=会话工作区['workspaceId'] if 会话工作区 is not None and 'workspaceId' in 会话工作区 else None#属主
        工作区相位=工作区['phase'] if 'phase' in 工作区 else None#相位
        自身.清理待选(会话工作区标识,工作区相位,待选工作区 is not None)#清 pending
        阶段=派生阶段(会话标识,作曲阶段,打开态,摘要空白)#相位
        英雄=阶段=='hero'#是否英雄
        区=None if 会话 is None or 输入态 is None else {'session':会话,'input':输入态}#InputZone
        芯片标题=待选工作区['title'] if 待选工作区 is not None and 'title' in 待选工作区 else None#优先待选
        if 芯片标题 is None and 会话标识 is not None:#非冷启动
            芯片标题=会话工作区['title'] if 会话工作区 is not None and 'title' in 会话工作区 else None#所属标题
            if 芯片标题 is None and 工作区相位!='ready' and 工作目录 is not None and 工作目录!='':#列表未就绪用 cwd
                芯片标题=工作区标签(工作目录)#桥接
        惰性=会话标识 is None or (英雄 is True and 芯片标题 is None)#无工作区
        阻断中=惰性 is False and 作曲阻断 is not None#阻断
        栏属主={'variant':'hero' if 英雄 is True else 'composer'}#变体
        if 惰性 is True:#无工作区触发
            栏属主.update({'disabled':True,'placeholder':翻译('placeholder.workspace'),'workspacePickerOpen':自身.选择器开,'onRequestWorkspace':自身.切换选择器})#惰性
        elif 阻断中 is True:#阻断
            栏属主.update({'blocked':作曲阻断,'placeholder':作曲阻断['reason'] if 'reason' in 作曲阻断 else None})#阻断原因
        elif 英雄 is True:#英雄占位
            栏属主['placeholder']=翻译('placeholder.hero')#英雄
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('对话列')#根
        自身.画面.classes(remove='对话英雄')
        if 英雄 is True:
            自身.画面.classes(add='对话英雄')
        def 要本地栈(结果):
            '链没有选中覆盖层时，画出英雄和输入栏。'
            if 结果 is None:#空
                return True#画
            if isinstance(结果,dict) and 'elected' in 结果 and 结果['elected'] is None:#回退可见
                return True#画
            return False#链已画出
        def 重画():
            '按工作区菜单重画会话根。'
            自身.画面.clear()#清空
            with 自身.画面:#根
                贴出失败(自身)
                渲染槽('conversation.session.header',{})#页眉自己画
                with 界面.column().classes('身'):#滚动
                    渲染槽('conversation.session',{})#会话体自己画
                    with 界面.column().classes('作曲席'):#席
                        链结果=渲染链('conversation.composer',{'interactions':未决,'session':会话},{'overlay':True})#链自己画
                        if 要本地栈(链结果) is False:#已有覆盖
                            return#停
                        if 英雄 is True:#英雄
                            with 界面.element('div').classes('英雄'):#鱼和标题
                                标=渲染槽('conversation.hero.brand.mark',{'size':34})
                                if 标 is None:
                                    鱼标({'size':34}).渲染()
                                with 界面.element('div').classes('标题组'):#标题和徽
                                    界面.label(翻译('hero.headline')).classes('英雄标题')
                                    界面.label(翻译('hero.preview')).classes('预览徽')
                            芯片文=芯片标题 if 芯片标题 is not None else 翻译('hero.chooseWorkspace')#芯片
                            def 点芯片():
                                '打开工作区菜单。'
                                自身.切换选择器()#翻
                                重画()#重画
                            with 界面.row().classes('工作区行'):#芯片行
                                芯片=界面.button(on_click=点芯片).props('flat no-caps').classes('工作区钮')
                                芯片.props('aria-label="'+翻译('hero.chooseWorkspace')+'"')
                                with 芯片:
                                    界面.label(芯片文).classes('工作区文')
                                选中标识=自身.待选工作区标识 if 自身.待选工作区标识 is not None else 会话工作区标识#选中
                                渲染槽('conversation.hero.workspace',{'open':自身.选择器开,'selectedId':选中标识,'onPick':自身.挑选工作区,'onClose':自身.关闭选择器})#选择器自己画
                                渲染槽('conversation.hero.agentPreset',{})#预设自己画
                        if 区 is not None:#停靠
                            渲染槽('conversation.input.dock',区)#停靠自己画
                        渲染槽('conversation.input.overlay',{})#覆盖
                        if 区 is not None:#左
                            渲染槽('conversation.input.left',区)#左自己画
                        栏结果=渲染槽('conversation.composer.bar',栏属主)#输入栏自己画
                        if 栏结果 is None:#没有输入栏
                            占位=栏属主['placeholder'] if 'placeholder' in 栏属主 and 栏属主['placeholder'] is not None else 翻译('placeholder.default')#占位
                            界面.label(占位)#占位
                        if 区 is not None:#右
                            渲染槽('conversation.input.right',区)#右自己画
                        if 英雄 is False and 区 is not None:#脚
                            渲染槽('conversation.composer.dock',区)#统计自己画
        重画()#画

    def __call__(自身,属性=None):
        '对齐 React'
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
