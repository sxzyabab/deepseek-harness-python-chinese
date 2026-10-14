from nicegui import ui as 界面
from .终端卡模型 import 终端块文案
from ...ui_基础界面组件.状态点 import 状态点
from ...ui_基础界面组件.终端块 import 终端块
from ...ui_基础界面组件.差异块 import 差异块
from ...ui_基础界面组件.读块 import 读块
from ...ui_基础界面组件.检索块 import 检索块
from ...ui_基础界面组件.网页块 import 网页块
from .工具详情 import 画详情模型

__all__=['工具行','前导态','状态文案']

样式已登记=False

样式表='''
.视隐{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.行罩{position:absolute;inset:0}
'''

def 登记样式():
    '工具行里重复用到的样式，整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表,shared=True)
    样式已登记=True

登记样式()

def 前导态(状态,图标):
    '错误或中止画状态点，其余画工具图标'
    if 状态=='error':
        状态点({'state':'error','size':14}).渲染()
        return
    if 状态=='stopped':
        状态点({'state':'warning','size':14}).渲染()
        return
    if isinstance(图标,str) and 图标!='':
        界面.icon(图标)

def 状态文案(状态,翻译):
    'ok 态为 None；其余给辅助技术'
    if 状态=='running':
        return 翻译('row.running') if callable(翻译) else 'row.running'
    if 状态=='error':
        return 翻译('row.failed') if callable(翻译) else 'row.failed'
    if 状态=='stopped':
        return 翻译('row.stopped') if callable(翻译) else 'row.stopped'
    return None

class 工具行:
    '渲染一行工具调用摘要与可选展开体。父组件调用渲染，构造本身不画'

    def __init__(自身,属性=None):
        '记下合成 props 与本地展开'
        自身.属性={} if 属性 is None else 属性
        自身.已展开=False

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性

    def 切换展开(自身):
        '有体、输出或卡片才可展开'
        if not 自身.可展开():
            return
        自身.已展开=not 自身.已展开

    def 可展开(自身):
        '有 body、output 或卡片材料则可展开'
        属性=自身.属性
        卡=(
            ('terminal' in 属性 and 属性['terminal'] is not None)
            or ('diff' in 属性 and 属性['diff'] is not None)
            or ('read' in 属性 and 属性['read'] is not None)
            or ('search' in 属性 and 属性['search'] is not None)
            or ('web' in 属性 and 属性['web'] is not None)
            or ('details' in 属性 and 属性['details'] is not None)
        )
        return ('body' in 属性 and 属性['body'] is not None) or ('output' in 属性 and 属性['output'] is not None) or 卡

    def 建展开体(自身):
        '卡片优先；否则代码程序与输入输出'
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 else None
        变体=属性['variant'] if 'variant' in 属性 else None
        体=属性['body'] if 'body' in 属性 else None
        出=属性['output'] if 'output' in 属性 else None
        终端=属性['terminal'] if 'terminal' in 属性 else None
        差异=属性['diff'] if 'diff' in 属性 else None
        读=属性['read'] if 'read' in 属性 else None
        检索=属性['search'] if 'search' in 属性 else None
        网页=属性['web'] if 'web' in 属性 else None
        详情=属性['details'] if 'details' in 属性 else None
        开文件=属性['onOpenFile'] if 'onOpenFile' in 属性 else None
        def 画文本(值):
            '字符串或卡片里的可读字段'
            if isinstance(值,str):
                if 值!='':
                    界面.label(值)
                return
            if not isinstance(值,dict):
                return
            for 键 in ('title','text','description','content','command','path','output'):
                if 键 in 值 and isinstance(值[键],str) and 值[键]!='':
                    界面.label(值[键])
        if 终端 is not None:
            if 'description' in 终端 and isinstance(终端['description'],str) and 终端['description']!='':
                界面.label(终端['description'])
            卡=终端['card'] if 'card' in 终端 and isinstance(终端['card'],dict) else {}
            载荷=dict(卡)
            if callable(翻译):
                载荷['labels']=终端块文案(翻译)
            终端块(载荷).渲染()
            return
        if 差异 is not None:
            卡=差异['card'] if 'card' in 差异 and isinstance(差异['card'],dict) else {}
            差异块(卡).渲染()
            return
        if 读 is not None:
            读块(读 if isinstance(读,dict) else {}).渲染()
            return
        if 检索 is not None:
            卡=检索['card'] if 'card' in 检索 and isinstance(检索['card'],dict) else {}
            检索块(卡).渲染()
            恢复=检索['recovery'] if isinstance(检索,dict) and 'recovery' in 检索 else None
            if isinstance(恢复,str) and 恢复!='':
                界面.label(恢复)
            return
        if 网页 is not None:
            网页块(网页 if isinstance(网页,dict) else {}).渲染()
            return
        if 画详情模型(详情,翻译,开文件):
            return
        if 变体=='code' and isinstance(体,str) and 体!='':
            界面.code(体, language='typescript')
            复制文=翻译('copy') if callable(翻译) else 'copy'
            def 复制():
                '复制程序'
                界面.clipboard.write(体)
            界面.button(复制文, on_click=复制)
        卡体=None if 变体=='code' else 体
        if 卡体 is not None or 出 is not None:
            with 界面.column().classes('进出卡'):
                if 卡体 is not None:
                    with 界面.element('div').classes('进出节'):
                        界面.label('IN').classes('进出标')
                        with 界面.column().classes('进出文'):
                            画文本(卡体)
                if 卡体 is not None and 出 is not None:
                    界面.element('div').classes('进出线')
                if 出 is not None:
                    with 界面.element('div').classes('进出节'):
                        界面.label('OUT').classes('进出标')
                        with 界面.column().classes('进出文'):
                            画文本(出)

    def 渲染(自身):
        '画出工具摘要行'
        登记样式()
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 else None
        状态=属性['state'] if 'state' in 属性 and 属性['state'] else 'ok'
        失败行=属性['errorSummary'] if 状态=='error' and 'errorSummary' in 属性 else None
        摘要=失败行 if 失败行 is not None else (属性['summary'] if 'summary' in 属性 else None)
        后缀=None if 失败行 is not None else (属性['summarySuffix'] if 'summarySuffix' in 属性 else None)
        路径=属性['filePath'] if 'filePath' in 属性 else None
        开文件=属性['onOpenFile'] if 'onOpenFile' in 属性 else None
        文件链=路径 is not None and callable(开文件) and 失败行 is None
        打开=自身.已展开 and 自身.可展开()
        检查=属性['inspect'] if 'inspect' in 属性 else None
        图标=属性['icon'] if 'icon' in 属性 else None
        标题=属性['title'] if 'title' in 属性 else None
        with 界面.column().classes('工具调用'):
            with 界面.row().classes('工具行头'):
                前导态(状态,图标)
                if isinstance(标题,str) and 标题!='':
                    界面.label(标题).classes('题')
                if 文件链:
                    def 点文件(路=路径):
                        '打开文件'
                        开文件(路)
                    界面.element('span').classes('点')
                    界面.button(str(路径), on_click=点文件).props('flat no-caps').classes('文件链')
                elif isinstance(摘要,str) and 摘要!='':
                    界面.element('span').classes('点')
                    摘要类='要'
                    if 状态=='error':
                        摘要类='要 要错'
                    elif 状态=='stopped':
                        摘要类='要 要止'
                    界面.label(摘要).classes(摘要类)
                if isinstance(后缀,str) and 后缀!='':
                    界面.label(后缀).classes('要尾')
                状态文=状态文案(状态,翻译)
                if isinstance(状态文,str) and 状态文!='':
                    界面.label(状态文).classes('视隐')
                if 自身.可展开():
                    def 点行():
                        '整行切换展开'
                        自身.切换展开()
                    界面.element('div').on('click', 点行).classes('行罩')
            if 打开:
                自身.建展开体()
                if callable(检查):
                    检视文=翻译('inspect') if callable(翻译) else 'inspect'
                    界面.button(检视文, on_click=检查).props('flat no-caps').classes('检视')

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
