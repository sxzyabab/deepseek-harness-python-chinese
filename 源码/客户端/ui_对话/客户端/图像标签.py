'会话输入流程拥有的附件错误和限额文案'

from .文案 import 中文,填入

__all__=['图像大小文本','附件错误文本']

def 图像大小文本(字节数):
    '字节数写成用户看见的兆字节，如 10MB、2.5MB'
    兆=字节数/(1024*1024)
    if 兆==int(兆):
        return str(int(兆))+'MB'
    return ('%.1f'%兆)+'MB'

def 附件错误文本(原因,限额=None):
    '宿主拒绝附件时给用户看的中文。不能处理的原因收成一条发送失败'
    if 原因=='MODEL_DOES_NOT_SUPPORT_IMAGES':
        return 中文['image.modelUnsupported']
    if 原因=='FILE_NOT_STAGED':
        return 中文['file.notStaged']
    if 原因=='IMAGE_TOO_MANY_PIXELS':
        return 中文['image.tooManyPixels']
    if 原因=='IMAGE_DIMENSION_TOO_LARGE':
        if 限额 is not None:
            return 填入(中文['image.dimensionTooLarge'],{'size':限额['maxImageDimension']})
    elif 原因=='INVALID_IMAGE' or 原因=='IMAGE_TYPE_MISMATCH':
        return 中文['image.unsupportedType']
    elif 原因=='TOO_MANY_IMAGES':
        if 限额 is not None:
            return 填入(中文['image.tooMany'],{'count':限额['maxImagesPerMessage']})
    elif 原因=='IMAGE_TOO_LARGE':
        if 限额 is not None:
            return 填入(中文['image.fileTooLarge'],{'size':图像大小文本(限额['maxImageBytes'])})
    elif 原因=='IMAGES_TOO_LARGE':
        if 限额 is not None:
            return 填入(中文['image.totalTooLarge'],{'size':图像大小文本(限额['maxMessageImageBytes'])})
    return 填入(中文['image.sendFailed'],{'reason':原因})
