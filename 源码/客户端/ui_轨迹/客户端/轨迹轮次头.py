import importlib.resources as 包资源
import pywebbridge

样式文本=包资源.files(__package__).joinpath('轨迹轮次头.module.css').read_text(encoding='utf-8')

class 轨迹轮次头:
    '粘性轮次条：第 N 轮，以及输入、输出、思考、时间'
    def __init__(自身,属性):
        '记下属性并画出轮次头'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '属性变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出轮次标题和四列标签'
        属性=自身.属性
        文档=属性['window'].document
        if 文档.getElementById('轨迹轮次头样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹轮次头样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('div')
        根.className='root'
        内=文档.createElement('div')
        内.className='inner'
        标题=文档.createElement('span')
        标题.className='title'
        标题.textContent='第 '+str(属性.get('turn') or 1)+' 轮'
        列=文档.createElement('div')
        列.className='columns'
        列.setAttribute('aria-hidden','true')
        for 文案 in ('输入','输出','思考','时间'):
            格=文档.createElement('span')
            格.className='column'
            格.textContent=文案
            列.appendChild(格)
        内.appendChild(标题)
        内.appendChild(列)
        根.appendChild(内)
        自身.根=根
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
