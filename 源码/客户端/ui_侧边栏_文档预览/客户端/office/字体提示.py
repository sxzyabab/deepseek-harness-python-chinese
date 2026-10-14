'缺字体提示与非模态详情面板，绑定同一源版本'
from nicegui import ui as 界面

__all__=['字体提示','字体提示条','字体动作']

def 字体提示(属性):
    '展示缺字体；关闭仅对本源版本在本组件仍挂载期间生效'
    字体=属性.get('fonts') or []#缺字体列表
    if len(字体)==0:#齐备
        return None#无
    翻译=属性['t']#翻译
    return {#提示结构
        'kind':'font-notice',
        'message':翻译('missingFonts',{'fonts':', '.join(字体)}),
        'title':翻译('missingFontsTitle'),
        'description':翻译('missingFontsDescription'),
        'count':翻译('missingFontsCount',{'count':len(字体)}),
        'fonts':list(字体),
        'showMore':翻译('showMore'),
        'dismiss':翻译('dismissNotice'),
        'closeDetails':翻译('closeDetails'),
    }#结束


class 字体提示条:
    '缺字体横幅与详情；关闭只在本组件仍挂载时生效'

    def __init__(自身,属性):
        '记下 props 与已关闭的源版本'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已关版本=None
        自身.详情开=False

    def 渲染(自身):
        '无缺字体或已对本版本关闭时不画'
        模型=字体提示(自身.属性)
        if 模型 is None:
            return
        版本=自身.属性.get('sourceVersion')
        if 自身.已关版本==版本:
            return
        def 关闭():
            '只隐藏当前源版本'
            自身.已关版本=版本
            自身.详情开=False
        def 切换详情():
            '打开或收起字体名单'
            自身.详情开=not 自身.详情开
        with 界面.row().classes('font-notice').props('role=status'):
            界面.label(模型['message'])
            界面.button(模型['showMore'], on_click=切换详情).props('flat dense no-caps')
            界面.button(模型['dismiss'], on_click=关闭).props('flat dense no-caps')
        if 自身.详情开:
            with 界面.column().classes('font-details'):
                界面.label(模型['title'])
                界面.label(模型['description'])
                界面.label(模型['count'])
                for 名 in 模型['fonts']:
                    界面.label(名)
                界面.button(模型['closeDetails'], on_click=切换详情).props('flat dense no-caps')

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()


class 字体动作:
    '工具条上只展示当前修订的缺字体'

    def __init__(自身,属性):
        '记下动作席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.条=None
        if isinstance(自身.属性,dict) and 'content' in 自身.属性 and 'useTabInfo' in 自身.属性 and 'useStore' in 自身.属性 and 't' in 自身.属性:
            自身.渲染()

    def 渲染(自身):
        '修订未完成时不画'
        属性=自身.属性
        内容=属性['content'] if 'content' in 属性 else None
        取标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None
        取存储=属性['useStore'] if 'useStore' in 属性 else None
        翻译=属性['t'] if 't' in 属性 else None
        if not isinstance(内容,dict) or 内容.get('kind')!='renderer' or 取标签 is None or 取存储 is None or 翻译 is None:
            return
        信息=取标签()
        签=信息['tab'] if isinstance(信息,dict) else 信息.tab
        标签标识=签['id'] if isinstance(签,dict) else 签.id
        def 选(状态):
            '本标签持有的转换结果'
            表=状态['byTab'] if isinstance(状态,dict) and 'byTab' in 状态 else {}
            return 表[标签标识] if 标签标识 in 表 else None
        持有=取存储(选)
        if 持有 is None or 持有.get('revision')!=内容.get('revision') or 'file' not in 持有:
            return
        文件=持有['file']
        if 自身.条 is None:
            自身.条=字体提示条({})
        自身.条.属性={
            'fonts':文件.get('missingFonts',[]),
            'sourceVersion':文件.get('version'),
            't':翻译,
        }
        自身.条.渲染()

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
            自身.条=None
        return 自身.渲染()
