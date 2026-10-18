'历史图片和提交回声的预览。单图按长边适配，多图用方砖'
from ..模块.客户端.通告 import 取握手窗口
import os
from ..ui_对话.异常 import 注入模块样式文件,标样式模块
from ..ui_基础界面组件.icons import 描边图标,图标加载描边常规
from ..ui_基础界面组件.图像灯箱 import 图像灯箱

__all__=['消息图','图库']

样式模块='attachment-message-image'

def 读字段(对象,键):
    '字典用键，浏览器对象用属性。缺了就是 None'
    if isinstance(对象,dict):
        if 键 in 对象:
            return 对象[键]
        return None
    return getattr(对象,键,None)

class 消息图:
    '可重试的加载，以及单击打开原图。预览臂直接用本地地址'
    def __init__(自身,属性):
        '记下图片、加载器和变体，并开始第一次加载'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.已载=None
        自身.错误=False
        自身.打开=False
        自身.尝试=0
        自身.存活代=0
        自身.上次附件=None
        自身.上次加载=None
        自身.上次尝试=None
        自身.灯箱=None
        自身.当前源=None
        自身.已拆=False
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上新的图片或加载器。加载是否重来由渲染比较'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 卸灯箱(自身):
        '卸掉原图预览的键盘监听，并从 body 拿掉遮罩'
        灯箱=自身.灯箱
        自身.灯箱=None
        if 灯箱 is None:
            return
        拆=getattr(灯箱,'拆除',None)
        if callable(拆):
            拆()
        根=getattr(灯箱,'根',None)
        if 根 is not None and getattr(根,'parentNode',None) is not None:
            根.remove()

    def 拆除(自身):
        '这一代加载结果作废，原图预览也关掉'
        自身.已拆=True
        自身.存活代=自身.存活代+1
        自身.卸灯箱()

    def 点开(自身,事件=None):
        '已经有地址才打开原图'
        if 自身.当前源 is None:
            return
        自身.打开=True
        自身.渲染()

    def 重试(自身,事件=None):
        '再走同一条加载'
        自身.尝试=自身.尝试+1
        自身.渲染()

    def 关闭(自身,事件=None):
        '关掉原图预览'
        自身.打开=False
        自身.渲染()

    def 渲染(自身):
        '按变体画缩略图、加载中或失败重试，打开时把原图挂到 body'
        if 自身.已拆:
            return 自身.根
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        画完=False
        try:
            属性=自身.属性
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
            文档=窗口.document
            注入模块样式文件(
                文档,
                'dsh-attachment-message-image',
                os.path.join(os.path.dirname(__file__),'消息图.module.css'),
                样式模块,
            )
            图=属性.get('image') if isinstance(属性.get('image'),dict) else {}
            附件=图['attachment'] if 'attachment' in 图 else None
            预览=图['preview'] if 'preview' in 图 else None
            加载=属性.get('load')
            变体=属性.get('variant')
            文案=属性.get('labels') if isinstance(属性.get('labels'),dict) else {}
            if 'attachment' in 图:
                尺寸={'width':读字段(附件,'width'),'height':读字段(附件,'height')}
            else:
                宽=读字段(预览,'width')
                高=读字段(预览,'height')
                if 宽 is not None and 高 is not None:
                    尺寸={'width':宽,'height':高}
                else:
                    尺寸=None
            if 变体!='single':
                适配=None
            elif 尺寸 is None:
                适配={'width':240,'height':240,'objectPosition':'center'}
            else:
                自然=尺寸['width']/尺寸['height']
                比例=min(4,max(0.25,自然))
                if 比例>=1:
                    盒宽=240
                    盒高=240/比例
                else:
                    盒宽=240*比例
                    盒高=240
                缩放=min(1,尺寸['width']/盒宽,尺寸['height']/盒高)
                if 自然<0.25:
                    位置='center top'
                elif 自然>4:
                    位置='left center'
                else:
                    位置='center'
                适配={
                    'width':max(1,int(盒宽*缩放+0.5)),
                    'height':max(1,int(盒高*缩放+0.5)),
                    'objectPosition':位置,
                }
            标签=图['label'] if 'attachment' in 图 and 图.get('label') is not None else None
            if 标签 is None:
                标签=读字段(预览,'name')
            if 标签 is None:
                标签=读字段(附件,'name')
            if 标签 is None:
                标签=文案.get('image')
            要载=附件 is not None and (
                附件 is not 自身.上次附件 or 加载 is not 自身.上次加载 or 自身.尝试!=自身.上次尝试
            )
            if 附件 is None:
                自身.存活代=自身.存活代+1
                自身.错误=False
                自身.上次附件=None
                自身.上次加载=None
            elif 要载:
                自身.存活代=自身.存活代+1
                代=自身.存活代
                自身.上次附件=附件
                自身.上次加载=加载
                自身.上次尝试=自身.尝试
                自身.错误=False
                窥=None
                窥探=getattr(加载,'peek',None)
                if callable(窥探):
                    窥=窥探(附件)
                自身.已载=窥

                def 成功(地址,代=代):
                    '这一代还活着才换上地址'
                    if 代!=自身.存活代 or 自身.已拆:
                        return
                    自身.已载=地址
                    自身.错误=False
                    if 自身.绘制中:
                        return
                    自身.渲染()

                def 失败(错误=None,代=代):
                    '这一代还活着才标成失败'
                    if 代!=自身.存活代 or 自身.已拆:
                        return
                    自身.错误=True
                    if 自身.绘制中:
                        return
                    自身.渲染()

                回=加载(附件)
                if callable(getattr(回,'then',None)):
                    后续=回.then(成功)
                    if callable(getattr(后续,'catch',None)):
                        后续.catch(失败)
                    elif callable(getattr(回,'catch',None)):
                        回.catch(失败)
                else:
                    成功(回)
            源=读字段(预览,'url')
            if 源 is None:
                源=自身.已载
            自身.当前源=源
            加载缩略=变体=='thumbnail' and 源 is None
            if 自身.错误:
                钮=文档.createElement('button')
                钮.type='button'
                钮.className='error'
                标样式模块(钮,样式模块)
                钮.setAttribute('data-variant','' if 变体 is None else str(变体))
                if 变体=='thumbnail':
                    失败文='' if 文案.get('loadFailed') is None else str(文案['loadFailed'])
                    钮.setAttribute('title',失败文)
                    钮.setAttribute('aria-label',失败文)
                    藏=文档.createElement('span')
                    藏.setAttribute('aria-hidden','true')
                    刷新图=描边图标({'window':窗口,'size':16},'0 0 16 16',[
                        'M14.5001 8C14.5 9.28552 14.1188 10.5422 13.4045 11.611C12.6903 12.6799 11.6752 13.5129 10.4875 14.0049C9.29982 14.4968 7.99295 14.6255 6.73212 14.3747C5.4713 14.124 4.31314 13.505 3.4041 12.596C2.49514 11.687 1.87614 10.5288 1.62537 9.26798C1.37459 8.00716 1.50331 6.70028 1.99525 5.51261C2.48719 4.32494 3.32025 3.30981 4.3891 2.59557C5.45795 1.88134 6.71458 1.50008 8.0001 1.5C9.9001 1.5 11.7001 2.3 13.0001 3.6L14.5001 5.1',
                        'M14.4999 1.5V5.1H10.8999',
                    ])
                    if 刷新图 is not None:
                        藏.appendChild(刷新图)
                    钮.appendChild(藏)
                else:
                    钮.textContent='' if 文案.get('loadFailed') is None else str(文案['loadFailed'])
                钮.addEventListener('click',自身.重试)
                自身.卸灯箱()
                新=钮
            else:
                钮=文档.createElement('button')
                钮.type='button'
                钮.className='frame'
                标样式模块(钮,样式模块)
                钮.setAttribute('data-variant','' if 变体 is None else str(变体))
                if 适配 is not None:
                    钮.style.width=str(适配['width'])+'px'
                    钮.style.height=str(适配['height'])+'px'
                if 加载缩略:
                    提示='' if 文案.get('loading') is None else str(文案['loading'])
                    钮.setAttribute('title',提示)
                    钮.setAttribute('aria-label',提示)
                    钮.setAttribute('aria-busy','true')
                else:
                    钮.setAttribute('title','' if 文案.get('open') is None else str(文案['open']))
                    具名=文案.get('openNamed')
                    if callable(具名):
                        钮.setAttribute('aria-label',具名('' if 标签 is None else str(标签)))
                钮.addEventListener('click',自身.点开)
                if 源 is None:
                    等待=文档.createElement('span')
                    等待.className='loading'
                    标样式模块(等待,样式模块)
                    if 加载缩略:
                        等待.setAttribute('aria-hidden','true')
                        转=图标加载描边常规({'window':窗口,'className':'spinner'})
                        if 转 is not None:
                            标样式模块(转,样式模块)
                            等待.appendChild(转)
                    else:
                        等待.textContent='' if 文案.get('loading') is None else str(文案['loading'])
                    钮.appendChild(等待)
                else:
                    图片=文档.createElement('img')
                    图片.src=str(源)
                    图片.alt='' if 标签 is None else str(标签)
                    if 适配 is not None:
                        图片.style.objectPosition=适配['objectPosition']
                    钮.appendChild(图片)
                if 自身.打开 and 源 is not None:
                    灯属性={
                        'src':源,
                        'alt':'' if 标签 is None else str(标签),
                        'labels':文案.get('lightbox') if isinstance(文案.get('lightbox'),dict) else {},
                        'onClose':自身.关闭,
                        'window':窗口,
                    }
                    旧灯=自身.灯箱
                    旧址=None if 旧灯 is None else 旧灯.属性.get('src')
                    if 旧灯 is None or 旧址!=源:
                        自身.卸灯箱()
                        自身.灯箱=图像灯箱(灯属性)
                        自身.灯箱.渲染()
                else:
                    自身.卸灯箱()
                新=钮
            旧=自身.根
            if 旧 is not None and getattr(旧,'parentNode',None) is not None:
                旧.parentNode.replaceChild(新,旧)
            自身.根=新
            画完=True
        finally:
            自身.绘制中=False
        if 画完 and 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根

class 图库:
    '单图放大，多图或拥有方要求紧凑时用方砖，列表行用缩略图'
    def __init__(自身,属性):
        '记下图片列和加载器'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.根=None
        自身.子={}
        自身.渲染()

    def 更新(自身,属性):
        '换上新的图片列'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 拆子(自身):
        '拆掉每一张图的加载和灯箱'
        for 项 in 自身.子.values():
            项.拆除()
        自身.子={}

    def 拆除(自身):
        '卸掉全部子图'
        自身.拆子()

    def 渲染(自身):
        '空列表不留节点。同一张图沿用原来的加载状态'
        属性=自身.属性
        图列=属性.get('images') or []
        if len(图列)==0:
            自身.拆子()
            if 自身.根 is not None and getattr(自身.根,'parentNode',None) is not None:
                自身.根.remove()
            自身.根=None
            return None
        窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
        文档=窗口.document
        注入模块样式文件(
            文档,
            'dsh-attachment-message-image',
            os.path.join(os.path.dirname(__file__),'消息图.module.css'),
            样式模块,
        )
        if 属性.get('thumbnail') is True:
            变体='thumbnail'
        elif 属性.get('compact') is True or len(图列)>1:
            变体='tile'
        else:
            变体='single'
        if 自身.根 is None:
            根=文档.createElement('div')
            根.className='gallery'
            标样式模块(根,样式模块)
            自身.根=根
        对齐=属性.get('align')
        自身.根.setAttribute('data-align','' if 对齐 is None else str(对齐))
        现存={}
        下标=0
        for 图 in 图列:
            if isinstance(图,dict) and 'attachment' in 图:
                身份=读字段(图.get('attachment'),'attachmentId')
            elif isinstance(图,dict):
                身份=读字段(图.get('preview'),'url')
            else:
                身份=''
            键=str(身份)+':'+str(下标)
            下标=下标+1
            子属性={
                'image':图,
                'load':属性.get('load'),
                'variant':变体,
                'labels':属性.get('labels'),
                'window':窗口,
            }
            已有=自身.子.get(键)
            if 已有 is None:
                已有=消息图(子属性)
            else:
                已有.更新(子属性)
                已有.渲染()
            现存[键]=已有
            if 已有.根 is not None:
                自身.根.appendChild(已有.根)
        for 键,旧项 in list(自身.子.items()):
            if 键 not in 现存:
                if 旧项.根 is not None and getattr(旧项.根,'parentNode',None) is not None:
                    旧项.根.remove()
                旧项.拆除()
        自身.子=现存
        return 自身.根
