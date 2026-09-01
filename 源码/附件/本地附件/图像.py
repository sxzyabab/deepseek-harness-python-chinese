"""栅格检查：准入时全解码，已验证读取时仅头探测。对齐上游 attachment-local/src/image.ts。"""
from io import BytesIO#字节缓冲
from PIL import Image,ImageOps#图像解码与 EXIF 方向
from ..附件.错误 import 附件错误#附件失败
__all__=['已检测图像字段','编码alpha是否兼容','探测图像','检测图像']#仅中文公开名

已检测图像字段=(#已解码元数据
    'mediaType','width','height','animated','carriesMetadata',
    'depth','space','hasAlpha',
)#字段结束

媒体类型表={#PIL 格式到 MIME
    'PNG':'image/png',
    'JPEG':'image/jpeg',
    'WEBP':'image/webp',
    'GIF':'image/gif',
}#表结束

def _携带保留元数据(图像):#是否携带描述性元数据
    """字节是否携带描述性元数据、色彩配置或方向。"""
    信息=图像.info or {}#附加信息
    return any(键 in 信息 for 键 in ('exif','xmp','icc_profile','photoshop','comment')) or getattr(图像,'text',None) is not None#有元数据

def _样本深度(模式):#映射样本深度
    """把 PIL 模式映射为 Sharp 风格 depth 字符串。"""
    if 模式 in ('I;16','I;16B','I;16L'):#16 位整型
        return 'ushort'#16 位
    return 'uchar'#默认 8 位

def _色彩空间(模式):#映射色彩空间
    """把 PIL 模式映射为 srgb 或原样。"""
    if 模式 in ('RGB','RGBA','L','LA','P'):#常见 sRGB 族
        return 'srgb'#sRGB
    return 模式.lower()#回退原样

def _图像元数据(图像):#从已打开图像提取元数据
    """从已打开 PIL 图像提取内在元数据。"""
    格式=图像.format#容器格式
    媒体类型=媒体类型表.get(格式)#映射 MIME
    if 媒体类型 is None:#不支持
        raise 附件错误('Unsupported or malformed image data.','INVALID_IMAGE')#拒绝
    定向后=ImageOps.exif_transpose(图像)#应用 EXIF 方向
    宽,高=定向后.size#感知宽高
    帧数=getattr(图像,'n_frames',1)#动画帧数
    有alpha='A' in 定向后.mode or (定向后.mode=='P' and 'transparency' in 定向后.info)#alpha 事实
    return {#检测结果
        'mediaType':媒体类型,
        'width':宽,
        'height':高,
        'animated':帧数>1,
        'carriesMetadata':_携带保留元数据(图像),
        'depth':_样本深度(定向后.mode),
        'space':_色彩空间(定向后.mode),
        'hasAlpha':有alpha,
    }#返回

def 编码alpha是否兼容(源有alpha,输出):#编码结果 alpha 是否兼容
    """检查本包编码器产物的 alpha 元数据是否与源事实兼容。"""
    if 源有alpha is None:#源帧未指定
        return True#视为兼容
    if 输出['hasAlpha']==源有alpha:#完全一致
        return True#兼容
    return 源有alpha and (not 输出['hasAlpha']) and 输出['mediaType']=='image/webp'#全不透明 WebP 可省略 alpha 平面

def 探测图像(数据):#仅头探测
    """解析受支持栅格头并返回内在元数据，不解码像素。"""
    try:#打开头
        with Image.open(BytesIO(数据)) as 图像:#头探测
            return _图像元数据(图像)#元数据
    except 附件错误:#已是附件错误
        raise#原样
    except Exception as 错误:#其他失败
        raise 附件错误('Unsupported or malformed image data.','INVALID_IMAGE',{'cause':错误})#包装

def 检测图像(数据,限额=None):#全解码检测
    """全解码受支持栅格并返回内在元数据；可选维度准入。"""
    try:#全解码路径
        with Image.open(BytesIO(数据)) as 图像:#打开
            图像.load()#强制解码像素
            结果=_图像元数据(图像)#元数据
    except 附件错误:#已是附件错误
        raise#原样
    except Exception as 错误:#解码失败
        raise 附件错误('Unsupported or malformed image data.','INVALID_IMAGE',{'cause':错误})#包装
    if 限额 is not None:#维度准入
        if 限额.get('maxPixels') is not None and 结果['width']*结果['height']>限额['maxPixels']:#像素过多
            raise 附件错误('Image exceeds the configured decoded-pixel limit.','IMAGE_TOO_MANY_PIXELS')#拒绝
        if 限额.get('maxDimension') is not None and max(结果['width'],结果['height'])>限额['maxDimension']:#单边过大
            raise 附件错误('Image exceeds the configured per-side pixel limit.','IMAGE_DIMENSION_TOO_LARGE')#拒绝
    return 结果#通过
