'输入区草稿附件：拖放邀请、文件卡、图片缩略图和原图预览'
from nicegui import ui as 界面
from .文件卡 import 文件卡
from .异常 import 叠页面失败
from .附件轨 import 附件轨
from .拖放覆盖 import 拖放覆盖
from .原图灯箱 import 原图灯箱
from .拖放事件 import 安装文档拖放事件

__all__=['撰写附件']

def 取(对象,键,默认=None):
    '字典或对象上的字段'
    if isinstance(对象,dict):
        return 对象[键] if 键 in 对象 else 默认
    return getattr(对象,键,默认)

def 灯箱文案(翻译):
    '原图对话框文案'
    return {'dialog':翻译('image.preview'),'close':翻译('image.closePreview')}

def 拖放文案(翻译,可接受,限制):
    '不能放下时只有标题'
    if 可接受 is not True:
        return {'title':翻译('attachment.dropBlocked')}
    文={'title':翻译('attachment.dropTitle')}
    if isinstance(限制,dict) and 'count' in 限制 and 'size' in 限制:
        文['desc']=翻译('attachment.dropDesc',{'count':限制['count'],'size':限制['size']})
    return 文

def 文件文案(翻译,名称):
    '文件卡用的句子'
    return {
        'label':翻译('file.pending'),
        'remove':翻译('file.remove',{'name':名称}),
        'uploading':翻译('file.uploading'),
        'failed':翻译('file.uploadFailed'),
        'retry':翻译('file.retry',{'name':名称}),
    }

def 轨文案(翻译):
    '附件轨箭头和组名'
    return {
        'group':翻译('attachment.pending'),
        'scrollLeft':翻译('attachment.scrollLeft'),
        'scrollRight':翻译('attachment.scrollRight'),
    }

class 撰写附件:
    '草稿图片、待传文件、拖放层和原图预览'
    def __init__(自身,属性):
        '记下 props，并在有页面文档时装上拖放'
        自身.属性=属性 if isinstance(属性,dict) else {}
        自身.预览=None
        自身.拖放中=False
        自身.深度={'current':0}
        自身._拆拖放=None
        自身._已装拖放=False
        自身.画面失败=None
        自身.装拖放()
        if 'attachments' in 自身.属性:
            自身.渲染()

    def 更新(自身,属性):
        '刷新 props；预览对应的附件消失则关掉'
        自身.属性=属性 if isinstance(属性,dict) else {}
        if 自身.预览 is not None:
            标识=取(自身.预览,'id')
            仍在=False
            for 条 in 自身.附件表():
                if 取(条,'id')==标识:
                    仍在=True
                    break
            if 仍在 is not True:
                自身.预览=None

    def 翻译(自身):
        '缺文案钩子时返回键'
        翻译=自身.属性.get('t')
        if callable(翻译):
            return 翻译
        return lambda 键,参数=None:键

    def 附件表(自身):
        '草稿附件列表；空列表保留'
        表=自身.属性.get('attachments')
        return 表 if isinstance(表,list) else []

    def 上传态(自身,标识):
        'uploading、ready 或 error，以及可选进度'
        表=自身.属性.get('uploads')
        条=None
        if isinstance(表,dict) and 标识 in 表:
            条=表[标识]
        elif 表 is not None:
            条=取(表,标识)
        if not isinstance(条,dict):
            return 'uploading',None
        状况=条.get('status')
        if 状况=='ready':
            return 'ready',None
        if 状况=='error':
            return 'error',None
        总量=条.get('total')
        已传=条.get('loaded')
        进度=None
        if isinstance(总量,(int,float)) and not isinstance(总量,bool) and 总量>0 and isinstance(已传,(int,float)) and not isinstance(已传,bool):
            进度=已传/总量
        return 'uploading',进度

    def 装拖放(自身):
        '页面文档存在时装整页拖放；没有文档则只画已有附件'
        if 自身._已装拖放:
            return
        自身._已装拖放=True
        def 加入(文件表,目录集):
            '交给输入区'
            回调=自身.属性.get('onAddFiles')
            if callable(回调):
                回调(文件表,目录集)
        def 设活动(开):
            '拖放层跟着深度计数开关'
            自身.拖放中=开 is True
            自身.渲染()
        自身._拆拖放=安装文档拖放事件(自身.属性.get('canAcceptDrop') is True,加入,自身.深度,设活动)

    def 渲染(自身):
        '始终留一列；拖放、草稿轨和灯箱画在里面'
        翻译=自身.翻译()
        可接受=自身.属性.get('canAcceptDrop') is True
        附件=自身.附件表()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=叠页面失败(自身.画面失败,错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.column().classes('composer-attachments')
        失败文=自身.画面失败 if isinstance(自身.画面失败,str) and 自身.画面失败!='' else None
        有内容=自身.拖放中 is True or len(附件)>0 or 自身.预览 is not None or 失败文 is not None
        自身.根.set_visibility(有内容)
        with 自身.根:
            if 失败文 is not None:
                界面.label(失败文)
            自身.画内容(界面,翻译,可接受,附件)

    def 画内容(自身,界面,翻译,可接受,附件):
        '拖放中画邀请层；有草稿时画轨；有预览时开灯箱'
        if 自身.拖放中:
            拖放覆盖({
                'disabled':可接受 is not True,
                'labels':拖放文案(翻译,可接受,自身.属性.get('dropLimits')),
            }).渲染()
        if len(附件)>0:
            def 画项(项):
                '文件走文件卡，图片走缩略图'
                条=项.get('attachment') if isinstance(项,dict) else None
                if 条 is None:
                    return
                标识=取(条,'id')
                种类=取(条,'kind')
                文件=取(条,'file') or {}
                名称=取(文件,'name')
                if not isinstance(名称,str) or 名称=='':
                    名称=翻译('file.label') if 种类=='file' else 翻译('image.pending')
                if 种类=='file':
                    态,进度=自身.上传态(标识)
                    面={'name':名称,'bytes':取(文件,'size') or 0,'state':态,'labels':文件文案(翻译,名称)}
                    if 进度 is not None:
                        面['progress']=进度
                    def 移除(当前=标识):
                        '从草稿去掉'
                        回调=自身.属性.get('onRemoveAttachment')
                        if callable(回调):
                            回调(当前)
                    def 重试(当前=标识):
                        '重传这一份'
                        回调=自身.属性.get('onRetryFile')
                        if callable(回调):
                            回调(当前)
                    面['onRemove']=移除
                    面['onRetry']=重试
                    文件卡(面).渲染()
                    return
                地址=取(条,'previewUrl')
                def 打开(当前=条):
                    '打开原图'
                    自身.预览=当前
                    自身.渲染()
                def 移除图(当前=标识):
                    '从草稿去掉这张图'
                    回调=自身.属性.get('onRemoveAttachment')
                    if callable(回调):
                        回调(当前)
                with 界面.column().classes('attachment-image'):
                    if isinstance(地址,str) and 地址!='':
                        图=界面.image(地址)
                        图.on('click', lambda _事件:打开())
                    界面.button(on_click=移除图).props('icon=close flat round aria-label="'+翻译('image.remove',{'name':名称})+'"')
            轨项=[{'id':取(条,'id'),'attachment':条,'previewUrl':取(条,'previewUrl') if 取(条,'kind')!='file' else None} for 条 in 附件]
            附件轨({
                'items':轨项,
                'labels':轨文案(翻译),
                'renderItem':画项,
            }).渲染()
        if 自身.预览 is not None:
            文件=取(自身.预览,'file') or {}
            名称=取(文件,'name')
            if not isinstance(名称,str) or 名称=='':
                名称=翻译('image.original')
            def 关掉():
                '关掉原图'
                自身.预览=None
                自身.渲染()
            原图灯箱({
                'src':取(自身.预览,'previewUrl'),
                'alt':名称,
                'labels':灯箱文案(翻译),
                'onClose':关掉,
            }).渲染()

    def __call__(自身,属性=None):
        '对齐组件调用'
        if 属性 is not None:
            自身.更新(属性)
        return 自身.渲染()
