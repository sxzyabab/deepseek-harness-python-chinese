import base64
from nicegui import ui as 界面
from .....基础设施.通用工具 import 路径转正斜杠
from ..加载指示器 import 加载状态
from ..缩放.控件 import 缩放控件
from ..缩放.类型 import 适应宽度
from ..远程过程调用 import 宿主文件#宿主文件

__all__=['图像媒体类型','图像体','图像面板','图像扩展名','样式表']
样式表='''
.frame{display:flex;box-sizing:border-box;width:100%;min-width:100%;height:max-content;min-height:100%;padding:12px;white-space:normal}
.surface{display:block;flex:none;margin:auto}
.image{display:block;width:100%;height:auto;border-radius:var(--dsw-radius-md);user-select:none}
.status{display:flex;align-items:center;justify-content:center;width:100%;min-height:100%;padding:10px;color:var(--dsw-alias-label-secondary);font-size:13px;line-height:1.5}
'''
界面.add_css(样式表,shared=True)

_图像媒体类型={#后缀 → MIME
    'png':'image/png',
    'jpg':'image/jpeg',
    'jpeg':'image/jpeg',
    'gif':'image/gif',
    'webp':'image/webp',
    'bmp':'image/bmp',
    'ico':'image/x-icon',
    'svg':'image/svg+xml',
}#媒体类型结束

图像扩展名=tuple(_图像媒体类型.keys())#后缀


def 图像媒体类型(路径):
    '把受支持文件名解析为媒体类型；未登记后缀为 None'
    归一=路径转正斜杠(路径)#归一
    名=归一[归一.rfind('/')+1:].lower()#文件名
    点=名.rfind('.')#末点
    if 点<0:#无扩展
        return None#无
    扩展=名[点+1:]#后缀
    return _图像媒体类型[扩展] if 扩展 in _图像媒体类型 else None#类型


def 图像体(内容,资源地址,翻译):
    '产出固有尺寸图片结构'
    路径=宿主文件(资源地址)['path']#路径
    媒体=图像媒体类型(路径)#媒体类型
    数据=内容['data'] if 内容.get('kind')=='bytes' else None#字节
    if 数据 is None or 媒体 is None:#不支持
        return {'kind':'image-status','status':'unsupported','message':翻译('unsupported')}#状态
    名=路径转正斜杠(路径)#归一
    名=名[名.rfind('/')+1:]#文件名
    return {#结构
        'kind':'image-body',
        'mediaType':媒体,
        'data':数据,
        'alt':翻译('preview',{'name':名}),
        'loading':翻译('loading'),
        'failed':翻译('failed'),
    }#结束


def _键齐(属性):
    '内容、地址和文案都在才画'
    return isinstance(属性,dict) and 'content' in 属性 and 'resourceAddress' in 属性 and 't' in 属性

class 图像面板:
    '完整图片与缩放工具'

    def __init__(自身,属性):
        '记下文档席 props。槽位只调用构造，键齐了才画'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if _键齐(自身.属性):
            自身.渲染()

    def 渲染(自身):
        '不支持、失败或图片本身'
        属性=自身.属性
        if not _键齐(属性):
            return
        内容=属性['content']
        地址=属性['resourceAddress']
        翻译=属性['t']
        模型=图像体(内容,地址,翻译)
        if 模型['kind']=='image-status':
            界面.label(模型['message']).classes('status').props('role=alert')
            return
        数据=模型['data']
        if isinstance(数据,bytearray):
            数据=bytes(数据)
        if not isinstance(数据,bytes):
            加载状态(模型['loading']).渲染()
            return
        源='data:'+模型['mediaType']+';base64,'+base64.b64encode(数据).decode('ascii')
        取标签=属性['useTabInfo'] if 'useTabInfo' in 属性 else None
        取存储=属性['useStore'] if 'useStore' in 属性 else None
        动作=属性['actions'] if 'actions' in 属性 else None
        偏好=适应宽度
        标签标识=None
        if 取标签 is not None:
            信息=取标签()
            签=信息['tab'] if isinstance(信息,dict) else 信息.tab
            标签标识=签['id'] if isinstance(签,dict) else 签.id
        if 取存储 is not None and 标签标识 is not None:
            def 选(状态):
                '本标签的缩放偏好'
                表=状态['byTab'] if isinstance(状态,dict) and 'byTab' in 状态 else {}
                return 表[标签标识] if 标签标识 in 表 else 适应宽度
            取到=取存储(选)
            if 取到 is not None:
                偏好=取到
        def 改偏好(下一):
            '写入缩放偏好'
            if 动作 is not None and 'zoom' in 动作 and 标签标识 is not None:
                动作['zoom'](标签标识,下一)
        with 界面.column().classes('frame'):
            缩放控件({'preference':偏好,'t':翻译,'onPreference':改偏好}).渲染()
            界面.image(源).classes('image').props('alt="'+模型['alt']+'"')

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()
