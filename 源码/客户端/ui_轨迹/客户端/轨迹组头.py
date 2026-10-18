import importlib.resources as 包资源
import pywebbridge

样式文本=包资源.files(__package__).joinpath('轨迹组头.module.css').read_text(encoding='utf-8')

class 轨迹组头:
    '标题和可选的次要描述'
    def __init__(自身,属性):
        '记下属性并画出组头'
        自身.属性=属性
        自身.根=None
        自身.渲染()

    def __call__(自身,属性=None):
        '属性变了就重画'
        if 属性 is not None:
            自身.属性=属性
        return 自身.渲染()

    def 渲染(自身):
        '画出 Message 或 Step 行'
        属性=自身.属性
        文档=属性['window'].document
        if 文档.getElementById('轨迹组头样式') is None:
            样式=文档.createElement('style')
            样式.id='轨迹组头样式'
            样式.textContent=样式文本
            文档.head.appendChild(样式)
        旧=自身.根
        父=None if 旧 is None else 旧.parentNode
        if 旧 is not None:
            旧.remove()
        根=文档.createElement('div')
        根.className='root'
        标题=文档.createElement('span')
        标题.className='title'
        标题.textContent=属性.get('title') or ''
        根.appendChild(标题)
        描述=属性.get('description')
        if isinstance(描述,str) and 描述!='':
            次=文档.createElement('span')
            次.className='description'
            次.textContent=描述
            根.appendChild(次)
        自身.根=根
        if 父 is None and 属性.get('parent') is not None:
            父=属性['parent']
        if 父 is not None and 根.parentNode is not 父:
            父.appendChild(根)
        return 根
