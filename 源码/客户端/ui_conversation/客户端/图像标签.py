"""把 conversation 词条接到零 cordis 附件原子的标签 props。

对齐上游 `ui-conversation/src/client/image-labels.ts`。公开面仅中文名。
"""

__all__=['图像尺寸文案','附件错误文案','灯箱标签','消息图像标签','拖放覆盖层标签','附件栏标签']#仅中文公开名

def 图像尺寸文案(字节数):#字节→兆字节文案
    """整数原样，否则一位小数，后接 MB。"""
    兆=字节数/(1024*1024)#转兆
    文=str(兆) if 兆==int(兆) else f'{兆:.1f}'#整数或一位
    return f'{文}MB'#文案

def 附件错误文案(翻译,原因,限额=None):#宿主附件拒绝文案
    """按 reason 码分发；用户无法操作则 sendFailed。"""
    if 原因=='MODEL_DOES_NOT_SUPPORT_IMAGES':#模型不支持
        return 翻译('image.modelUnsupported')#文案
    if 原因=='SUBAGENT_IMAGE_UNSUPPORTED':#子智能体
        return 翻译('image.subagentUnsupported')#文案
    if 原因=='IMAGE_TOO_MANY_PIXELS':#像素
        return 翻译('image.tooManyPixels')#文案
    if 原因 in ('INVALID_IMAGE','IMAGE_TYPE_MISMATCH'):#格式
        return 翻译('image.unsupportedType')#文案
    if 原因=='TOO_MANY_IMAGES' and 限额 is not None:#张数
        上限=限额.get('maxImagesPerMessage') if isinstance(限额,dict) else getattr(限额,'maxImagesPerMessage',None)#张数
        return 翻译('image.tooMany',{'count':上限})#上限
    if 原因=='IMAGE_TOO_LARGE' and 限额 is not None:#单张
        上限=限额.get('maxImageBytes') if isinstance(限额,dict) else getattr(限额,'maxImageBytes',None)#字节
        return 翻译('image.fileTooLarge',{'size':图像尺寸文案(上限)})#体积
    if 原因=='IMAGES_TOO_LARGE' and 限额 is not None:#合计
        上限=限额.get('maxMessageImageBytes') if isinstance(限额,dict) else getattr(限额,'maxMessageImageBytes',None)#字节
        return 翻译('image.totalTooLarge',{'size':图像尺寸文案(上限)})#合计
    return 翻译('image.sendFailed',{'reason':原因})#发送失败

def 灯箱标签(翻译):#原图灯箱
    """对话框与关闭。"""
    return {'dialog':翻译('image.preview'),'close':翻译('image.closePreview')}#标签

def 消息图像标签(翻译):#聊天历史图
    """含转发灯箱。"""
    return {#消息图
        'image':翻译('image.label'),#无障碍
        'open':翻译('image.openOriginal'),#打开
        'openNamed':lambda 标签:翻译('image.openOriginalLabel',{'label':标签}),#带名
        'loading':翻译('image.loading'),#加载
        'loadFailed':翻译('image.loadFailed'),#失败
        'lightbox':灯箱标签(翻译),#灯箱
    }#结束

def 拖放覆盖层标签(翻译,接受中,限额=None):#整页拖放
    """不接受只报拦截；接受时可附限额说明。"""
    if not 接受中:#拦截
        return {'title':翻译('image.dropBlocked')}#标题
    说明=None if 限额 is None else 翻译('image.dropDesc',{'count':限额['count'],'size':限额['size']})#说明
    return {'title':翻译('image.dropTitle'),'desc':说明}#接受

def 附件栏标签(翻译):#撰写区草稿图栏
    """分组与翻页。"""
    return {#栏
        'group':翻译('image.pending'),#待发
        'open':翻译('image.openOriginal'),#打开
        'scrollLeft':翻译('image.scrollLeft'),#左
        'scrollRight':翻译('image.scrollRight'),#右
    }#结束
