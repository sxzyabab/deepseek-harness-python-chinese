'时、分、秒三列。cron 可以关掉秒列'
import os
import pywebbridge
from ...ui_对话.异常 import 注入模块样式文件
from .管理文案 import 管理中文
from .任务时刻 import 秒精度
from .选择器弹出 import 选择器弹出

__all__=['时钟选择']

样式模块='clock-picker'
列定义=[
    {'label':'timing.hour','count':24},
    {'label':'timing.minute','count':60},
    {'label':'timing.second','count':60},
]

def 确保样式(文档):
    '时钟列样式只插一次'
    注入模块样式文件(文档,'日程时钟选择样式',os.path.join(os.path.dirname(__file__),'时钟选择.module.css'),样式模块)

def 补选项(数量):
    '从 00 排到数量减一'
    列=[]
    序=0
    while 序<数量:
        文=str(序)
        if len(文)<2:
            文='0'+文
        列.append(文)
        序=序+1
    return 列

def 底时钟(值):
    '没有完整时钟就从午夜起'
    秒=秒精度(值 or '')
    if len(秒)==8 and 秒[2]==':' and 秒[5]==':':
        return 秒
    return '00:00:00'

class 时钟选择:
    '打开时滚到当前值。左右换列，上下移动'
    def __init__(自身,属性):
        '先不挂面板'
        自身.属性=属性
        自身.弹出=None
        自身.光标={'column':0,'index':0}
        自身.已开=False

    def 同步(自身,属性):
        '开关变化时挂上或拆掉'
        自身.属性=属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        if 属性.get('open') is not True:
            if 自身.弹出 is not None:
                自身.弹出.关闭()
                自身.弹出=None
            自身.已开=False
            return None
        if not 自身.已开:
            底=底时钟(属性.get('value'))
            自身.光标={'column':0,'index':int(底[0:2])}
            自身.已开=True
        if 自身.弹出 is None:
            自身.弹出=选择器弹出({
                'window':窗口,
                'anchor':属性.get('anchor'),
                'label':管理中文['timing.time'],
                'className':'clock',
                '内容模块':样式模块,
                'onClose':属性.get('onClose'),
            })
        内容=自身.弹出.打开()
        自身.画出(内容,文档)
        return 自身.弹出.根

    def 画出(自身,内容,文档):
        '按列画出选项'
        while 内容.firstChild is not None:
            内容.removeChild(内容.firstChild)
        要秒=自身.属性.get('seconds',True) is not False
        列=列定义 if 要秒 else 列定义[:2]
        底=底时钟(自身.属性.get('value'))
        已选=[底[0:2],底[3:5],底[6:8]]
        序=0
        for 项 in 列:
            盒=文档.createElement('div')
            盒.setAttribute('role','listbox')
            盒.setAttribute('aria-label',管理中文[项['label']])
            盒.className='column'
            盒.setAttribute('data-dsh-css',样式模块)
            选项=补选项(项['count'])
            下标=0
            for 文 in 选项:
                行=文档.createElement('div')
                行.setAttribute('role','option')
                行.className='option selected' if 文==已选[序] else 'option'
                行.setAttribute('data-dsh-css',样式模块)
                行.setAttribute('aria-selected','true' if 文==已选[序] else 'false')
                是光标=自身.光标['column']==序 and 自身.光标['index']==下标
                行.tabIndex=0 if 是光标 else -1
                行.textContent=文
                def 选(事件,序=序,文=文,下标=下标):
                    '改这一列并写回 HH:MM:SS'
                    自身.光标={'column':序,'index':下标}
                    下一=list(已选)
                    下一[序]=文
                    自身.属性['onPick'](':'.join(下一))
                    自身.画出(内容,文档)
                def 按键(事件,序=序,文=文,下标=下标,总数=len(选项)):
                    '回车选中，左右换列，上下移动'
                    if 事件.key=='Enter' or 事件.key==' ':
                        事件.preventDefault()
                        选(事件)
                        return
                    if 事件.key=='ArrowLeft' or 事件.key=='ArrowRight':
                        事件.preventDefault()
                        目标=序+(1 if 事件.key=='ArrowRight' else -1)
                        if 目标<0 or 目标>=len(列):
                            return
                        上限=列[目标]['count']-1
                        自身.光标={'column':目标,'index':min(下标,上限)}
                        自身.画出(内容,文档)
                        return
                    if 事件.key=='Home' or 事件.key=='End':
                        事件.preventDefault()
                        自身.光标={'column':序,'index':0 if 事件.key=='Home' else 总数-1}
                        自身.画出(内容,文档)
                        return
                    if 事件.key!='ArrowDown' and 事件.key!='ArrowUp':
                        return
                    事件.preventDefault()
                    步=1 if 事件.key=='ArrowDown' else -1
                    下一=下标+步
                    if 下一<0:
                        下一=0
                    if 下一>总数-1:
                        下一=总数-1
                    自身.光标={'column':序,'index':下一}
                    自身.画出(内容,文档)
                行.addEventListener('click',选)
                行.addEventListener('keydown',按键)
                盒.appendChild(行)
                下标=下标+1
            内容.appendChild(盒)
            序=序+1
        焦点=内容.querySelector('[tabindex="0"]')
        if 焦点 is not None:
            焦点.focus()

    def __call__(自身,属性=None):
        '按开关重画'
        if 属性 is not None:
            return 自身.同步(属性)
        return 自身.同步(自身.属性)
