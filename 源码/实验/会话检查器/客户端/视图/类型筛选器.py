'锚定的类型筛选编辑器，候选异步出现，并且必须显式确认'

from .....基础设施.js特性 import PromiseEX as 期约#过期响应不能盖住更新的候选
from .....客户端.ui_基础界面组件.锚定位置 import 锚定位置
from .聊天节点.文档对象 import 矩形字典

__all__=['类型筛选器']

class 类型筛选器:
    '编辑类型片段；Enter、确认或选中候选之前不筛选'
    def __init__(自身,属性):
        '记下已确认查询、候选函数和提交回调'
        自身.属性=属性
        自身.打开=False
        自身.草稿=属性.get('value') or ''
        自身.活动=-1
        自身.结果=None
        自身.锚=None
        自身.面板=None
        自身.输入=None
        自身.标识=f'type-filter-{id(自身)}'
        自身._代=0
        自身._开着监听=False
        自身._已聚焦=False
        自身._候选键=None

    def 更新(自身,属性):
        '刷新 props'
        自身.属性=属性

    def 关闭(自身,恢复焦点):
        '关掉编辑器，需要时把焦点还回按钮'
        自身.打开=False
        自身._确保监听()
        if 恢复焦点 and 自身.锚 is not None:
            自身.锚.focus({'preventScroll':True})

    def 提交(自身,查询):
        '确认查询并关闭'
        自身.属性['apply'](查询)
        自身.关闭(True)

    def _外面(自身,事件):
        '点到面板和按钮之外则放弃'
        目标=事件.target
        在面板=自身.面板 is not None and 自身.面板.contains(目标)
        在锚=自身.锚 is not None and 自身.锚.contains(目标)
        if not 在面板 and not 在锚:
            自身.关闭(False)

    def _失焦窗(自身,事件=None):
        '窗口失焦则放弃'
        自身.关闭(False)

    def _刷新候选(自身):
        '打开期间按草稿要候选；代次挡住过期响应'
        if not 自身.打开:
            return
        代=自身._代+1
        自身._代=代
        自身.结果=None
        自身.活动=-1
        草稿=自身.草稿
        def 成功(项):
            '仍是这一代才写入候选'
            if 代==自身._代:
                自身.结果={'query':草稿,'items':list(项)}
            return None
        def 失败(错误):
            '仍是这一代才写入错误'
            if 代==自身._代:
                自身.结果={'query':草稿,'items':[],'error':str(错误)}
            return None
        def 去建议(值=None):
            '调用候选函数，返回期约'
            return 自身.属性['suggest'](草稿)
        起点=期约()
        起点.然后(去建议).然后(成功,失败)
        起点.解决(None)

    def _同步候选(自身):
        '打开且草稿或候选函数变了才重新请求'
        if not 自身.打开:
            自身._候选键=None
            return
        键=(自身.草稿,自身.属性.get('suggest'))
        if 自身._候选键==键:
            return
        自身._候选键=键
        自身._刷新候选()

    def _确保监听(自身):
        '打开时聚焦输入并监听外部点击；关掉时卸下'
        if 自身.打开 and not 自身._开着监听:
            window.addEventListener('pointerdown',自身._外面,True)
            window.addEventListener('blur',自身._失焦窗)
            自身._开着监听=True
        if 自身.打开 and 自身.输入 is not None and not 自身._已聚焦:
            自身.输入.focus({'preventScroll':True})
            自身.输入.select()
            自身._已聚焦=True
        if not 自身.打开 and 自身._开着监听:
            window.removeEventListener('pointerdown',自身._外面,True)
            window.removeEventListener('blur',自身._失焦窗)
            自身._开着监听=False
        if not 自身.打开:
            自身._已聚焦=False
        自身._同步候选()

    def _点按钮(自身):
        '再点一次关闭；否则用已确认值打开'
        if 自身.打开:
            自身.关闭(True)
            return
        自身.草稿=自身.属性.get('value') or ''
        自身.结果=None
        自身.活动=-1
        自身.打开=True
        自身._确保监听()

    def _改草稿(自身,事件):
        '改草稿并清掉键盘选中'
        自身.草稿=事件.currentTarget.value
        自身.活动=-1
        自身._同步候选()

    def _输入键(自身,事件):
        '方向键移动候选，Enter 确认选中项或草稿'
        原生=getattr(事件,'nativeEvent',事件)
        if getattr(原生,'isComposing',False) or getattr(原生,'keyCode',None)==229:
            return
        项=自身._当前项()
        if 事件.key in ('ArrowDown','ArrowUp'):
            事件.preventDefault()
            if len(项)==0:
                自身.活动=-1
            elif 自身._选中()<0:
                自身.活动=0 if 事件.key=='ArrowDown' else len(项)-1
            else:
                步=1 if 事件.key=='ArrowDown' else -1
                自身.活动=(自身._选中()+步+len(项))%len(项)
        elif 事件.key=='Enter':
            事件.preventDefault()
            选=自身._选中()
            自身.提交(自身.草稿 if 选<0 or 选>=len(项) else 项[选])

    def _面板键(自身,事件):
        'Esc 放弃草稿'
        if 事件.key!='Escape':
            return
        事件.preventDefault()
        事件.stopPropagation()
        自身.关闭(True)

    def _面板失焦(自身,事件):
        '焦点离开面板和按钮则放弃'
        相关=getattr(事件,'relatedTarget',None)
        if not isinstance(相关,Node):
            return
        在面板=事件.currentTarget.contains(相关)
        在锚=自身.锚 is not None and 自身.锚.contains(相关)
        if not 在面板 and not 在锚:
            自身.关闭(False)

    def _当前项(自身):
        '结果查询和草稿一致时才用这批候选'
        if 自身.结果 is not None and 自身.结果.get('query')==自身.草稿:
            return list(自身.结果.get('items') or [])
        return []

    def _选中(自身):
        '越界的键盘下标当作没有选中'
        项=自身._当前项()
        if 0<=自身.活动<len(项):
            return 自身.活动
        return -1

    def _位置样式(自身):
        '量不到锚或面板时先藏起来'
        if not 自身.打开 or 自身.锚 is None or 自身.面板 is None:
            return {'left':0,'top':0,'visibility':'hidden'}
        锚矩形=矩形字典(自身.锚.getBoundingClientRect())
        面板矩形=矩形字典(自身.面板.getBoundingClientRect())
        return 锚定位置(锚矩形,面板矩形['width'],面板矩形['height'],window.innerWidth,window.innerHeight,间隙=4,边距=12)

    def 渲染(自身):
        '表头按钮和传送到 body 的编辑器'
        自身._确保监听()
        翻译=自身.属性['t']
        值=自身.属性.get('value') or ''
        项=自身._当前项()
        选=自身._选中()
        当前=自身.结果 if 自身.结果 is not None and 自身.结果.get('query')==自身.草稿 else None
        列表标识=f'{自身.标识}-types'
        按钮={
            'type':'button',
            'className':'typeFilterButton',
            'ref':自身._记锚,
            'aria-label':翻译('filter.title'),
            'title':翻译('filter.title') if 值=='' else f"{翻译('filter.title')}: *{值}*",
            'aria-haspopup':'dialog',
            'aria-expanded':自身.打开,
            'aria-pressed':值!='',
            'onClick':自身._点按钮,
            'icon':{'type':'svg','width':13,'height':13,'viewBox':'0 0 16 16','fill':'none','stroke':'currentColor','strokeWidth':1.3,'aria-hidden':True,'path':'M2 3h12L9.5 8v5l-3-1.5V8L2 3Z'},
        }
        面板=None
        if 自身.打开:
            选项=[]
            for 下标,类型 in enumerate(项):
                def 防止(事件,下标=下标):
                    '按下时别把焦点从输入框偷走'
                    事件.preventDefault()
                def 选这个(类型=类型):
                    '确认该候选'
                    自身.提交(类型)
                选项.append({
                    'type':'button',
                    'key':类型,
                    'id':f'{自身.标识}-option-{下标}',
                    'role':'option',
                    'aria-selected':选==下标,
                    'tabIndex':-1,
                    'title':类型,
                    'text':类型,
                    'onPointerDown':防止,
                    'onClick':选这个,
                })
            面板={
                'portal':True,
                'target':'body',
                'surface':'MenuSurface',
                'compact':True,
                'ref':自身._记面板,
                'className':'typeFilterPanel',
                'role':'dialog',
                'aria-label':翻译('filter.title'),
                'style':自身._位置样式(),
                'onKeyDown':自身._面板键,
                'onBlur':自身._面板失焦,
                'input':{
                    'ref':自身._记输入,
                    'className':'typeFilterInput',
                    'value':自身.草稿,
                    'role':'combobox',
                    'aria-label':翻译('filter.input'),
                    'aria-autocomplete':'list',
                    'aria-expanded':True,
                    'aria-controls':列表标识,
                    'aria-activedescendant':None if 选<0 else f'{自身.标识}-option-{选}',
                    'placeholder':翻译('filter.placeholder'),
                    'onChange':自身._改草稿,
                    'onKeyDown':自身._输入键,
                },
                'help':翻译('filter.help'),
                'list':{
                    'id':列表标识,
                    'role':'listbox',
                    'aria-label':翻译('filter.candidates'),
                    'aria-busy':当前 is None,
                    'className':'typeFilterOptions',
                    'options':选项,
                },
                'loading':None if 当前 is not None else 翻译('filter.loading'),
                'error':None if 当前 is None or 当前.get('error') is None else {'text':翻译('filter.failed'),'detail':当前.get('error')},
                'empty':翻译('filter.noCandidates') if 当前 is not None and 当前.get('error') is None and len(项)==0 else None,
                'actions':{
                    'clear':{'text':翻译('filter.clear'),'onClick':自身._清空},
                    'cancel':{'text':翻译('filter.cancel'),'onClick':lambda:自身.关闭(True)},
                    'apply':{'text':翻译('filter.apply'),'onClick':lambda:自身.提交(自身.草稿)},
                },
            }
        if 选>=0 and 自身.面板 is not None:
            选项元素=自身.面板.querySelectorAll('[role="option"]')
            if 选<len(选项元素):
                选项元素[选].scrollIntoView({'block':'nearest'})
        return {'button':按钮,'panel':面板,'cssModule':'检查器.module.css'}

    def _清空(自身):
        '清空草稿并聚焦输入'
        自身.草稿=''
        自身.活动=-1
        自身._同步候选()
        if 自身.输入 is not None:
            自身.输入.focus()

    def _记锚(自身,元素):
        '表头按钮'
        自身.锚=元素

    def _记面板(自身,元素):
        '传送层面板'
        自身.面板=元素

    def _记输入(自身,元素):
        '关键词输入'
        自身.输入=元素

    def __call__(自身,属性=None):
        '对齐 React 调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
