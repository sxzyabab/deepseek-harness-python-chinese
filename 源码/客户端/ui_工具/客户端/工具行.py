import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_基础界面组件.icons import 图标检视12
from ...ui_基础界面组件.文字闪烁 import 文字闪烁
from ...ui_基础界面组件.终端块 import 终端块
from ...ui_基础界面组件.差异块 import 差异块
from ...ui_基础界面组件.读块 import 读块
from ...ui_基础界面组件.检索块 import 检索块
from ...ui_基础界面组件.网页块 import 网页块
from ...ui_基础界面组件.markdown.代码块 import 代码块
from .文案 import 中文文案
from .原语文案 import 代码工具条文案,差异块文案,读块文案,检索块文案,网页块文案
from .差异卡模型 import 聊天差异最大行数
from .读卡模型 import 聊天读最大行数
from .检索卡模型 import 聊天检索最大行数
from .终端卡模型 import 本地化终端卡模型,终端块文案,终端退出文案
from .调用模型 import 格式化工具体
from .退出代码角标 import 退出代码角标
from .询问问题卡片 import 询问问题卡片
from .工具详情 import 工具详情

__all__=['工具行']

样式模块='dsh-tool-row'

def 确保样式(文档):
    '工具行样式只插一次'
    注入模块样式文件(
        文档,
        'dsh-tool-row',
        os.path.join(os.path.dirname(__file__),'工具行.module.css'),
        样式模块,
    )

def 元素(文档,标签,类名=None):
    '带官方类名和样式模块'
    节点=文档.createElement(标签)
    if isinstance(类名,str) and 类名!='':
        节点.className=类名
        标样式模块(节点,样式模块)
    return 节点

def 内容行(文本):
    '去掉作为终止符的末尾换行后再按行切开'
    if 文本=='':
        return []
    体=文本[:-1] if 文本.endswith('\n') else 文本
    return 体.split('\n')

def 差异合计(差异列表):
    '整段替换时的增减行数。结构化补丁在差异块里，这里没有'
    增=0
    删=0
    for 差异 in 差异列表:
        旧=差异['oldText'] if isinstance(差异.get('oldText'),str) else ''
        新=差异['newText'] if isinstance(差异.get('newText'),str) else ''
        删=删+len(内容行(旧))
        增=增+len(内容行(新))
    return {'added':增,'removed':删}

def 状态文案(状态):
    'ok 没有读屏文案'
    if 状态=='preparing':
        return 中文文案('row.preparing')
    if 状态=='running':
        return 中文文案('row.running')
    if 状态=='error':
        return 中文文案('row.failed')
    if 状态=='stopped':
        return 中文文案('row.stopped')
    return None

class 工具行:
    '一行工具摘要和可选展开体'
    def __new__(类,属性):
        '画出这一行并返回根节点'
        自身=object.__new__(类)
        自身.属性=属性 if isinstance(属性,dict) else {}
        return 自身.渲染()

    def 停链接(自身,事件):
        '链接点击不切换展开'
        事件.stopPropagation()

    def 键停(自身,事件):
        '回车和空格留在链接上，不冒泡去切换行'
        if 事件.key=='Enter' or 事件.key==' ':
            事件.stopPropagation()

    def 点路径(自身,事件):
        '打开记录路径。有行号就落到那一行'
        事件.stopPropagation()
        属性=自身.属性
        打开=属性.get('onOpenFile')
        路径=属性.get('filePath')
        if 打开 is None or 路径 is None:
            return
        if 属性.get('filePathLine') is None:
            打开(路径)
        else:
            打开(路径,{'line':属性['filePathLine']})

    def 渲染(自身):
        '摘要行，展开后是卡或输入输出'
        属性=自身.属性
        窗口=属性['window']
        文档=窗口.document
        确保样式(文档)
        披露=属性['useDisclosure']()
        已展开=披露['expanded'] is True
        切换=披露['toggle']
        变体=属性['variant']
        状态=属性['state']
        终端=属性.get('terminal')
        终端体=None if 终端 is None else 本地化终端卡模型(终端)
        差异=属性.get('diff')
        读=属性.get('read')
        图像=属性.get('image')
        渲染槽=属性.get('renderSlot')
        载图=属性.get('loadImage')
        if 图像 is None or 渲染槽 is None or 载图 is None:
            图像体=None
        else:
            图像体=图像
        检索=属性.get('search')
        网页=属性.get('web')
        提问=属性.get('askQuestion')
        详情=属性.get('details')
        输入原文=属性.get('bodyRaw')
        输出文=属性.get('output')
        卡=提问 or 终端体 or 差异 or 读 or 图像体 or 检索 or 网页 or 详情
        可展=状态!='preparing' and (输入原文 is not None or 输出文 is not None or 卡 is not None)
        打开=已展开 and 可展
        体文=None
        if 打开 and 卡 is None and 输入原文 is not None:
            体文=格式化工具体(变体,输入原文)
        运行=状态=='running' or 状态=='preparing'
        if 终端体 is not None and 终端体.get('description') is not None:
            普通摘要=终端体['description']
        elif 打开 and isinstance(详情,dict) and 详情.get('expandedSummary') is not None:
            普通摘要=详情['expandedSummary']
        else:
            普通摘要=属性.get('summary') or ''
        退出文=终端退出文案(终端)
        if 状态=='error' and 退出文 is None:
            失败行=属性.get('errorSummary')
            if 失败行 is None:
                失败行=普通摘要
        else:
            失败行=None
        摘要文=普通摘要 if 失败行 is None else 失败行
        已结算提示=状态=='error' or 状态=='stopped'
        后缀=None if 已结算提示 else 属性.get('summarySuffix')
        合计=None
        if not 已结算提示 and isinstance(差异,dict):
            合计=差异合计(差异['card']['diffs'])
        能开文件=属性.get('filePath') is not None and 属性.get('onOpenFile') is not None and not 已结算提示
        链接=None if 已结算提示 else 属性.get('href')
        根=元素(文档,'div','root')
        根.setAttribute('data-variant',变体)
        if 属性.get('toolName') is not None:
            根.setAttribute('data-tool',属性['toolName'])
        根.setAttribute('data-state',状态)
        读屏=状态文案(状态)
        if 读屏 is not None:
            隐藏=元素(文档,'span','visuallyHidden')
            隐藏.textContent=读屏
            根.appendChild(隐藏)
        行=元素(文档,'div','row')
        if 可展:
            行.setAttribute('data-expandable','')
            行.setAttribute('role','button')
            行.tabIndex=0
            行.setAttribute('aria-expanded','true' if 打开 else 'false')
            def 点行(事件,切换=切换):
                '整行切换展开'
                切换()
            def 键行(事件,切换=切换):
                '回车或空格切换展开'
                if 事件.key=='Enter' or 事件.key==' ':
                    事件.preventDefault()
                    切换()
            行.addEventListener('click',点行)
            行.addEventListener('keydown',键行)
        前导=元素(文档,'span','leading')
        图标=属性.get('icon')
        if hasattr(图标,'tagName'):
            前导.appendChild(图标)
        行.appendChild(前导)
        闪=文字闪烁({'window':窗口,'active':运行,'children':属性.get('title') or '','className':'title'})
        行.appendChild(闪.渲染())
        if 摘要文!='':
            点=元素(文档,'span','sep')
            点.setAttribute('data-shimmer-decoration','')
            点.setAttribute('aria-hidden','true')
            行.appendChild(点)
            if 退出文 is None and 能开文件:
                按钮=元素(文档,'button','fileLink')
                按钮.type='button'
                按钮.textContent=摘要文
                按钮.addEventListener('click',自身.点路径)
                按钮.addEventListener('keydown',自身.键停)
                行.appendChild(按钮)
            elif 退出文 is None and isinstance(链接,str):
                锚=元素(文档,'a','fileLink')
                锚.setAttribute('href',链接)
                锚.setAttribute('target','_blank')
                锚.setAttribute('rel','noopener noreferrer')
                锚.textContent=摘要文
                锚.addEventListener('click',自身.停链接)
                锚.addEventListener('keydown',自身.键停)
                行.appendChild(锚)
            else:
                类名='summary'
                if 退出文 is None and 状态=='error':
                    类名=类名+' errorSummary'
                if 退出文 is None and 状态=='stopped':
                    类名=类名+' stoppedSummary'
                摘=元素(文档,'span',类名)
                摘.textContent=摘要文
                行.appendChild(摘)
            if 退出文 is not None:
                行.appendChild(退出代码角标({'window':窗口,'label':退出文}))
            if isinstance(后缀,str) and 后缀!='':
                尾=元素(文档,'span','summarySuffix')
                尾.textContent=后缀
                行.appendChild(尾)
            if 合计 is not None:
                统计=元素(文档,'span','summarySuffix diffStat')
                加=元素(文档,'span','diffAdded')
                加.textContent='+'+str(合计['added'])
                减=元素(文档,'span','diffRemoved')
                减.textContent='-'+str(合计['removed'])
                统计.appendChild(加)
                统计.appendChild(文档.createTextNode(' '))
                统计.appendChild(减)
                行.appendChild(统计)
        根.appendChild(行)
        if 打开:
            体类='bodyWrap'
            if 详情 is not None:
                体类=体类+' detailsBodyWrap'
            体=元素(文档,'div',体类)
            if 提问 is not None:
                体.appendChild(询问问题卡片({'window':窗口,'card':提问}))
            elif 终端体 is not None:
                卡属性=dict(终端体['card'])
                卡属性['window']=窗口
                卡属性['maxLines']=None
                卡属性['labels']=终端块文案()
                卡属性['className']='terminalBody'
                体.appendChild(终端块(卡属性).渲染())
            elif 差异 is not None:
                卡属性=dict(差异['card'])
                卡属性['window']=窗口
                卡属性['labels']=差异块文案()
                卡属性['maxLines']=聊天差异最大行数
                卡属性['className']='diffBody'
                体.appendChild(差异块(卡属性).渲染())
            elif 读 is not None:
                卡属性=dict(读)
                卡属性['window']=窗口
                卡属性['labels']=读块文案()
                卡属性['maxLines']=聊天读最大行数
                卡属性['className']='readBody'
                体.appendChild(读块(卡属性).渲染())
            elif 图像体 is not None:
                图盒=元素(文档,'div','imageBody')
                if 渲染槽 is not None and 载图 is not None:
                    画廊=渲染槽('tool.call.images',{
                        'images':图像体['images'],
                        'loadImage':载图,
                        'align':'start',
                        'window':窗口,
                    })
                    if hasattr(画廊,'tagName'):
                        图盒.appendChild(画廊)
                元=元素(文档,'div','imageMeta')
                路径行=文档.createElement('div')
                路径行.textContent=图像体['path']
                元.appendChild(路径行)
                for 图像项 in 图像体['images']:
                    附件=图像项['attachment']
                    尺寸行=文档.createElement('div')
                    if 附件.get('originalDimensions') is None:
                        尺寸行.textContent=中文文案('row.imageSize',{
                            'width':附件['width'],
                            'height':附件['height'],
                            'bytes':附件['bytes'],
                        })
                    else:
                        原始=附件['originalDimensions']
                        尺寸行.textContent=中文文案('row.imageSizeDownscaled',{
                            'width':附件['width'],
                            'height':附件['height'],
                            'originalWidth':原始['width'],
                            'originalHeight':原始['height'],
                            'bytes':附件['bytes'],
                        })
                    元.appendChild(尺寸行)
                图盒.appendChild(元)
                if 图像体.get('extraText') is not None:
                    额外=元素(文档,'div','imageExtra')
                    额外.textContent=图像体['extraText']
                    图盒.appendChild(额外)
                体.appendChild(图盒)
            elif 检索 is not None:
                卡属性=dict(检索['card'])
                卡属性['window']=窗口
                卡属性['labels']=检索块文案()
                卡属性['maxLines']=聊天检索最大行数
                卡属性['className']='searchBody'
                体.appendChild(检索块(卡属性).渲染())
                if 检索.get('recovery') is not None:
                    恢复=元素(文档,'div','searchRecovery')
                    恢复.textContent=检索['recovery']
                    体.appendChild(恢复)
            elif 网页 is not None:
                卡属性=dict(网页)
                卡属性['window']=窗口
                卡属性['labels']=网页块文案()
                卡属性['className']='webBody'
                体.appendChild(网页块(卡属性).渲染())
            elif 详情 is not None:
                体.appendChild(工具详情({
                    'window':窗口,
                    'model':详情,
                    'hasInspect':属性.get('inspect') is not None,
                    'onOpenFile':属性.get('onOpenFile'),
                }))
            else:
                if 变体=='code' and 体文 is not None:
                    滚=元素(文档,'div','bodyScroll')
                    滚.appendChild(代码块({
                        'window':窗口,
                        'code':体文,
                        'lang':'typescript',
                        'copyLabel':中文文案('copy'),
                        'copiedLabel':中文文案('copied'),
                        'toolbarLabels':代码工具条文案(),
                        'className':'codeBody',
                    }).渲染())
                    体.appendChild(滚)
                卡体=None if 变体=='code' else 体文
                if 卡体 is not None or 输出文 is not None:
                    盒=元素(文档,'div','ioCard')
                    if 卡体 is not None:
                        段=元素(文档,'div','ioSection')
                        标=元素(文档,'span','ioLabel')
                        标.textContent=中文文案('row.input')
                        文=元素(文档,'span','ioText')
                        文.textContent=卡体
                        段.appendChild(标)
                        段.appendChild(文)
                        盒.appendChild(段)
                    if 卡体 is not None and 输出文 is not None:
                        盒.appendChild(元素(文档,'span','ioDivider'))
                    if 输出文 is not None:
                        段=元素(文档,'div','ioSection')
                        标=元素(文档,'span','ioLabel')
                        标.textContent=中文文案('row.output')
                        文=元素(文档,'span','ioText')
                        if 状态=='error':
                            文.setAttribute('data-error','')
                        文.textContent=输出文
                        段.appendChild(标)
                        段.appendChild(文)
                        盒.appendChild(段)
                    体.appendChild(盒)
            查看=属性.get('inspect')
            if 查看 is not None:
                钮=元素(文档,'button','inspectButton')
                钮.type='button'
                钮.appendChild(图标检视12({'window':窗口}))
                钮.appendChild(文档.createTextNode(中文文案('row.inspect')))
                def 点查看(事件,查看=查看):
                    '打开轨迹里的这次调用'
                    查看()
                钮.addEventListener('click',点查看)
                体.appendChild(钮)
            根.appendChild(体)
        return 根
