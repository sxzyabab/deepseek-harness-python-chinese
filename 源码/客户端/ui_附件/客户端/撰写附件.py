'撰写栏上的草稿附件：拖放邀请、文件卡、图片缩略图和原图预览'
from ...模块.客户端.通告 import 取握手窗口
import os
from ...ui_对话.异常 import 注入模块样式文件,标样式模块
from ...ui_对话.客户端.文案 import 中文,填入
from ...ui_基础界面组件.icons import 描边图标
from ...ui_基础界面组件.图像灯箱 import 图像灯箱
from ..拖放覆盖 import 拖放覆盖
from ..文件卡 import 文件卡
from ..附件轨 import 附件轨
from .标注列表 import 灯箱文案

__all__=['撰写附件']

样式模块='attachment-composer'

class 撰写附件:
    '草稿图片、待发送文件、整页拖放和原图预览'
    def __init__(自身,属性):
        '记下份额，并装上文档拖放'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.预览=None
        自身.拖放中=False
        自身.拖放深度=0
        自身.卸拖放=None
        自身.拖放键=None
        自身.覆盖=None
        自身.灯箱=None
        自身.轨=None
        自身.壳=None
        自身.根=None
        自身.窗口=None
        自身.绘制中=False
        自身.待重画=False
        自身.渲染()

    def 更新(自身,属性):
        '换上新的草稿和上传状态'
        自身.属性=属性 if isinstance(属性,dict) else {}

    def 卸监听(自身):
        '卸掉这一份文档拖放监听'
        if callable(自身.卸拖放):
            自身.卸拖放()
        自身.卸拖放=None
        自身.拖放键=None

    def 卸覆盖(自身):
        '拿掉整页拖放邀请'
        if 自身.覆盖 is not None:
            自身.覆盖.拆除()
            自身.覆盖=None

    def 卸灯箱(自身):
        '卸掉原图预览的键盘监听和遮罩'
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
        '卸拖放、邀请层、原图和附件轨'
        自身.卸监听()
        自身.卸覆盖()
        自身.卸灯箱()
        if 自身.轨 is not None:
            自身.轨.拆除()
            自身.轨=None

    def 设拖放(自身,活动):
        '拖放是否盖住页面。没变就不重画'
        if 自身.拖放中==活动:
            return
        自身.拖放中=活动
        if 自身.绘制中:
            自身.待重画=True
            return
        自身.渲染()

    def 关闭预览(自身,事件=None):
        '关掉当前原图'
        自身.预览=None
        自身.渲染()

    def 挂监听(自身):
        '能接收或加入回调变了才重装。深度计数跨着重装保留'
        属性=自身.属性
        可接受=属性['canAcceptDrop']
        加入=属性['onAddFiles']
        键=(可接受,id(加入))
        if 自身.拖放键==键 and 自身.卸拖放 is not None:
            return
        if callable(自身.卸拖放):
            自身.卸拖放()
            自身.卸拖放=None
        自身.拖放键=键
        窗口=自身.窗口
        文档=窗口.document

        def 文件传输(事件):
            '没有 Files 类型的拖拽不当成附件'
            传输=事件.dataTransfer
            if 传输 is None:
                return None
            if 传输.types.includes('Files') is not True:
                return None
            return 传输

        def 复位(事件=None):
            '拖放深度归零，并收起邀请层'
            自身.拖放深度=0
            自身.设拖放(False)

        def 进入(事件):
            '文件拖进页面就加深一层'
            if 文件传输(事件) is None:
                return
            事件.preventDefault()
            自身.拖放深度=自身.拖放深度+1
            自身.设拖放(True)

        def 经过(事件):
            '能接收就显示复制，否则禁止放下'
            传输=文件传输(事件)
            if 传输 is None:
                return
            事件.preventDefault()
            if 可接受:
                传输.dropEffect='copy'
            else:
                传输.dropEffect='none'

        def 离开(事件):
            '离开一层。拖出视口时整页复位'
            if 文件传输(事件) is None:
                return
            下一层=自身.拖放深度-1
            if 下一层<0:
                下一层=0
            自身.拖放深度=下一层
            if 自身.拖放深度==0:
                自身.设拖放(False)
            离开视口=(
                事件.clientX<=0 or 事件.clientY<=0
                or 事件.clientX>=窗口.innerWidth
                or 事件.clientY>=窗口.innerHeight
            )
            目标=事件.target
            if (目标 is 文档.documentElement or 目标 is 文档.body) and 离开视口:
                复位()

        def 放下(事件):
            '收下这一批文件。目录只能靠 entry 接口认出来'
            传输=文件传输(事件)
            if 传输 is None:
                return
            事件.preventDefault()
            复位()
            if 可接受 is not True:
                return
            文件列=[]
            文件表=传输.files
            序号=0
            while 序号<文件表.length:
                文件列.append(文件表.item(序号))
                序号=序号+1
            目录=set()
            文件下标=0
            项表=传输.items
            项序=0
            while 项序<项表.length:
                项=项表.item(项序)
                项序=项序+1
                if 项.kind!='file':
                    continue
                文件=文件列[文件下标] if 文件下标<len(文件列) else None
                文件下标=文件下标+1
                取入口=getattr(项,'webkitGetAsEntry',None)
                if not callable(取入口):
                    continue
                入口=取入口()
                if 入口 is None or 入口.isDirectory is not True:
                    continue
                if 文件 is not None:
                    目录.add(文件)
            加入(文件列,目录)

        文档.addEventListener('dragenter',进入)
        文档.addEventListener('dragover',经过)
        文档.addEventListener('dragleave',离开)
        文档.addEventListener('drop',放下)
        窗口.addEventListener('dragend',复位)

        def 卸下():
            '卸掉这一份文档拖放监听'
            文档.removeEventListener('dragenter',进入)
            文档.removeEventListener('dragover',经过)
            文档.removeEventListener('dragleave',离开)
            文档.removeEventListener('drop',放下)
            窗口.removeEventListener('dragend',复位)

        自身.卸拖放=卸下

    def 画一项(自身,项):
        '文件画文件卡，图片画缩略图和移除钮'
        附件=项['attachment']
        窗口=自身.窗口
        文档=窗口.document
        文件=附件['file']
        if isinstance(文件,dict):
            原名=文件['name'] if isinstance(文件.get('name'),str) else ''
            字节=文件['size'] if 'size' in 文件 else 0
        else:
            原名=getattr(文件,'name',None) or ''
            字节=getattr(文件,'size',None) or 0
            if not isinstance(原名,str):
                原名=''
        if 附件['kind']=='file':
            标识=附件['id']
            上传表=自身.属性['uploads']
            记录=上传表[标识] if isinstance(上传表,dict) and 标识 in 上传表 else None
            if 记录 is None or 记录.get('status')=='uploading':
                状态='uploading'
            elif 记录.get('status')=='ready':
                状态='ready'
            else:
                状态='error'
            进度=None
            if (
                isinstance(记录,dict)
                and 记录.get('status')=='uploading'
                and 记录.get('total') is not None
                and 记录.get('total')>0
            ):
                进度=记录['loaded']/记录['total']

            def 移除文件(事件=None,标识=标识):
                '从草稿拿掉这一份文件'
                自身.属性['onRemoveAttachment'](标识)

            def 重试文件(事件=None,标识=标识):
                '重试这一份文件上传'
                自身.属性['onRetryFile'](标识)

            卡属性={
                'name':原名 if 原名!='' else 中文['file.label'],
                'bytes':字节,
                'state':状态,
                'labels':{
                    'label':中文['file.pending'],
                    'remove':填入(中文['file.remove'],{'name':原名}),
                    'uploading':中文['file.uploading'],
                    'failed':中文['file.uploadFailed'],
                    'retry':填入(中文['file.retry'],{'name':原名}),
                },
                'onRemove':移除文件,
                'onRetry':重试文件,
                'window':窗口,
            }
            if 进度 is not None:
                卡属性['progress']=进度
            卡=文件卡(卡属性)
            return 卡.根
        盒=文档.createElement('div')
        盒.className='imageItem'
        标样式模块(盒,样式模块)

        def 打开这张(事件=None,附件=附件):
            '打开这一张的原图'
            自身.预览=附件
            自身.渲染()

        缩略=文档.createElement('button')
        缩略.type='button'
        缩略.className='thumbnail'
        标样式模块(缩略,样式模块)
        缩略.setAttribute('title',中文['image.openOriginal'])
        缩略.addEventListener('click',打开这张)
        图片=文档.createElement('img')
        图片.src=附件['previewUrl']
        if 原名!='':
            图片.alt=原名
        else:
            图片.alt=中文['image.pending']
        缩略.appendChild(图片)

        def 移除图片(事件=None,附件=附件):
            '从草稿拿掉这一张图片'
            自身.属性['onRemoveAttachment'](附件['id'])

        移除=文档.createElement('button')
        移除.type='button'
        移除.className='remove'
        标样式模块(移除,样式模块)
        移除.setAttribute('aria-label',填入(中文['image.remove'],{'name':原名}))
        移除.addEventListener('click',移除图片)
        关闭图=描边图标({'window':窗口,'size':12},'0 0 16 16',[
            'M3.5 3.5L12.5 12.5',
            'M12.5 3.5L3.5 12.5',
        ])
        if 关闭图 is not None:
            移除.appendChild(关闭图)
        盒.appendChild(缩略)
        盒.appendChild(移除)
        return 盒

    def 渲染(自身):
        '有拖放就盖邀请层，有草稿就画轨，有预览就把原图挂到 body'
        if 自身.绘制中:
            自身.待重画=True
            return 自身.根
        自身.绘制中=True
        画完=False
        try:
            属性=自身.属性
            窗口=属性['window'] if 'window' in 属性 else 取握手窗口()
            自身.窗口=窗口
            文档=窗口.document
            注入模块样式文件(
                文档,
                'dsh-attachment-composer',
                os.path.join(os.path.dirname(__file__),'撰写附件.module.css'),
                样式模块,
            )
            附件列=属性['attachments']
            预览=自身.预览
            if 预览 is not None:
                还在=False
                for 项 in 附件列:
                    if 项['id']==预览['id']:
                        还在=True
                        break
                if 还在 is not True:
                    自身.预览=None
                    预览=None
            自身.挂监听()
            可接受=属性['canAcceptDrop'] is True
            限额=属性.get('dropLimits')
            if 可接受 is not True:
                拖放文案={'title':中文['attachment.dropBlocked']}
            else:
                拖放文案={'title':中文['attachment.dropTitle']}
                if 限额 is not None:
                    拖放文案['desc']=填入(中文['attachment.dropDesc'],限额)
            if 自身.拖放中:
                覆盖属性={'disabled':可接受 is not True,'labels':拖放文案,'window':窗口}
                if 自身.覆盖 is None:
                    自身.覆盖=拖放覆盖(覆盖属性)
                else:
                    自身.覆盖.更新(覆盖属性)
                    自身.覆盖.渲染()
            else:
                自身.卸覆盖()
            if len(附件列)==0:
                if 自身.轨 is not None:
                    自身.轨.拆除()
                    自身.轨=None
                自身.壳=None
                目标=None
            else:
                if 自身.壳 is None:
                    壳=文档.createElement('div')
                    壳.className='rail'
                    标样式模块(壳,样式模块)
                    自身.壳=壳
                项列=[{'id':项['id'],'attachment':项} for 项 in 附件列]
                轨属性={
                    'items':项列,
                    'labels':{
                        'group':中文['attachment.pending'],
                        'scrollLeft':中文['attachment.scrollLeft'],
                        'scrollRight':中文['attachment.scrollRight'],
                    },
                    'renderItem':自身.画一项,
                    'window':窗口,
                }
                if 自身.轨 is None:
                    自身.轨=附件轨(轨属性)
                else:
                    自身.轨.更新(轨属性)
                    自身.轨.渲染()
                if 自身.轨.根 is not None and 自身.轨.根.parentNode is not 自身.壳:
                    自身.壳.appendChild(自身.轨.根)
                目标=自身.壳
            if 预览 is not None:
                文件=预览['file']
                if isinstance(文件,dict):
                    原名=文件['name'] if isinstance(文件.get('name'),str) else ''
                else:
                    原名=getattr(文件,'name',None) or ''
                    if not isinstance(原名,str):
                        原名=''
                灯属性={
                    'src':预览['previewUrl'],
                    'alt':原名 if 原名!='' else 中文['image.original'],
                    'labels':灯箱文案(),
                    'onClose':自身.关闭预览,
                    'window':窗口,
                }
                旧址=None if 自身.灯箱 is None else 自身.灯箱.属性.get('src')
                if 自身.灯箱 is None or 旧址!=灯属性['src']:
                    自身.卸灯箱()
                    自身.灯箱=图像灯箱(灯属性)
                    自身.灯箱.渲染()
            else:
                自身.卸灯箱()
            旧=自身.根
            if 旧 is not 目标:
                if 旧 is not None and getattr(旧,'parentNode',None) is not None:
                    if 目标 is None:
                        旧.remove()
                    else:
                        旧.parentNode.replaceChild(目标,旧)
                自身.根=目标
            画完=True
        finally:
            自身.绘制中=False
        if 画完 and 自身.待重画:
            自身.待重画=False
            return 自身.渲染()
        return 自身.根
