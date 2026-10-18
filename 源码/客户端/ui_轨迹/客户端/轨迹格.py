import importlib.resources as 包资源
import pywebbridge
from .轨迹记录 import 格式化已用秒数#时长标签

样式文本=包资源.files(__package__).joinpath('轨迹格.module.css').read_text(encoding='utf-8')

种类标签={
    'system':'系统',
    'user':'用户',
    'context':'上下文',
    'compacted':'已压缩',
    'message':'消息',
    'tool':'工具',
    'subtool':'子项',
}
标签类={
    'system':'tagSystem',
    'user':'tagUser',
    'context':'tagContext',
    'compacted':'tagSystem',
    'message':'tagMessage',
    'tool':'tagTool',
    'subtool':'tagSubtool',
}

class 轨迹格:
    '独立的一步轨迹格。账本行另画，这里留给直接使用'
    def __init__(自身,属性):
        '记下属性并画出格'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '属性变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出序号、种类、正文和可选用量'
        属性=自身.属性
        文档=属性['window'].document
        if 文档.getElementById('轨迹格样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹格样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        种类=属性.get('kind') or 'message'
        选中=属性.get('selected') is True
        类名=['root']
        if 选中:
            类名.append('selected')
        if isinstance(属性.get('className'),str) and 属性['className']!='':
            类名.append(属性['className'])
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('div')
        根.className=' '.join(类名)
        根.setAttribute('data-kind',种类)
        if 选中:
            根.setAttribute('data-selected','true')
        序号=文档.createElement('span')
        序号.className='index'
        序号.textContent='#'+str(属性.get('index') or '')
        槽=文档.createElement('span')
        槽.className='tagSlot'
        标=文档.createElement('span')
        标.className='tag '+标签类.get(种类,'')
        标.textContent=种类标签.get(种类,种类)
        槽.appendChild(标)
        文=文档.createElement('span')
        文.className='text'
        文.textContent=属性.get('text') or ''
        尾=文档.createElement('span')
        尾.className='trailing'
        if 种类=='message':
            for 键 in ('input','output','think'):
                量=文档.createElement('span')
                量.className='metric'
                值=属性.get(键)
                量.textContent='' if 值 is None else str(值)
                尾.appendChild(量)
        时=文档.createElement('span')
        时.className='time'
        时.textContent=格式化已用秒数(属性.get('timeSeconds'))
        尾.appendChild(时)
        根.appendChild(序号)
        根.appendChild(槽)
        根.appendChild(文)
        根.appendChild(尾)
        自身.根=根
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
