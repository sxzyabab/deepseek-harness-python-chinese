'单次日期的月历。草稿仍是 ISO，行上另显示斜杠'
from ...模块.客户端.通告 import 取握手窗口
import os
import re
from ...ui_对话.异常 import 注入模块样式文件
from ...ui_基础界面组件.icons import 图标左chevron14,图标右chevron14
from .管理文案 import 管理中文
from .选择器弹出 import 选择器弹出

__all__=['日期选择']

样式模块='date-picker'
日期表达式=re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')
星期键=['frequency.weekday.1','frequency.weekday.2','frequency.weekday.3','frequency.weekday.4','frequency.weekday.5','frequency.weekday.6','frequency.weekday.7']
步长={'ArrowLeft':-1,'ArrowRight':1,'ArrowUp':-7,'ArrowDown':7}

def 确保样式(文档):
    '月历样式只插一次'
    注入模块样式文件(文档,'日程日期选择样式',os.path.join(os.path.dirname(__file__),'日期选择.module.css'),样式模块)

def 视图(日期):
    '打不开就用今天'
    匹配=日期表达式.match(日期 or '')
    窗口=取握手窗口()
    if 匹配 is None:
        今天=窗口.Date()
        return {'year':今天.getFullYear(),'month':今天.getMonth(),'day':今天.getDate()}
    return {'year':int(匹配.group(1)),'month':int(匹配.group(2))-1,'day':int(匹配.group(3))}

def 补位(值):
    '两位'
    文=str(值)
    if len(文)<2:
        return '0'+文
    return 文

def 月天数(年,月):
    '这个月有几天'
    窗口=取握手窗口()
    return 窗口.Date(窗口.Date.UTC(年,月+1,0)).getUTCDate()

def 组iso(年,月,日):
    'YYYY-MM-DD'
    return str(年)+'-'+补位(月+1)+'-'+补位(日)

class 日期选择:
    '打开时回到已存的那天。方向键在本月里移动'
    def __init__(自身,属性):
        '先不挂面板'
        自身.属性=属性
        自身.弹出=None
        自身.视图=视图(属性.get('value') or '')
        自身.已开=False

    def 同步(自身,属性):
        '开关变化时挂上或拆掉'
        自身.属性=属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        打开=属性.get('open') is True
        if not 打开:
            if 自身.弹出 is not None:
                自身.弹出.关闭()
                自身.弹出=None
            自身.已开=False
            return None
        if not 自身.已开:
            自身.视图=视图(属性.get('value') or '')
            自身.已开=True
        if 自身.弹出 is None:
            自身.弹出=选择器弹出({
                'window':窗口,
                'open':True,
                'anchor':属性.get('anchor'),
                'label':管理中文['timing.date'],
                'className':'calendar',
                '内容模块':样式模块,
                'onClose':属性.get('onClose'),
            })
        内容=自身.弹出.打开()
        自身.画出(内容,文档,窗口)
        return 自身.弹出.根

    def 画出(自身,内容,文档,窗口):
        '月标题和日期格子'
        while 内容.firstChild is not None:
            内容.removeChild(内容.firstChild)
        视图=自身.视图
        今天=窗口.Date()
        今日=组iso(今天.getFullYear(),今天.getMonth(),今天.getDate())
        标题=窗口.Intl.DateTimeFormat(管理中文['time.locale'],{'month':'long','year':'numeric','timeZone':'UTC'}).format(窗口.Date.UTC(视图['year'],视图['month'],1))
        头=文档.createElement('div')
        头.className='head'
        头.setAttribute('data-dsh-css',样式模块)
        上=文档.createElement('button')
        上.type='button'
        上.className='nav'
        上.setAttribute('data-dsh-css',样式模块)
        上.setAttribute('aria-label',管理中文['timing.prevMonth'])
        上图=图标左chevron14({'window':窗口})
        if 上图 is not None:
            上.appendChild(上图)
        def 上一月():
            '往前一个月，日子夹在该月长度里'
            总月=自身.视图['year']*12+自身.视图['month']-1
            年=总月//12
            月=总月%12
            天数=月天数(年,月)
            自身.视图={'year':年,'month':月,'day':min(自身.视图['day'],天数)}
            自身.画出(内容,文档,窗口)
        def 点上(事件):
            '上个月'
            上一月()
        上.addEventListener('click',点上)
        题=文档.createElement('span')
        题.className='title'
        题.setAttribute('data-dsh-css',样式模块)
        题.setAttribute('aria-live','polite')
        题.textContent=标题
        下=文档.createElement('button')
        下.type='button'
        下.className='nav'
        下.setAttribute('data-dsh-css',样式模块)
        下.setAttribute('aria-label',管理中文['timing.nextMonth'])
        下图=图标右chevron14({'window':窗口})
        if 下图 is not None:
            下.appendChild(下图)
        def 下一月():
            '往后一个月'
            总月=自身.视图['year']*12+自身.视图['month']+1
            年=总月//12
            月=总月%12
            天数=月天数(年,月)
            自身.视图={'year':年,'month':月,'day':min(自身.视图['day'],天数)}
            自身.画出(内容,文档,窗口)
        def 点下(事件):
            '下个月'
            下一月()
        下.addEventListener('click',点下)
        头.appendChild(上)
        头.appendChild(题)
        头.appendChild(下)
        内容.appendChild(头)
        格=文档.createElement('div')
        格.className='grid'
        格.setAttribute('data-dsh-css',样式模块)
        格.setAttribute('role','grid')
        格.setAttribute('aria-label',标题)
        周头=文档.createElement('div')
        周头.className='week'
        周头.setAttribute('data-dsh-css',样式模块)
        周头.setAttribute('role','row')
        for 键 in 星期键:
            名=文档.createElement('div')
            名.setAttribute('role','columnheader')
            名.className='weekday'
            名.setAttribute('data-dsh-css',样式模块)
            名.textContent=管理中文[键]
            周头.appendChild(名)
        格.appendChild(周头)
        首日=窗口.Date(窗口.Date.UTC(视图['year'],视图['month'],1)).getUTCDay()
        偏移=(首日+6)%7
        总=月天数(视图['year'],视图['month'])
        格数=((偏移+总+6)//7)*7
        序=0
        while 序<格数:
            if 序%7==0:
                周=文档.createElement('div')
                周.className='week'
                周.setAttribute('data-dsh-css',样式模块)
                周.setAttribute('role','row')
                格.appendChild(周)
            日=序-偏移+1
            if 日<1 or 日>总:
                空=文档.createElement('div')
                空.setAttribute('role','gridcell')
                空.setAttribute('aria-hidden','true')
                空.className='blank'
                空.setAttribute('data-dsh-css',样式模块)
                周.appendChild(空)
            else:
                单元=文档.createElement('div')
                单元.setAttribute('role','gridcell')
                单元.className='cell'
                单元.setAttribute('data-dsh-css',样式模块)
                文本=组iso(视图['year'],视图['month'],日)
                if 文本==属性值(自身):
                    单元.setAttribute('aria-selected','true')
                    单元.className='cell selected'
                else:
                    单元.setAttribute('aria-selected','false')
                if 文本==今日:
                    单元.setAttribute('aria-current','date')
                单元.tabIndex=0 if 日==视图['day'] else -1
                单元.textContent=str(日)
                def 选(事件,日=日):
                    '选中这一天并写回草稿'
                    自身.视图={**自身.视图,'day':日}
                    自身.属性['onPick'](组iso(自身.视图['year'],自身.视图['month'],日))
                    自身.画出(内容,文档,窗口)
                def 按键(事件,日=日):
                    '回车选中，方向键在月内移动'
                    if 事件.key=='Enter' or 事件.key==' ':
                        事件.preventDefault()
                        选(事件,日)
                        return
                    步=步长.get(事件.key,0)
                    if 步==0:
                        return
                    事件.preventDefault()
                    末=月天数(自身.视图['year'],自身.视图['month'])
                    下一=日+步
                    if 下一<1:
                        下一=1
                    if 下一>末:
                        下一=末
                    自身.视图={**自身.视图,'day':下一}
                    自身.画出(内容,文档,窗口)
                单元.addEventListener('click',选)
                单元.addEventListener('keydown',按键)
                周.appendChild(单元)
            序=序+1
        内容.appendChild(格)
        焦点=None
        for 节点 in 格.querySelectorAll('[role="gridcell"]'):
            if 节点.tabIndex==0:
                焦点=节点
        if 焦点 is not None:
            焦点.focus()

    def __call__(自身,属性=None):
        '按开关重画'
        if 属性 is not None:
            return 自身.同步(属性)
        return 自身.同步(自身.属性)

def 属性值(自身):
    '当前草稿日期'
    return 自身.属性.get('value') or ''
