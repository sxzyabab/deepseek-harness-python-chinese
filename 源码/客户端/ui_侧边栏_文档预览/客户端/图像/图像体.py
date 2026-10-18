from ....模块.客户端.通告 import 取握手窗口
import os
from .....工具.工作区路径 import 路径展示拆分
from ....ui_对话.异常 import 注入模块样式文件,模块节点
from ..文案 import 套入
from ..加载指示器 import 加载指示器
from ..远程过程调用 import 宿主文件
from ..缩放.视口 import 缩放视口,缩放表面类名
from ..缩放.存储 import 默认缩放
from .文案 import 中文

__all__=['图像体','已载图片','图像媒体类型']

样式模块='image-body'
图像媒体={
    'png':'image/png',
    'jpg':'image/jpeg',
    'jpeg':'image/jpeg',
    'gif':'image/gif',
    'webp':'image/webp',
    'bmp':'image/bmp',
    'ico':'image/x-icon',
    'svg':'image/svg+xml',
}

def 图像媒体类型(路径):
    '按文件名后缀取 Blob 媒体类型。没登记的后缀没有'
    规范=路径.replace('\\','/')
    名=规范[规范.rfind('/')+1:].lower()
    扩展=名[名.rfind('.')+1:]
    return 图像媒体[扩展] if 扩展 in 图像媒体 else None

class 已载图片:
    '图加载完才量固有宽度。SVG 只进 img 的 Blob 地址'
    def __init__(自身,属性=None):
        '记下地址和缩放'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.态='loading'
        自身.宽=None
        if 'window' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '缩放视口里放图片。失败或加载中换说明'
        if 自身.根 is not None:
            自身.根.remove()
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        注入模块样式文件(
            文档,
            '图像体样式',
            os.path.join(os.path.dirname(__file__),'图像体.module.css'),
            样式模块,
        )
        框=模块节点(文档,'div',样式模块,'frame')
        框.setAttribute('data-image-preview','')
        if 自身.态=='loading':
            框.appendChild(加载指示器({'window':窗口,'label':中文['loading']}).渲染())
        if 自身.态=='failed':
            失败=模块节点(文档,'p',样式模块,'status')
            失败.setAttribute('role','alert')
            失败.textContent=中文['failed']
            框.appendChild(失败)
        面=模块节点(文档,'div',样式模块,'surface '+缩放表面类名)
        面.setAttribute('data-document-zoom-surface','')
        面.style.setProperty('--document-zoom-width',str(自身.宽 or 0)+'px')
        if 自身.态!='ready':
            面.hidden=True
        图=模块节点(文档,'img',样式模块,'image')
        图.src=属性['url']
        图.alt=套入(中文['preview'],{'name':属性['name']})
        图.setAttribute('decoding','async')
        图.draggable=False
        图.setAttribute('referrerpolicy','no-referrer')
        def 载好(事件):
            '记下固有宽度'
            自身.宽=事件.currentTarget.naturalWidth
            自身.态='ready'
            自身.渲染()
        def 出错(事件):
            '图片解码失败'
            自身.态='failed'
            自身.渲染()
        图.addEventListener('load',载好)
        图.addEventListener('error',出错)
        面.appendChild(图)
        框.appendChild(面)
        视口=缩放视口({
            'window':窗口,
            'preference':属性['preference'],
            'intrinsicWidth':自身.宽,
            'horizontalInset':24,
            'labels':属性['labels'],
            'signal':属性['signal'],
            'scrollportRef':属性['scrollportRef'],
            'onPreference':属性['onPreference'],
            'children':框,
        })
        自身.根=视口.渲染()
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

class 图像体:
    '完整图片字节。适应宽度或固定比例'
    def __init__(自身,属性=None):
        '记下文档 props'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.地址=None
        自身.源=None
        if 'window' in 自身.属性 and 'content' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '字节变成 Blob 地址后再画。类型不对就说明无法预览'
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '图像体样式',
            os.path.join(os.path.dirname(__file__),'图像体.module.css'),
            样式模块,
        )
        内容=属性['content']
        信息=属性['useTabInfo']()
        签=信息['tab']
        if 'retainTab' in 属性:
            属性['retainTab'](签['id'],签['signal'])
        def 取偏好(快照):
            '这一标签的缩放。没有则适应宽度'
            按=快照['byTab'] if isinstance(快照,dict) else {}
            return 按[签['id']] if 签['id'] in 按 else 默认缩放
        偏好=属性['useStore'](取偏好) if 'useStore' in 属性 else 默认缩放
        路径=宿主文件(属性['resourceAddress'])['path']
        媒体=图像媒体类型(路径)
        数据=内容['data'] if 内容['kind']=='bytes' else None
        if 数据 is None or 媒体 is None:
            行=模块节点(文档,'p',样式模块,'status')
            行.setAttribute('role','alert')
            行.textContent=中文['unsupported']
            自身.根=行
        else:
            if 自身.源 is None or 自身.源.get('data') is not 数据 or 自身.源.get('mediaType')!=媒体:
                if 自身.地址 is not None and hasattr(窗口,'URL'):
                    窗口.URL.revokeObjectURL(自身.地址)
                    自身.地址=None
                try:
                    块=窗口.Blob([数据],{'type':媒体})
                    自身.地址=窗口.URL.createObjectURL(块)
                    自身.源={'kind':'ready','data':数据,'mediaType':媒体,'url':自身.地址}
                except Exception:
                    自身.源={'kind':'failed','data':数据,'mediaType':媒体}
            if 自身.源.get('kind')=='failed':
                行=模块节点(文档,'p',样式模块,'status')
                行.setAttribute('role','alert')
                行.textContent=中文['failed']
                自身.根=行
            elif 自身.源.get('data') is not 数据:
                自身.根=加载指示器({'window':窗口,'label':中文['loading']}).渲染()
            else:
                名=路径展示拆分(路径)['name']
                def 改偏好(值):
                    '写下缩放偏好'
                    属性['actions']['zoom'](签['id'],值)
                标签={
                    'controls':中文['zoomControls'],
                    'menu':中文['zoomMenu'],
                    'out':中文['zoomOut'],
                    'into':中文['zoomIn'],
                    'fitWidth':中文['zoomFitWidth'],
                    'value':值文,
                }
                自身.根=已载图片({
                    'window':窗口,
                    'url':自身.源['url'],
                    'name':名,
                    'preference':偏好,
                    'onPreference':改偏好,
                    'labels':标签,
                    'signal':签['signal'],
                    'scrollportRef':属性.get('scrollportRef'),
                }).渲染()
        if 'parent' in 属性 and 属性['parent'] is not None and 自身.根 is not None:
            属性['parent'].appendChild(自身.根)
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()

def 值文(百分比):
    '缩放百分比文案'
    return 套入(中文['zoomValue'],{'percent':百分比})
