from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['菜单表面']

样式模块='menu-surface'
锚序=0

def 下一锚名():
    '给这一层菜单一个不重复的 CSS 锚名'
    global 锚序
    锚序=锚序+1
    return '--dsh-menu-'+str(锚序)

class 菜单表面:
    '菜单材质。macOS 上在页面内容后面铺一块不透明背板，好让透明窗能模糊'
    def __init__(自身,属性=None):
        '记下是否紧凑'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.背板=None

    def 更新(自身,属性):
        '换成新的 props'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 渲染(自身):
        '画出半透明表面，并把背板挂到 body。锚必须先于背板'
        if 自身.背板 is not None:
            自身.背板.remove()
            自身.背板=None
        if 自身.根 is not None:
            自身.根.remove()
            自身.根=None
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            '菜单表面样式',
            os.path.join(os.path.dirname(__file__),'菜单表面.module.css'),
            样式模块,
        )
        紧凑=属性.get('compact') is True
        锚名=下一锚名()
        表面类=['surface']
        if 紧凑:
            表面类.append('compact')
        附加=属性.get('className')
        if isinstance(附加,str) and 附加!='':
            表面类.append(附加)
        根=文档.createElement('div')
        根.className=' '.join(表面类)
        标样式模块(根,样式模块)
        根.setAttribute('data-menu-material','translucent')
        根.style.setProperty('--dsh-menu-anchor',锚名)
        if 'role' in 属性 and 属性['role'] is not None:
            根.setAttribute('role',属性['role'])
        材质=文档.createElement('div')
        材质.setAttribute('aria-hidden','true')
        材质.className='material'
        标样式模块(材质,样式模块)
        根.appendChild(材质)
        背类=['backing']
        if 紧凑:
            背类.append('compact')
        背=文档.createElement('div')
        背.setAttribute('aria-hidden','true')
        背.setAttribute('data-menu-backing','')
        背.className=' '.join(背类)
        标样式模块(背,样式模块)
        背.style.setProperty('--dsh-menu-anchor',锚名)
        文档.body.appendChild(背)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(根)
        自身.根=根
        自身.背板=背
        return 自身.根

    def __call__(自身,属性=None):
        '再次调用时先换 props 再画'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
