from .引导 import 创建超文本文档
from .打包 import 打包超文本
from .读取相对 import 创建读取超文本相对
from .基础文档 import 创建基础超文本文档
from .文案 import 中文

__all__=['超文本体','超文本面板','处理超文本面板','样式表']

样式表='''
.frame{display:block;width:100%;height:100%;min-height:240px;border:none;background:var(--dsw-alias-bg-base)}
.status{margin:0;padding:10px;color:var(--dsw-alias-label-secondary);white-space:normal}
'''

def 超文本体(内容,资源地址,关联读取,取标签信息,翻译):
    '产出隔离 HTML 文档结构，或文本交付时无。打包或引导抛出的 Exception 变成失败状态，说明不含绝对路径'
    if 内容.get('kind')!='bytes':
        return None
    标签=取标签信息()['tab']
    信号=标签['signal'] if 'signal' in 标签 else None
    相对读=创建读取超文本相对(关联读取,资源地址,信号)
    try:
        包=打包超文本(内容['data'],相对读,信号)
        文档=创建超文本文档(包)
        return {
            'kind':'html-body',
            'document':文档,
            'title':中文['frame'],
            'sandbox':'allow-scripts',
        }
    except Exception as 错误:
        return {'kind':'html-status','status':'failed','message':中文['failed']}


def _键齐(属性):
    '内容、地址、页签、文案和关联读取都在才画'
    if not isinstance(属性,dict):
        return False
    if 'content' not in 属性 or 'resourceAddress' not in 属性 or 'useTabInfo' not in 属性 or 't' not in 属性:
        return False
    return 'readRelated' in 属性 or 'addResource' in 属性

def 处理超文本面板(window,属性):
    '字节交付画进沙箱帧；失败画出状态。有 parent 就挂上去'
    if not _键齐(属性):
        return None
    文档=window.document
    if 文档.getElementById('超文本面板样式') is None:
        样式=文档.createElement('style')
        样式.id='超文本面板样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    内容=属性['content']
    if not isinstance(内容,dict) or 内容.get('kind')!='bytes':
        return None
    交互=True
    if 'useInteractivePreview' in 属性 and callable(属性['useInteractivePreview']):
        def 取值(值):
            '交互预览开关'
            return 值
        交互=属性['useInteractivePreview'](取值) is True
    if not 交互:
        try:
            静态=创建基础超文本文档(内容['data'])
        except Exception:
            状态=文档.createElement('p')
            状态.className='status'
            状态.setAttribute('role','alert')
            状态.textContent=中文['failed']
            if 'parent' in 属性:
                属性['parent'].appendChild(状态)
            return 状态
        标签=属性['useTabInfo']()['tab']
        帧=文档.createElement('iframe')
        帧.className='frame'
        帧.name='dsh-sidebar-html-'+str(标签['id'])
        帧.setAttribute('sandbox','')
        帧.setAttribute('title',中文['frame'])
        帧.setAttribute('data-html-preview','')
        帧.srcdoc=静态
        if 'parent' in 属性:
            属性['parent'].appendChild(帧)
        return 帧
    地址=属性['resourceAddress']
    取标签=属性['useTabInfo']
    翻译=属性['t']
    关联=属性['readRelated'] if 'readRelated' in 属性 else 属性['addResource']
    模型=超文本体(内容,地址,关联,取标签,翻译)
    if 模型 is None:
        return None
    if 模型['kind']=='html-status':
        状态=文档.createElement('div')
        状态.className='status'
        状态.textContent=模型['message']
        if 'parent' in 属性:
            属性['parent'].appendChild(状态)
        return 状态
    帧=文档.createElement('iframe')
    帧.className='frame'
    帧.setAttribute('sandbox',模型['sandbox'])
    帧.setAttribute('title',模型['title'])
    帧.setAttribute('data-html-preview','')
    帧.srcdoc=模型['document']
    if 'parent' in 属性:
        属性['parent'].appendChild(帧)
    return 帧

class 超文本面板:
    '隔离 HTML 文档'

    def __init__(自身,属性):
        '记下文档席 props。有 window 且键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        if _键齐(自身.属性) and 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新合成 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '拆掉旧帧，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        if 'window' not in 自身.属性:
            自身.根=None
            return None
        自身.根=处理超文本面板(自身.属性['window'],自身.属性)
        return 自身.根

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
