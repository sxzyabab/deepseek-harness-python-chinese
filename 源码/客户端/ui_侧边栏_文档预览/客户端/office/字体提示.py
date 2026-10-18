'缺字体提示与非模态详情面板，绑定同一源版本'

__all__=['字体提示','字体提示条','处理字体提示条','字体动作','处理字体动作']

def 字体提示(属性):
    '展示缺字体；关闭仅对本源版本在本组件仍挂载期间生效'
    字体=属性.get('fonts') or []
    if len(字体)==0:
        return None
    翻译=属性['t']
    return {
        'kind':'font-notice',
        'message':翻译('missingFonts',{'fonts':', '.join(字体)}),
        'title':翻译('missingFontsTitle'),
        'description':翻译('missingFontsDescription'),
        'count':翻译('missingFontsCount',{'count':len(字体)}),
        'fonts':list(字体),
        'showMore':翻译('showMore'),
        'dismiss':翻译('dismissNotice'),
        'closeDetails':翻译('closeDetails'),
    }


def 处理字体提示条(window,属性):
    '无缺字体或已对本版本关闭时不画。有 parent 就挂上去'
    文档=window.document
    组件=属性['组件'] if '组件' in 属性 else None
    模型=字体提示(属性)
    if 模型 is None:
        return None
    版本=属性.get('sourceVersion')
    if 组件 is not None and 组件.已关版本==版本:
        return None
    行=文档.createElement('div')
    行.className='font-notice'
    行.setAttribute('role','status')
    讯=文档.createElement('span')
    讯.textContent=模型['message']
    行.appendChild(讯)
    详情=文档.createElement('div')
    详情.className='font-details'
    开着=组件.详情开 if 组件 is not None else False
    详情.hidden=not 开着
    def 切换详情(事件):
        '打开或收起字体名单'
        if 组件 is not None:
            组件.详情开=not 组件.详情开
            详情.hidden=not 组件.详情开
    def 关闭(事件):
        '只隐藏当前源版本'
        if 组件 is not None:
            组件.已关版本=版本
            组件.详情开=False
        行.hidden=True
        详情.hidden=True
    更多=文档.createElement('button')
    更多.type='button'
    更多.textContent=模型['showMore']
    更多.addEventListener('click',切换详情)
    关掉=文档.createElement('button')
    关掉.type='button'
    关掉.textContent=模型['dismiss']
    关掉.addEventListener('click',关闭)
    行.appendChild(更多)
    行.appendChild(关掉)
    题=文档.createElement('div')
    题.textContent=模型['title']
    述=文档.createElement('div')
    述.textContent=模型['description']
    数=文档.createElement('div')
    数.textContent=模型['count']
    详情.appendChild(题)
    详情.appendChild(述)
    详情.appendChild(数)
    for 名 in 模型['fonts']:
        一项=文档.createElement('div')
        一项.textContent=名
        详情.appendChild(一项)
    收=文档.createElement('button')
    收.type='button'
    收.textContent=模型['closeDetails']
    收.addEventListener('click',切换详情)
    详情.appendChild(收)
    壳=文档.createElement('div')
    壳.appendChild(行)
    壳.appendChild(详情)
    if 'parent' in 属性:
        属性['parent'].appendChild(壳)
    return 壳


class 字体提示条:
    '缺字体横幅与详情；关闭只在本组件仍挂载时生效'

    def __init__(自身,属性):
        '记下 props 与已关闭的源版本。构造不画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.已关版本=None
        自身.详情开=False
        自身.根=None

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '拆掉旧条，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 'window' not in 自身.属性:
            自身.根=None
            return None
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理字体提示条(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()


def _动作键齐(属性):
    '内容和页签、存储、文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 'useTabInfo' in 属性 and 'useStore' in 属性 and 't' in 属性

def 处理字体动作(window,属性):
    '修订未完成时不画。有 parent 就挂上去'
    if '组件' not in 属性:
        return None
    组件=属性['组件']
    内容=属性['content'] if 'content' in 属性 else None
    取标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None
    取存储=属性['useStore'] if 'useStore' in 属性 else None
    翻译=属性['t'] if 't' in 属性 else None
    if not isinstance(内容,dict) or 内容.get('kind')!='renderer' or 取标签 is None or 取存储 is None or 翻译 is None:
        return None
    信息=取标签()
    签=信息['tab'] if isinstance(信息,dict) else 信息.tab
    标签标识=签['id'] if isinstance(签,dict) else 签.id
    def 选(状态):
        '本标签持有的转换结果'
        表=状态['byTab'] if isinstance(状态,dict) and 'byTab' in 状态 else {}
        return 表[标签标识] if 标签标识 in 表 else None
    持有=取存储(选)
    if 持有 is None or 持有.get('revision')!=内容.get('revision') or 'file' not in 持有:
        return None
    文件=持有['file']
    if 组件.条 is None:
        组件.条=字体提示条({})
    组件.条.属性={
        'fonts':文件.get('missingFonts',[]),
        'sourceVersion':文件.get('version'),
        't':翻译,
        'window':window,
    }
    根=组件.条.渲染()
    if 根 is not None and 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根


class 字体动作:
    '工具条上只展示当前修订的缺字体'

    def __init__(自身,属性):
        '记下动作席 props。有 window 且键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.条=None
        自身.根=None
        if _动作键齐(自身.属性) and 'window' in 自身.属性:
            自身.渲染()

    def 渲染(自身):
        '拆掉旧动作，再画一次'
        if 自身.根 is not None and (自身.条 is None or 自身.根 is not 自身.条.根):
            自身.根.remove()
        自身.根=None
        if 'window' not in 自身.属性:
            return None
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理字体动作(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None):
        '有新属性先更新，再画出'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
            自身.条=None
        return 自身.渲染()
