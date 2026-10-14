import html as 转义
from nicegui import ui as 界面
from ...异常 import 页面失败文案
from .引导 import 创建超文本文档
from .打包 import 打包超文本#打包
from .读取相对 import 创建读取超文本相对#相对读

__all__=['超文本体','超文本面板','样式表']

样式表='''
.frame{display:block;width:100%;height:100%;min-height:240px;border:none;background:var(--dsw-alias-bg-base)}
.status{margin:0;padding:10px;color:var(--dsw-alias-label-secondary);white-space:normal}
'''
界面.add_css(样式表,shared=True)

def 超文本体(内容,资源地址,关联读取,取标签信息,翻译):
    '产出隔离 HTML 文档结构，或文本交付时无。打包或引导抛出的 Exception 变成失败状态，说明不含绝对路径'
    if 内容.get('kind')!='bytes':#非字节
        return None#无
    标签=取标签信息()['tab']#标签
    信号=标签['signal'] if 'signal' in 标签 else None#寿命
    相对读=创建读取超文本相对(关联读取,资源地址,信号)#相对读
    try:
        包=打包超文本(内容['data'],相对读,信号)#打包
        文档=创建超文本文档(包)#引导
        return {#结构
            'kind':'html-body',
            'document':文档,
            'title':翻译('frame'),
            'sandbox':'allow-scripts',
        }#结束
    except Exception as 错误:
        return {'kind':'html-status','status':'failed','message':f"{翻译('failed')}：{页面失败文案(错误)}"}


def _键齐(属性):
    '内容、地址、页签、文案和关联读取都在才画'
    if not isinstance(属性,dict):
        return False
    if 'content' not in 属性 or 'resourceAddress' not in 属性 or 'useTabInfo' not in 属性 or 't' not in 属性:
        return False
    return 'readRelated' in 属性 or 'addResource' in 属性

class 超文本面板:
    '隔离 HTML 文档'

    def __init__(自身,属性):
        '记下文档席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身.渲染()

    def 渲染(自身):
        '字节交付画进沙箱帧；失败画出状态'
        属性=自身.属性
        if not _键齐(属性):
            return
        内容=属性['content']
        地址=属性['resourceAddress']
        取标签=属性['useTabInfo']
        翻译=属性['t']
        关联=属性['readRelated'] if 'readRelated' in 属性 else 属性['addResource']
        模型=超文本体(内容,地址,关联,取标签,翻译)
        if 模型 is None:
            return
        if 模型['kind']=='html-status':
            界面.label(模型['message']).classes('status')
            return
        文档=转义.escape(模型['document'],quote=True)
        标题=转义.escape(模型['title'],quote=True)
        界面.html('<iframe class="frame" sandbox="'+模型['sandbox']+'" title="'+标题+'" srcdoc="'+文档+'"></iframe>',sanitize=False)

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()
