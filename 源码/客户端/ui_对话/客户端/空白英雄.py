from nicegui import ui as 界面
from .文案 import 中文 as 对话文案
from ..异常 import 页面失败文案,贴出失败
from ....基础设施.通用工具 import 路径转正斜杠

样式已登记=False

def 确保辉光样式():
    '同一段辉光样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css('.英雄辉光条{height:48px;background:#6187D8;opacity:0.08}')
    样式已登记=True

__all__=['工作区标签','工作区芯片','英雄辉光','英雄壳']#仅中文公开名

def 恒等翻译(键,参数=None):
    '无文案表时返回键本身'
    return 键#键即文案

def 工作区标签(工作目录):
    '分隔符-only 路径回显原 cwd'
    if 工作目录 is None or 工作目录=='':#空
        return 工作目录#原样
    段=路径转正斜杠(工作目录).rstrip('/').split('/')#分段
    基=段[-1] if len(段)>0 else ''#末段
    return 基 if 基!='' else 工作目录#空则原路径

class 工作区芯片:
    '无标签时占位「选择工作区」'

    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '画出可点的工作区芯片。'
        属性=自身.属性#props
        原译=属性['t'] if 't' in 属性 and 属性['t'] is not None else None#宿主文案
        def 翻译(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        标签=属性['label'] if 'label' in 属性 else None#标签
        点击=属性['onClick'] if 'onClick' in 属性 else None#点击
        文案=标签 if 标签 is not None else 翻译('hero.chooseWorkspace')#文案
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.row().classes('workspace')#芯片
        自身.画面.clear()#清空
        with 自身.画面:#芯片
            贴出失败(自身)
            def 点芯片():
                '打开工作区菜单。'
                if 点击 is not None:#有
                    点击()#点
            界面.button(文案,on_click=点芯片)#芯片

class 英雄辉光:
    '属主 className 供位；滤镜 id 防碰撞'

    def __init__(自身,类名=None,滤镜标识=None):
        '记下定位类与滤镜 id'
        自身.类名=类名#定位
        自身.滤镜标识=滤镜标识 if 滤镜标识 not in (None,'') else 'empty-glow'#滤镜
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 渲染(自身):
        '画出淡色辉光条。'
        if 自身.类名 is None or 自身.类名=='':#无定位类
            类名='英雄辉光'#默认
        else:#有
            类名=自身.类名#定位
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.element('div').classes(类名)#辉光
        自身.画面.clear()#清空
        确保辉光样式()
        自身.画面.classes(add='英雄辉光条')
        with 自身.画面:
            贴出失败(自身)

class 英雄壳:
    '无辉光、无 composer、无工作区行'

    def __init__(自身,属性=None):
        '记下合成 props'
        自身.属性=属性 if 属性 is not None else {}#合成
        自身.画面=None#可反复清空的画面
        自身.渲染()#槽位只调用构造，这里就要画

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性 if 属性 is not None else {}#新

    def 渲染(自身):
        '画出标题、预览徽和覆盖层。'
        属性=自身.属性#props
        原译=属性['t'] if 't' in 属性 and 属性['t'] is not None else None#宿主文案
        def 翻译(键,参数=None):
            '属性上的 t 优先，否则用本包中文词典。'
            if 原译 is not None:#宿主
                if 参数 is None:#无参数
                    return 原译(键)#译
                return 原译(键,参数)#带参数
            if 键 not in 对话文案:#词典没有
                return 键#键
            文本=对话文案[键]#词条
            if 参数 is None:#无参数
                return 文本#原文
            for 名 in 参数:#替换占位
                文本=文本.replace('{'+名+'}',str(参数[名]))#替换
            return 文本#译完
        子=属性['children'] if 'children' in 属性 else None#覆盖层
        自身.画面失败=None
        if 自身.画面 is not None:
            try:
                自身.画面.clear()
            except Exception as 错误:
                自身.画面=None
                自身.画面失败=页面失败文案(错误)
        if 自身.画面 is None:#新建
            自身.画面=界面.column().classes('root')#壳
        自身.画面.clear()#清空
        with 自身.画面:#壳
            贴出失败(自身)
            with 界面.row().classes('headline'):#标题行
                界面.label(翻译('hero.headline')).classes('英雄标题')#标题
                界面.label(翻译('hero.preview')).classes('英雄徽')#预览徽
            界面.column().classes('body')#正文位
            if 子 is not None and hasattr(子,'渲染'):#子组件自己画
                子.渲染()#画
