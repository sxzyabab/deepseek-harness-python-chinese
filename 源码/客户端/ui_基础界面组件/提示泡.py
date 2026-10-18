from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from .快捷键 import 快捷键
from .点外关闭 import 点外关闭
from .输入模态 import 指针模态

__all__=['提示泡','处理提示泡','侧表']

侧表=('right','bottom','top')
样式模块='tooltip'
边距=12

def 处理提示泡(window,属性):
    '挂上锚的悬停、焦点和可选点击钉住。延迟、方位和快捷键都从 props 来'
    文档=window.document
    注入模块样式文件(
        文档,
        '提示泡样式',
        os.path.join(os.path.dirname(__file__),'提示泡.module.css'),
        样式模块,
    )
    组件=属性.get('组件')
    侧=属性['side'] if 'side' in 属性 and 属性['side'] in 侧表 else 'right'
    对齐=属性['align'] if 'align' in 属性 else 'center'
    延迟=属性['delayMs'] if 'delayMs' in 属性 and 属性['delayMs'] is not None else 0
    焦点延迟=属性['focusDelayMs'] if 'focusDelayMs' in 属性 and 属性['focusDelayMs'] is not None else 0
    间隙=属性['gap'] if 'gap' in 属性 and 属性['gap'] is not None else 8
    禁用=属性.get('disabled') is True
    传送=属性.get('portal') is True
    点击打开=属性.get('openOnClick') is True
    最大宽=属性.get('maxWidth')
    快捷=属性['shortcutKeys'] if 'shortcutKeys' in 属性 and 属性['shortcutKeys'] is not None else []
    子=属性.get('children')
    触发={'hover':False,'focus':False}
    钉住=False
    定时=None
    泡=None
    拆外面=None
    def 取文():
        '可见时才解析文案。函数标签此时才调用'
        标签=属性.get('label')
        if callable(标签):
            文=标签()
        else:
            文=标签
        if 文 is None:
            return ''
        return str(文)
    def 取消显示():
        '清掉还没到点的显示'
        nonlocal 定时
        if 定时 is None:
            return
        window.clearTimeout(定时)
        定时=None
    def 藏泡():
        '从文档拿掉气泡'
        nonlocal 泡,拆外面,钉住
        取消显示()
        if 拆外面 is not None:
            拆外面()
            拆外面=None
        if 泡 is not None:
            泡.remove()
            泡=None
        钉住=False
        if 组件 is not None:
            组件.可见=False
    def 放置():
        '按锚的边和气泡尺寸夹进视口，放不下就上下对调'
        if 泡 is None or 锚 is None:
            return
        矩形=锚.getBoundingClientRect()
        宽=泡.offsetWidth if 泡.offsetWidth is not None else 0
        高=泡.offsetHeight if 泡.offsetHeight is not None else 0
        if 侧=='right':
            偏移=0
            左起点=矩形.right+10
        elif 对齐=='end':
            偏移=宽
            左起点=矩形.right
        else:
            偏移=宽/2
            左起点=矩形.left+矩形.width/2
        左=左起点-偏移
        if 左<边距:
            左=边距
        右限=window.innerWidth-边距-宽
        if 左>右限:
            左=右限
        放下=矩形.bottom+间隙+高<=window.innerHeight-边距
        放上=矩形.top-间隙-高>=边距
        实际=侧
        if 实际=='bottom' and 放下 is False and 放上 is True:
            实际='top'
        elif 实际=='top' and 放上 is False and 放下 is True:
            实际='bottom'
        if 实际=='right':
            顶=(矩形.top+矩形.bottom)/2
        elif 实际=='top':
            顶=矩形.top-间隙
        else:
            顶=矩形.bottom+间隙
        泡.style.left=str(左+偏移)+'px'
        泡.style.top=str(顶)+'px'
        泡.setAttribute('data-side',实际)
        泡.style.visibility='visible'
    def 显示():
        '量锚并挂上气泡'
        nonlocal 泡,拆外面
        if 禁用 or 锚 is None:
            return
        if 泡 is not None:
            泡.remove()
        文=取文()
        泡=文档.createElement('span')
        泡.className='bubble'
        标样式模块(泡,样式模块)
        泡.setAttribute('role','tooltip')
        泡.setAttribute('data-side',侧)
        泡.setAttribute('data-align',对齐)
        泡.style.visibility='hidden'
        if 传送:
            泡.setAttribute('data-portal','true')
        if 钉住:
            泡.setAttribute('data-pinned','true')
        if len(快捷)>0:
            泡.setAttribute('data-has-shortcut','true')
        if 最大宽 is not None:
            泡.style.maxWidth=str(最大宽)+'px'
        if 文!='':
            字=文档.createElement('span')
            字.className='label'
            标样式模块(字,样式模块)
            字.textContent=文
            泡.appendChild(字)
        if len(快捷)>0:
            名=[]
            if 文!='':
                名.append(文)
            名.append(' '.join([str(键) for 键 in 快捷]))
            泡.setAttribute('aria-label',' '.join(名))
            帽=快捷键({'window':window,'keys':快捷,'variant':'tooltip'}).渲染()
            if 帽 is not None:
                泡.appendChild(帽)
        if 传送:
            文档.body.appendChild(泡)
        else:
            锚.appendChild(泡)
        if 组件 is not None:
            组件.可见=True
            组件.放置=侧
        放置()
        构造=getattr(window,'ResizeObserver',None)
        if 构造 is not None:
            观察=构造(放置)
            观察.observe(泡)
            组件.观察=观察 if 组件 is not None else None
        window.addEventListener('resize',放置)
        if 点击打开:
            def 置关(开着):
                '点外面或按键关掉钉住的气泡'
                if 开着 is False:
                    藏泡()
            拆外面=点外关闭(锚,True,置关,泡)
    def 延迟显示(毫秒):
        '到点再显示。0 则立刻'
        nonlocal 定时
        取消显示()
        if 毫秒<=0:
            显示()
            return
        def 到点():
            '延迟结束'
            nonlocal 定时
            定时=None
            显示()
        定时=window.setTimeout(到点,毫秒)
    def 进入(事件):
        '指针进入，按 delayMs 显示'
        触发['hover']=True
        if 禁用:
            return
        延迟显示(延迟)
    def 离开(事件):
        '指针离开。没钉住就收起'
        触发['hover']=False
        取消显示()
        if 钉住 is False:
            藏泡()
    def 点下(事件):
        '普通点击收起。openOnClick 时第一次点击钉住'
        nonlocal 钉住
        触发['focus']=False
        取消显示()
        if 点击打开 and 禁用 is False and 钉住 is False:
            钉住=True
            显示()
            return
        藏泡()
    def 聚焦(事件):
        '键盘焦点按 focusDelayMs 显示。指针造成的焦点不显示'
        if 指针模态():
            return
        触发['focus']=True
        if 禁用:
            return
        延迟显示(焦点延迟)
    def 失焦(事件):
        '焦点离开。悬停和钉住都没了才收起'
        触发['focus']=False
        取消显示()
        if 触发['hover'] is False and 钉住 is False:
            藏泡()
    def 按键(事件):
        '钉住时 Escape 或 Tab 收起'
        if 点击打开 is False or 泡 is None:
            return
        if 事件.key!='Escape' and 事件.key!='Tab':
            return
        if 事件.key=='Escape':
            事件.preventDefault()
            事件.stopPropagation()
        藏泡()
    if hasattr(子,'addEventListener') and hasattr(子,'tagName'):
        锚=子
        自建=False
    else:
        锚=文档.createElement('span')
        自建=True
        if isinstance(子,str):
            锚.textContent=子
        elif hasattr(子,'渲染'):
            if hasattr(子,'属性') and isinstance(子.属性,dict):
                子.属性['window']=window
            节点=子.渲染()
            if 节点 is not None:
                锚.appendChild(节点)
    锚.addEventListener('mouseenter',进入)
    锚.addEventListener('mouseleave',离开)
    锚.addEventListener('click',点下)
    锚.addEventListener('focus',聚焦)
    锚.addEventListener('blur',失焦)
    文档.addEventListener('keydown',按键,True)
    if 组件 is not None:
        def 卸():
            '卸掉锚上的监听和气泡'
            取消显示()
            藏泡()
            锚.removeEventListener('mouseenter',进入)
            锚.removeEventListener('mouseleave',离开)
            锚.removeEventListener('click',点下)
            锚.removeEventListener('focus',聚焦)
            锚.removeEventListener('blur',失焦)
            文档.removeEventListener('keydown',按键,True)
            window.removeEventListener('resize',放置)
        组件.卸=卸
        组件.锚=锚
        组件.自建=自建
    if 自建 and 'parent' in 属性 and 属性['parent'] is not None:
        属性['parent'].appendChild(锚)
    return 锚

class 提示泡:
    '锚点提示。悬停延迟、方位、对齐和快捷键都受控'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})
        自身.属性.update(关键字参数)
        自身.可见=False
        自身.放置=自身.属性['side'] if 'side' in 自身.属性 else 'right'
        自身.根=None
        自身.卸=None
        自身.锚=None
        自身.自建=False
        自身.观察=None

    def 更新(自身,属性):
        '刷新 props。禁用则收起'
        自身.属性=dict(属性)
        if 属性.get('disabled') is True:
            自身.可见=False

    def 显示(自身):
        '标记为可见'
        if 自身.属性.get('disabled') is not True:
            自身.可见=True

    def 隐藏(自身):
        '标记为隐藏'
        自身.可见=False

    def 解析标签(自身):
        '字符串原样，函数则调用'
        标签=自身.属性.get('label')
        if callable(标签):
            return 标签()
        return 标签

    def 渲染(自身):
        '拆掉上一轮监听后再挂'
        if 自身.观察 is not None:
            自身.观察.disconnect()
            自身.观察=None
        if 自身.卸 is not None:
            自身.卸()
            自身.卸=None
        if 自身.自建 and 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        窗口=自身.属性['window'] if 'window' in 自身.属性 else 取握手窗口()
        自身.根=处理提示泡(窗口,绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React 调用'
        if 属性 is not None or len(关键字参数)>0:
            合并=dict(属性 if 属性 is not None else {})
            合并.update(关键字参数)
            自身.更新(合并)
        return 自身.渲染()
