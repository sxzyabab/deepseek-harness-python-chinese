from nicegui import ui as 界面
from .差异卡模型 import 差异卡模型
from .读卡模型 import 读卡模型
from .检索卡模型 import 检索卡模型
from .终端卡模型 import 终端卡模型,终端块文案
from .网页卡模型 import 网页卡模型
from .调用模型 import 结果文本
from .详情卡片模型 import 详情卡片模型
from ...ui_基础界面组件.终端块 import 终端块
from ...ui_基础界面组件.差异块 import 差异块
from ...ui_基础界面组件.读块 import 读块
from ...ui_基础界面组件.检索块 import 检索块
from ...ui_基础界面组件.网页块 import 网页块

__all__=['工具详情','画详情条目','画详情模型']

def 缺省翻译(键,_插值=None):
    '原样返回键'
    return 键

def 画详情条目(项,开文件):
    '标题、字段、行、代码与分组'
    if not isinstance(项,dict):
        return
    with 界面.column().classes('详情条目'):
        标题=项['title'] if 'title' in 项 else None
        位置=项['location'] if 'location' in 项 and isinstance(项['location'],dict) else None
        if isinstance(标题,str) and 标题!='':
            if 位置 is not None and callable(开文件) and 'path' in 位置:
                路径=位置['path']
                行号=位置['line'] if 'line' in 位置 else None
                def 点(路=路径,行=行号):
                    '打开记录位置'
                    if 行 is None:
                        开文件(路)
                    else:
                        开文件(路,{'line':行})
                界面.button(标题,on_click=点).props('flat no-caps').classes('详情路径')
            else:
                界面.label(标题).classes('详情题')
        徽=项['badge'] if 'badge' in 项 and isinstance(项['badge'],dict) else None
        if 徽 is not None and 'label' in 徽 and 徽['label'] is not None:
            界面.label(str(徽['label'])).classes('详情徽')
        态=项['status'] if 'status' in 项 and isinstance(项['status'],dict) else None
        if 态 is not None and 'label' in 态:
            前文=项['previousStatus'] if 'previousStatus' in 项 else None
            if isinstance(前文,str) and 前文!='':
                界面.label(前文+' → '+str(态['label']))
            else:
                界面.label(str(态['label']))
        副=项['subtitle'] if 'subtitle' in 项 else None
        if isinstance(副,str) and 副!='':
            界面.label(副)
        述=项['description'] if 'description' in 项 else None
        if isinstance(述,str) and 述!='':
            界面.label(述)
        字段=项['fields'] if 'fields' in 项 and isinstance(项['fields'],list) else []
        for 栏 in 字段:
            if isinstance(栏,dict):
                名=栏['label'] if 'label' in 栏 else ''
                值=栏['value'] if 'value' in 栏 else ''
                界面.label(str(名)+': '+str(值))
        行列表=项['lines'] if 'lines' in 项 and isinstance(项['lines'],list) else None
        if 行列表 is not None:
            for 线 in 行列表:
                界面.label(str(线))
        代码=项['code'] if 'code' in 项 and isinstance(项['code'],dict) else None
        if 代码 is not None and 'text' in 代码 and isinstance(代码['text'],str):
            语言=代码['language'] if 'language' in 代码 and isinstance(代码['language'],str) and 代码['language']!='' else 'text'
            界面.code(代码['text'],language=语言)
        标记=项['markdown'] if 'markdown' in 项 else None
        if isinstance(标记,str) and 标记!='':
            界面.markdown(标记)
        组列表=项['groups'] if 'groups' in 项 and isinstance(项['groups'],list) else []
        for 组 in 组列表:
            if not isinstance(组,dict):
                continue
            组标=组['label'] if 'label' in 组 and isinstance(组['label'],str) else ''
            with 界面.expansion(组标).classes('详情组'):
                子项=组['items'] if 'items' in 组 and isinstance(组['items'],list) else []
                for 子 in 子项:
                    画详情条目(子,开文件)

def 画详情模型(模型,翻译,开文件):
    '有 items 才画；否则交给调用方继续'
    if not isinstance(模型,dict) or 'items' not in 模型 or not isinstance(模型['items'],list):
        return False
    条目=模型['items']
    with 界面.column().classes('tool-details'):
        题=模型['caption'] if 'caption' in 模型 else None
        if isinstance(题,str) and 题!='':
            界面.label(题)
        摘要=模型['summary'] if 'summary' in 模型 else None
        if isinstance(摘要,str) and 摘要!='':
            界面.label(摘要)
        if len(条目)==0:
            空=模型['empty'] if 'empty' in 模型 else None
            if isinstance(空,str) and 空!='':
                界面.label(空)
        else:
            for 项 in 条目:
                画详情条目(项,开文件)
        未变=模型['unchanged'] if 'unchanged' in 模型 else None
        if isinstance(未变,dict):
            标=未变['label'] if 'label' in 未变 and isinstance(未变['label'],str) else ''
            with 界面.expansion(标).classes('详情未变'):
                子项=未变['items'] if 'items' in 未变 and isinstance(未变['items'],list) else []
                for 项 in 子项:
                    画详情条目(项,开文件)
    return True

class 工具详情:
    '已知呈现意图走对应块；否则展平文本。调用方负责渲染，构造本身不画'

    def __init__(自身,属性):
        '记下 props。不再挂独立槽，避免和工具卡各画一遍'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 取块(自身):
        'block 优先；否则 selection.block'
        属性=自身.属性
        if 'block' in 属性 and isinstance(属性['block'],dict):
            return 属性['block']
        选=属性['selection'] if 'selection' in 属性 and isinstance(属性['selection'],dict) else None
        if 选 is not None and 'block' in 选 and isinstance(选['block'],dict):
            return 选['block']
        return None

    def 渲染(自身):
        '按意图画出详情'
        属性=自身.属性
        翻译=属性['t'] if 't' in 属性 and callable(属性['t']) else 缺省翻译
        开文件=属性['openFile'] if 'openFile' in 属性 else None
        if 开文件 is None and 'onOpenFile' in 属性:
            开文件=属性['onOpenFile']
        块=自身.取块()
        if 块 is None:
            选=属性['selection'] if 'selection' in 属性 and isinstance(属性['selection'],dict) else None
            with 界面.column().classes('tool-details'):
                if 选 is None:
                    界面.label(翻译('details.empty'))
                    return
                名=选['toolName'] if 'toolName' in 选 else None
                if isinstance(名,str) and 名!='':
                    界面.label(名)
                标识=选['callId'] if 'callId' in 选 else None
                if 标识 is not None:
                    界面.label(str(标识))
            return
        工作目录=属性['cwd'] if 'cwd' in 属性 else None
        终端=终端卡模型(块,工作目录)
        if 终端 is not None:
            with 界面.column().classes('tool-details'):
                if 'description' in 终端 and isinstance(终端['description'],str) and 终端['description']!='':
                    界面.label(终端['description'])
                卡=终端['card'] if 'card' in 终端 and isinstance(终端['card'],dict) else {}
                载荷=dict(卡)
                载荷['labels']=终端块文案(翻译)
                终端块(载荷).渲染()
            return
        读=读卡模型(块,工作目录)
        if 读 is not None:
            with 界面.column().classes('tool-details'):
                读块(读).渲染()
            return
        差异=差异卡模型(块)
        if 差异 is not None:
            with 界面.column().classes('tool-details'):
                卡=差异['card'] if 'card' in 差异 and isinstance(差异['card'],dict) else {}
                差异块(卡).渲染()
            return
        检索=检索卡模型(块)
        if 检索 is not None:
            with 界面.column().classes('tool-details'):
                卡=检索['card'] if 'card' in 检索 and isinstance(检索['card'],dict) else {}
                检索块(卡).渲染()
                恢复=检索['recovery'] if 'recovery' in 检索 else None
                if isinstance(恢复,str) and 恢复!='':
                    界面.label(恢复)
            return
        网页=网页卡模型(块)
        if 网页 is not None:
            正文=结果文本(块) if 'kind' in 块 else ''
            with 界面.column().classes('tool-details'):
                网页块(网页).渲染()
                if isinstance(正文,str) and 正文!='':
                    界面.label(正文)
            return
        语言=属性['locale'] if 'locale' in 属性 and isinstance(属性['locale'],str) else 'zh'
        详情=详情卡片模型(块,翻译,语言)
        if 画详情模型(详情,翻译,开文件):
            return
        if 'kind' not in 块:
            界面.label(翻译('details.running'))
            return
        文本=结果文本(块)
        if isinstance(文本,str) and 文本!='':
            界面.code(文本)

    def __call__(自身,属性=None):
        '有新属性则刷新后渲染'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
