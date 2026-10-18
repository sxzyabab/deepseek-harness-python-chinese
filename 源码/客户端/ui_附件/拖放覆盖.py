'整页拖放邀请。指针穿透，文档上的进入和离开计数仍由拥有方维持'
from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块

__all__=['拖放覆盖']

样式模块='attachment-drop-overlay'

class 拖放覆盖:
    '文件拖到页面上方时盖住视口。禁用时换拒绝插图并去掉限额行'
    def __init__(自身,属性):
        '记下禁用和文案，并画到 body'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.渲染()

    def 更新(自身,属性):
        '换上新的禁用状态和文案'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 拆除(自身):
        '从 body 拿掉邀请层'
        if 自身.根 is not None and getattr(自身.根,'parentNode',None) is not None:
            自身.根.remove()
        自身.根=None

    def 渲染(自身):
        '把邀请层挂到 body。标题始终在，接受拖放时才显示限额'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            'dsh-attachment-drop-overlay',
            os.path.join(os.path.dirname(__file__),'拖放覆盖.module.css'),
            样式模块,
        )
        禁用=属性.get('disabled') is True
        文案=属性.get('labels') if isinstance(属性.get('labels'),dict) else {}
        罩=文档.createElement('div')
        罩.className='mask'
        标样式模块(罩,样式模块)
        罩.setAttribute('role','status')
        包=文档.createElement('div')
        包.className='wrap'
        标样式模块(包,样式模块)
        插图盒=文档.createElement('div')
        插图盒.className='illustration'
        标样式模块(插图盒,样式模块)
        插图盒.setAttribute('aria-hidden','true')
        纸='var(--dsh-drop-paper)'
        青='var(--dsh-drop-cyan)'
        蓝='var(--dsh-drop-blue)'
        前='var(--dsh-drop-front)'
        灰='var(--dsh-drop-grey)'
        章='var(--dsh-drop-badge)'

        def 造(标签,属性表):
            '造一个 SVG 节点并写上属性'
            节点=文档.createElementNS('http://www.w3.org/2000/svg',标签)
            for 键,值 in 属性表.items():
                节点.setAttribute(键,值)
            return 节点

        图=造('svg',{
            'width':'115',
            'height':'84',
            'viewBox':'0 0 115 84',
            'fill':'none',
        })
        if 禁用:
            图.appendChild(造('path',{
                'd':'M29.6829 4.63701L11.0677 12.4368C4.95519 14.998 2.07624 22.0294 4.6374 28.1419L12.2285 46.259C14.7896 52.3715 21.8211 55.2505 27.9336 52.6893L46.5488 44.8895C52.6613 42.3283 55.5403 35.2969 52.9791 29.1844L45.388 11.0673C42.8269 4.9548 35.7954 2.07585 29.6829 4.63701Z',
                'fill':灰,
            }))
            图.appendChild(造('path',{
                'd':'M30.4915 28.1375L40.8863 33.4569L37.223 34.9529L29.53 31.0165L26.7917 39.2128L23.1283 40.7088L26.8285 29.6344L16.8965 24.5522L20.5599 23.0562L27.79 26.7555L30.3637 19.0526L34.0271 17.5566L30.4915 28.1375Z',
                'fill':纸,
            }))
            图.appendChild(造('path',{
                'd':'M107.496 19.2285L81.0381 10.9357C76.8221 9.61423 72.333 11.9607 71.0116 16.1768L60.6844 49.1246C59.363 53.3406 61.7095 57.8297 65.9255 59.1511L92.383 67.4439C96.599 68.7654 101.088 66.4189 102.41 62.2029L112.737 29.255C114.058 25.039 111.712 20.55 107.496 19.2285Z',
                'fill':灰,
            }))
            图.appendChild(造('path',{
                'd':'M77.5088 26.3047L101.057 33.7967',
                'stroke':纸,
                'stroke-width':'3',
            }))
            图.appendChild(造('path',{
                'd':'M72.2646 42.7871L86.3938 47.2823',
                'stroke':纸,
                'stroke-width':'3',
            }))
            图.appendChild(造('path',{
                'd':'M74.8867 34.5469L98.4353 42.0388',
                'stroke':纸,
                'stroke-width':'3',
            }))
            图.appendChild(造('path',{
                'd':'M66.5798 30.1418L41.481 30.2006C33.5281 30.2193 27.0962 36.6815 27.1148 44.6343L27.172 69.0742C27.1907 77.0271 33.6529 83.459 41.6057 83.4404L66.7045 83.3816C74.6574 83.363 81.0894 76.9008 81.0707 68.9479L81.0135 44.5081C80.9949 36.5552 74.5327 30.1232 66.5798 30.1418Z',
                'fill':章,
            }))
            图.appendChild(造('path',{
                'd':'M54 70.7969C61.732 70.7969 68 64.5289 68 56.7969C68 49.0649 61.732 42.7969 54 42.7969C46.268 42.7969 40 49.0649 40 56.7969C40 64.5289 46.268 70.7969 54 70.7969Z',
                'stroke':纸,
                'stroke-width':'3.5',
            }))
            图.appendChild(造('path',{
                'd':'M44 46.7969L64 66.7969',
                'stroke':纸,
                'stroke-width':'3.5',
                'stroke-linecap':'round',
            }))
        else:
            组=造('g',{'clip-path':'url(#dshDropOverlayClip)'})
            组.appendChild(造('rect',{
                'y':'17.0742',
                'width':'44.1832',
                'height':'43.6431',
                'rx':'12',
                'transform':'rotate(-22.7338 0 17.0742)',
                'fill':青,
            }))
            组.appendChild(造('rect',{
                'x':'73.4043',
                'y':'8.54297',
                'width':'43.7267',
                'height':'50.5284',
                'rx':'8',
                'transform':'rotate(17.403 73.4043 8.54297)',
                'fill':蓝,
            }))
            组.appendChild(造('path',{
                'd':'M30.4917 28.1369L40.8865 33.4564L37.2232 34.9524L29.5302 31.0159L26.7919 39.2122L23.1285 40.7082L26.8287 29.6338L16.8967 24.5516L20.5601 23.0556L27.7902 26.7549L30.3639 19.052L34.0273 17.556L30.4917 28.1369Z',
                'fill':纸,
            }))
            组.appendChild(造('path',{
                'd':'M77.5088 26.3047L101.057 33.7966',
                'stroke':纸,
                'stroke-width':'3',
            }))
            组.appendChild(造('path',{
                'd':'M72.2646 42.7871L86.3938 47.2823',
                'stroke':纸,
                'stroke-width':'3',
            }))
            组.appendChild(造('path',{
                'd':'M74.8867 34.5469L98.4353 42.0388',
                'stroke':纸,
                'stroke-width':'3',
            }))
            组.appendChild(造('rect',{
                'x':'31.583',
                'y':'38.6641',
                'width':'44.9157',
                'height':'44.3666',
                'rx':'12',
                'transform':'rotate(-0.134233 31.583 38.6641)',
                'fill':前,
            }))
            组.appendChild(造('path',{
                'd':'M38.9521 73.0337C39.6129 71.7086 41.7113 66.0937 43.5113 61.1663C44.1607 59.3885 46.7484 59.3923 47.4591 61.1465C48.9728 64.8828 50.7969 68.6922 51.9988 69.1925C54.2946 70.1482 57.9854 59.3573 68.0064 70.1801',
                'stroke':纸,
                'stroke-width':'3',
            }))
            组.appendChild(造('circle',{
                'cx':'60.6157',
                'cy':'52.247',
                'r':'4.38794',
                'transform':'rotate(22.5996 60.6157 52.247)',
                'fill':纸,
            }))
            定义=造('defs',{})
            裁剪=造('clipPath',{'id':'dshDropOverlayClip'})
            裁剪.appendChild(造('rect',{
                'width':'115',
                'height':'84',
                'fill':纸,
            }))
            定义.appendChild(裁剪)
            图.appendChild(组)
            图.appendChild(定义)
        插图盒.appendChild(图)
        标题=文档.createElement('div')
        标题.className='title'
        标样式模块(标题,样式模块)
        标题.textContent='' if 文案.get('title') is None else str(文案['title'])
        包.appendChild(插图盒)
        包.appendChild(标题)
        if 禁用 is not True and 文案.get('desc') is not None:
            说明=文档.createElement('div')
            说明.className='desc'
            标样式模块(说明,样式模块)
            说明.textContent=str(文案['desc'])
            包.appendChild(说明)
        罩.appendChild(包)
        if 自身.根 is not None and getattr(自身.根,'parentNode',None) is not None:
            自身.根.remove()
        文档.body.appendChild(罩)
        自身.根=罩
        return 罩
