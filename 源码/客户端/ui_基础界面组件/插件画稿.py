from ..模块.客户端.通告 import 取握手窗口

__all__=['插件画稿终端','插件画稿循环','插件画稿子智能体','插件画稿搜索','插件画稿默认']

序号=0

def 下一标识():
    '每个实例一份 svg 定义 id，避免 url(#) 撞车'
    global 序号
    序号=序号+1
    return 'dsh_plugin_art_'+str(序号)

def 建图(文档,尺寸,类名):
    '36 视口的装饰 svg'
    图=文档.createElement('svg')
    图.setAttribute('width',str(尺寸))
    图.setAttribute('height',str(尺寸))
    图.setAttribute('viewBox','0 0 36 36')
    图.setAttribute('fill','none')
    图.setAttribute('xmlns','http://www.w3.org/2000/svg')
    if isinstance(类名,str) and 类名!='':
        图.setAttribute('class',类名)
    return 图

def 加路径(图,文档,数据,描边=None,填充=None,宽=None):
    '一条 path'
    路=文档.createElement('path')
    路.setAttribute('d',数据)
    if 描边 is not None:
        路.setAttribute('stroke',描边)
    if 宽 is not None:
        路.setAttribute('stroke-width',宽)
    if 填充 is not None:
        路.setAttribute('fill',填充)
    图.appendChild(路)
    return 路

class 插件画稿终端:
    '浅蓝终端画稿'
    def __init__(自身,属性=None):
        '记下尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '画出终端提示符'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建图(文档,尺寸,属性.get('className'))
        加路径(图,文档,'M10 11L16.606 17.606C16.6841 17.6841 16.6841 17.8107 16.606 17.8888L10 24.4948','#679EFE',None,'3.5')
        加路径(图,文档,'M20.1211 24.4946H26.8685','#679EFE',None,'3.5')
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        return 图

class 插件画稿循环:
    '四片叶子绕中心'
    def __init__(自身,属性=None):
        '记下尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '画出循环画稿'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        标识=下一标识()
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建图(文档,尺寸,属性.get('className'))
        加路径(图,文档,'M18.0486 28.4901C12.0858 28.4901 7.25195 23.6562 7.25195 17.6934C13.2148 17.6934 18.0486 22.5272 18.0486 28.4901Z',None,'#A797FC')
        加路径(图,文档,'M18.0486 6.89667C12.0858 6.89667 7.25195 11.7305 7.25195 17.6934C13.2148 17.6934 18.0486 12.8595 18.0486 6.89667Z',None,'url(#'+标识+'a)')
        加路径(图,文档,'M18.0485 28.4901C24.0114 28.4901 28.8452 23.6562 28.8452 17.6934C22.8824 17.6934 18.0485 22.5272 18.0485 28.4901Z',None,'#4561EE')
        加路径(图,文档,'M18.0485 6.89667C24.0114 6.89667 28.8452 11.7305 28.8452 17.6934C22.8824 17.6934 18.0485 12.8595 18.0485 6.89667Z',None,'#658EFF')
        定义=文档.createElement('defs')
        渐变=文档.createElement('linearGradient')
        渐变.id=标识+'a'
        渐变.setAttribute('x1','16.7911')
        渐变.setAttribute('y1','16.1655')
        渐变.setAttribute('x2','8.98192')
        渐变.setAttribute('y2','8.74289')
        渐变.setAttribute('gradientUnits','userSpaceOnUse')
        停=文档.createElement('stop')
        停.setAttribute('stop-color','#A23AE7')
        停2=文档.createElement('stop')
        停2.setAttribute('offset','1')
        停2.setAttribute('stop-color','#E2E2E2')
        渐变.appendChild(停)
        渐变.appendChild(停2)
        定义.appendChild(渐变)
        图.appendChild(定义)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        return 图

class 插件画稿子智能体:
    '两块叠着的圆角方'
    def __init__(自身,属性=None):
        '记下尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '画出子智能体画稿'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        标识=下一标识()
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建图(文档,尺寸,属性.get('className'))
        甲=文档.createElement('rect')
        甲.setAttribute('x','14.9893')
        甲.setAttribute('y','15.1877')
        甲.setAttribute('width','12.2365')
        甲.setAttribute('height','12.2365')
        甲.setAttribute('rx','2')
        甲.setAttribute('fill','url(#'+标识+'a)')
        甲.setAttribute('fill-opacity','0.8')
        乙=文档.createElement('rect')
        乙.setAttribute('x','8.87109')
        乙.setAttribute('y','9.0697')
        乙.setAttribute('width','12.2365')
        乙.setAttribute('height','12.2365')
        乙.setAttribute('rx','2')
        乙.setAttribute('fill','url(#'+标识+'b)')
        乙.setAttribute('fill-opacity','0.8')
        图.appendChild(甲)
        图.appendChild(乙)
        定义=文档.createElement('defs')
        def 渐变(名字,起,止色,终色):
            '一条纵向渐变'
            条=文档.createElement('linearGradient')
            条.id=标识+名字
            条.setAttribute('x1',起[0])
            条.setAttribute('y1',起[1])
            条.setAttribute('x2',起[2])
            条.setAttribute('y2',起[3])
            条.setAttribute('gradientUnits','userSpaceOnUse')
            停=文档.createElement('stop')
            停.setAttribute('stop-color',止色)
            停2=文档.createElement('stop')
            停2.setAttribute('offset','1')
            停2.setAttribute('stop-color',终色)
            条.appendChild(停)
            条.appendChild(停2)
            return 条
        定义.appendChild(渐变('a',('21.1075','15.1877','21.1075','27.4243'),'#45E7A4','#05909D'))
        定义.appendChild(渐变('b',('14.9894','9.0697','14.9894','21.3063'),'#69B9FF','#324DE2'))
        图.appendChild(定义)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        return 图

class 插件画稿搜索:
    '锥形渐变环和手柄。环用 foreignObject 里的 conic-gradient'
    def __init__(自身,属性=None):
        '记下尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '画出搜索画稿'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        标识=下一标识()
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建图(文档,尺寸,属性.get('className'))
        加柄=文档.createElement('path')
        加柄.setAttribute('d','M26.5362 26.9865L22.3813 22.8317')
        加柄.setAttribute('stroke','#658EFF')
        加柄.setAttribute('stroke-width','3')
        图.appendChild(加柄)
        裁组=文档.createElement('g')
        裁组.setAttribute('clip-path','url(#'+标识+'ring)')
        内组=文档.createElement('g')
        内组.setAttribute('transform','matrix(0.0119394 -0.00173904 0.00173904 0.0119394 15.7661 16.2159)')
        外来=文档.createElement('foreignObject')
        外来.setAttribute('x','-958.94')
        外来.setAttribute('y','-958.94')
        外来.setAttribute('width','1917.88')
        外来.setAttribute('height','1917.88')
        色块=文档.createElement('div')
        色块.style.background='conic-gradient(from 90deg, rgb(65, 225, 172) 0deg, rgb(101, 142, 255) 62.0619deg, rgb(65, 225, 172) 360deg)'
        色块.style.height='100%'
        色块.style.width='100%'
        外来.appendChild(色块)
        内组.appendChild(外来)
        裁组.appendChild(内组)
        图.appendChild(裁组)
        定义=文档.createElement('defs')
        裁=文档.createElement('clipPath')
        裁.id=标识+'ring'
        裁路=文档.createElement('path')
        裁路.setAttribute('d','M21.9717 16.2159H19.9717C19.9717 18.5386 18.0888 20.4215 15.7661 20.4215V22.4215V24.4215C20.2979 24.4215 23.9717 20.7478 23.9717 16.2159H21.9717ZM15.7661 22.4215V20.4215C13.4434 20.4215 11.5605 18.5386 11.5605 16.2159H9.56055H7.56055C7.56055 20.7478 11.2343 24.4215 15.7661 24.4215V22.4215ZM9.56055 16.2159H11.5605C11.5605 13.8933 13.4434 12.0104 15.7661 12.0104V10.0104V8.01038C11.2343 8.01038 7.56055 11.6841 7.56055 16.2159H9.56055ZM15.7661 10.0104V12.0104C18.0888 12.0104 19.9717 13.8933 19.9717 16.2159H21.9717H23.9717C23.9717 11.6841 20.2979 8.01038 15.7661 8.01038V10.0104Z')
        裁.appendChild(裁路)
        定义.appendChild(裁)
        图.appendChild(定义)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        return 图

class 插件画稿默认:
    '没有专属画稿时的连接块'
    def __init__(自身,属性=None):
        '记下尺寸'
        自身.属性=属性 if isinstance(属性,dict) else {}
    def 渲染(自身):
        '画出默认插件画稿'
        属性=自身.属性
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        标识=下一标识()
        尺寸=属性['size'] if 'size' in 属性 else 36
        图=建图(文档,尺寸,属性.get('className'))
        加路径(图,文档,'M24.6294 8.63696C26.2862 8.63705 27.6294 9.98016 27.6294 11.637V12.7825C27.6292 14.4391 26.2861 15.7824 24.6294 15.7825H23.4839C22.6519 15.7825 21.5454 16.3459 21.5454 17.1778V18.1573C21.5454 18.7757 22.216 19.1966 22.8345 19.1965H24.6294C26.2861 19.1965 27.6292 20.5398 27.6294 22.1965V23.9924C27.6292 25.6491 26.2861 26.9924 24.6294 26.9924H22.8345C21.1778 26.9924 19.8347 25.649 19.8345 23.9924V22.1965C19.8345 21.7148 19.4957 21.2327 19.014 21.2327H16.4792C15.7975 21.2327 15.3374 22.0061 15.3374 22.6877V23.8333C15.3373 25.49 13.9942 26.8333 12.3374 26.8333H11.1919C9.53509 26.8333 8.19198 25.49 8.19189 23.8333V22.6877C8.19189 21.0309 9.53504 19.6877 11.1919 19.6877H12.3374C13.1964 19.6877 14.3999 19.0959 14.3999 18.2369V16.0185C14.3999 14.9518 15.2646 14.0872 16.3312 14.0872H19.435C20.0596 14.0872 20.484 13.4071 20.4839 12.7825V11.637C20.4839 9.98011 21.827 8.63696 23.4839 8.63696H24.6294ZM13.4116 11.2468C13.4116 12.6882 12.2431 13.8567 10.8018 13.8567C9.36037 13.8567 8.19189 12.6882 8.19189 11.2468C8.19189 9.80544 9.36037 8.63696 10.8018 8.63696C12.2431 8.63696 13.4116 9.80544 13.4116 11.2468Z',None,'url(#'+标识+'a)')
        定义=文档.createElement('defs')
        渐变=文档.createElement('linearGradient')
        渐变.id=标识+'a'
        渐变.setAttribute('x1','15.1481')
        渐变.setAttribute('y1','9.94188')
        渐变.setAttribute('x2','15.1481')
        渐变.setAttribute('y2','13.6375')
        渐变.setAttribute('gradientUnits','userSpaceOnUse')
        停=文档.createElement('stop')
        停.setAttribute('stop-color','#54ECE7')
        停2=文档.createElement('stop')
        停2.setAttribute('offset','1')
        停2.setAttribute('stop-color','#658EFF')
        渐变.appendChild(停)
        渐变.appendChild(停2)
        定义.appendChild(渐变)
        图.appendChild(定义)
        if 'parent' in 属性 and 属性['parent'] is not None:
            属性['parent'].appendChild(图)
        return 图
