import os
from ....ui_基础界面组件.提示泡 import 处理提示泡
from ....ui_基础界面组件.锚定位置 import 使用锚定位置
from ....ui_基础界面组件.点外关闭 import 点外关闭
from ...异常 import 注入模块样式文件,标样式模块
from ..文案 import 中文,填入
from ..上下文占用 import 上下文占用

__all__=['上下文仪表']

样式模块='context-meter'
半径=5.5
周长=2*3.141592653589793*半径
读数槽='\u0000'

def 格式化令牌(值):
    '小于一千原样。更大用 K 或 M'
    def 缩放(候选):
        '一百以上取整，否则保留一位'
        if 候选>=100:
            return str(round(候选))
        return str(round(候选*10)/10)
    if 值<1000:
        return str(值)
    if 值<1000000:
        return 缩放(值/1000)+'K'
    return 缩放(值/1000000)+'M'

class 上下文仪表:
    '环和百分比。点开后是系统提示、工具和对话的组成'
    def __init__(自身,属性):
        '默认关着'
        自身.属性=属性
        自身.根=None
        自身.开=False
        自身.拆位=None
        自身.拆外=None
        自身.渲染()

    def 渲染(自身):
        '压力或容量还没有就不画'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        压力=属性['useProjection']('contextPressure')
        分解=属性['useProjection']('contextBreakdown')
        占用=上下文占用(压力)
        if 占用 is None:
            自身.开=False
            if 自身.根 is not None:
                自身.根.remove()
                自身.根=None
            return None
        注入模块样式文件(文档,'上下文仪表样式',os.path.join(os.path.dirname(__file__),'上下文仪表.module.css'),样式模块)
        百分=占用['percent']
        读数=str(百分)+'%'
        句=填入(中文['context.aria'],{'percent':读数槽})
        部分=句.split(读数槽)
        前=部分[0].strip() if len(部分)>0 else ''
        后=部分[1].strip() if len(部分)>1 else ''
        父=None
        if 自身.根 is not None:
            父=自身.根.parentNode
            自身.根.remove()
        elif 'parent' in 属性:
            父=属性['parent']
        根=文档.createElement('span')
        根.className='root'
        标样式模块(根,样式模块)
        钮=文档.createElement('button')
        钮.type='button'
        钮.className='trigger'
        标样式模块(钮,样式模块)
        钮.setAttribute('aria-label',填入(中文['context.aria'],{'percent':读数}))
        钮.setAttribute('aria-haspopup','dialog')
        钮.setAttribute('aria-expanded','true' if 自身.开 else 'false')
        def 切换(事件):
            '打开或关上分解面板'
            自身.开=not 自身.开
            自身.渲染()
        钮.addEventListener('click',切换)
        图=文档.createElementNS('http://www.w3.org/2000/svg','svg')
        图.setAttribute('viewBox','0 0 14 14')
        图.setAttribute('width','14')
        图.setAttribute('height','14')
        图.setAttribute('aria-hidden','true')
        轨=文档.createElementNS('http://www.w3.org/2000/svg','circle')
        轨.setAttribute('class','track')
        标样式模块(轨,样式模块)
        轨.setAttribute('cx','7')
        轨.setAttribute('cy','7')
        轨.setAttribute('r',str(半径))
        填=文档.createElementNS('http://www.w3.org/2000/svg','circle')
        填.setAttribute('class','fill')
        标样式模块(填,样式模块)
        填.setAttribute('cx','7')
        填.setAttribute('cy','7')
        填.setAttribute('r',str(半径))
        填.setAttribute('stroke-dasharray',str(周长*百分/100)+' '+str(周长))
        填.setAttribute('transform','rotate(-90 7 7)')
        图.appendChild(轨)
        图.appendChild(填)
        钮.appendChild(图)
        字=文档.createElement('span')
        字.textContent=读数
        钮.appendChild(字)
        根.appendChild(处理提示泡(窗口,{'label':填入(中文['context.aria'],{'percent':读数}),'side':'top','delayMs':200,'disabled':自身.开,'children':钮,'window':窗口}))
        if 自身.开:
            面板=文档.createElement('div')
            面板.className='panel'
            标样式模块(面板,样式模块)
            面板.setAttribute('role','dialog')
            面板.setAttribute('aria-label','上下文已用')
            头=文档.createElement('div')
            头.className='header'
            标样式模块(头,样式模块)
            for 文,类 in ((前,'headline'),(读数,'percent'),(后,'headline')):
                段=文档.createElement('span')
                段.className=类
                标样式模块(段,样式模块)
                段.textContent=文
                头.appendChild(段)
            数字=文档.createElement('span')
            数字.className='figures'
            标样式模块(数字,样式模块)
            数字.textContent='~'+格式化令牌(占用['usedTokens'])+' / '+格式化令牌(占用['contextWindow'])
            头.appendChild(数字)
            面板.appendChild(头)
            文档.body.appendChild(面板)
            if 自身.拆位 is not None:
                自身.拆位()
            自身.拆位=使用锚定位置({'anchor':根,'panel':面板,'window':窗口,'open':True,'side':'top','gap':8,'margin':12})
            if 自身.拆外 is not None:
                自身.拆外()
            def 置关(开):
                '点外面就关'
                if 开 is False:
                    自身.开=False
                    自身.渲染()
            自身.拆外=点外关闭(根,True,置关,面板)
        自身.根=根
        if 父 is not None:
            父.appendChild(自身.根)
        return 自身.根
