"""确定性提供者无关图像规范化。对齐上游 attachment-local/src/normalization.ts。"""
from io import BytesIO#内存缓冲
from PIL import Image,ImageOps#图像处理
from ..附件.错误 import 附件错误#附件失败
from ..附件.请求投影 import 请求图像尺寸#投影几何
from .编码 import 编码首个不超限,编码阶梯,是否耗尽编码#质量阶梯
from .图像 import 检测图像,编码alpha是否兼容#检测与 alpha 兼容
__all__=['规范化策略字段','规范化图像字段','能否直通规范化','规范化图像']#仅中文公开名

规范化策略字段=('maxPixels','maxDimension','maxBytes')#规范化策略
规范化图像字段=('data','mediaType','width','height')#规范化输出

def 能否直通规范化(已检测,字节数,策略):#源是否已满足规范化要求
    """判断字节是否已满足规范化要求，可原样通过。"""
    return (已检测['mediaType']!='image/gif'
        and not 已检测['animated']
        and not 已检测['carriesMetadata']
        and 已检测['depth']=='uchar'
        and 已检测['space']=='srgb'
        and 字节数<=策略['maxBytes']
        and 已检测['width']*已检测['height']<=策略['maxPixels']
        and max(已检测['width'],已检测['height'])<=策略['maxDimension'])#全部满足

def _验证规范化图像(图像,期望alpha):#断言规范化输出事实
    """断言规范化输出是单帧 8 位 sRGB 且事实匹配。"""
    已检测=检测图像(图像['data'])#再检测
    if (已检测['mediaType']!=图像['mediaType']
        or 已检测['width']!=图像['width']
        or 已检测['height']!=图像['height']
        or 已检测['animated']
        or 已检测['carriesMetadata']
        or 已检测['depth']!='uchar'
        or 已检测['space']!='srgb'
        or not 编码alpha是否兼容(期望alpha,已检测)):#事实不符
        raise 附件错误('Image normalization did not produce a single-frame 8-bit sRGB image with matching metadata.','ATTACHMENT_WRITE_FAILED')#拒绝
    return 图像#通过

def _初始尺寸(已检测,策略):#总像素预算后再套长边上限
    """在总像素预算下计算尺寸，再应用长边上限且保持纵横比。"""
    预算=请求图像尺寸(已检测['width'],已检测['height'],策略['maxPixels'])#总像素预算
    长边=max(预算['width'],预算['height'])#当前长边
    if 长边<=策略['maxDimension']:#未超长边
        return 预算#直接返回
    缩放=策略['maxDimension']/长边#长边缩放
    return {
        'width':max(1,int(预算['width']*缩放)),
        'height':max(1,int(预算['height']*缩放)),
    }#缩放后尺寸

def _准备管线(数据,宽,高):#固定尺寸 sRGB 管线
    """从提交字节构建固定尺寸、已定向、无元数据的 sRGB 管线。"""
    with Image.open(BytesIO(数据)) as 源:#打开
        定向=ImageOps.exif_transpose(源)#应用方向
        if 定向.mode not in ('RGB','RGBA'):#统一到 sRGB 族
            定向=定向.convert('RGBA' if 'A' in 定向.mode else 'RGB')#转换
        定向.thumbnail((宽,高),Image.Resampling.LANCZOS)#内贴缩放且不放大
        return 定向#已准备图像

def 规范化图像(数据,已检测,策略):#产出持久规范化版本
    """产出已验证的提供者无关规范化字节与元数据。"""
    if 能否直通规范化(已检测,len(数据),策略):#可原样通过
        return {'data':数据,'mediaType':已检测['mediaType'],'width':已检测['width'],'height':已检测['height']}#直通
    try:#重编码路径
        尺寸=_初始尺寸(已检测,策略)#目标尺寸
        已准备=_准备管线(数据,尺寸['width'],尺寸['height'])#准备管线
        编码结果=编码首个不超限(编码阶梯(已准备,已检测['hasAlpha']),策略['maxBytes'])#阶梯编码
        选中=编码结果['smallest'] if 是否耗尽编码(编码结果) else 编码结果#取 fitting 或最小
        期望alpha=None if 已检测['mediaType']=='image/gif' else 已检测['hasAlpha']#GIF 不约束 alpha
        return _验证规范化图像(选中,期望alpha)#验证后返回
    except 附件错误:#已是附件错误
        raise#原样
    except Exception as 错误:#转换失败
        if 已检测['mediaType']=='image/png' and 已检测['depth']!='uchar':#高位深 PNG
            源描述=f"{('16-bit' if 已检测['depth']=='ushort' else 已检测['depth'])} PNG"#描述
        else:#其他格式
            源描述=f"{已检测['depth']} {已检测['mediaType'].split('/',1)[1].upper()}"#描述
        raise 附件错误(f'The {源描述} could not be converted to the normalized 8-bit sRGB form.','ATTACHMENT_WRITE_FAILED',{'cause':错误})#包装
