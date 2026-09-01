"""模型请求的确定性缓存图像版本。对齐上游 attachment-local/src/request-image.ts。"""
import hashlib,json,os,uuid#摘要、描述符与原子写
from io import BytesIO#内存缓冲
from PIL import Image#图像变换
from ..附件 import 附件错误,图像变体标识,请求图像尺寸,若已中止则抛出#附件缝
from .编码 import WEBP编码力度,图像编码质量阶梯,编码首个不超限,编码阶梯,是否耗尽编码#编码阶梯
from .图像 import 探测图像,检测图像,编码alpha是否兼容#图像事实
__all__=['请求图像变换版本','请求图像变体标识','读取请求图像文件']#仅中文公开名

请求图像变换版本='request-image-v5'#缓存与上传索引身份版本

def _摘要(值):#sha256 十六进制
    """对字符串或字节计算 sha256 十六进制摘要。"""
    if isinstance(值,str):#字符串
        值=值.encode('utf-8')#转字节
    return hashlib.sha256(值).hexdigest()#十六进制

def _检查正整数(值,名称):#正整数策略字段
    """检查正整数策略字段。"""
    if not isinstance(值,int) or 值<=0:#非法
        raise 附件错误(f'{名称} must be a positive integer.','INVALID_ATTACHMENT_REF')#拒绝
    return 值#通过

def _验证策略(策略):#验证请求策略
    """验证请求图像策略字段。"""
    _检查正整数(策略['maxPixels'],'Image request maxPixels')#像素预算
    _检查正整数(策略['maxBytes'],'Image request maxBytes')#字节预算

def _描述符(附件引用,策略):#确定性描述符 JSON
    """构造变体标识覆盖的完整描述符。"""
    return json.dumps({#稳定键序由 sort_keys 保证
        'transformVersion':请求图像变换版本,
        'attachmentId':附件引用['attachmentId'],
        'routePixelBudget':策略['maxPixels'],
        'encodedByteBudget':策略['maxBytes'],
        'encoding':{
            'webpQualities':list(图像编码质量阶梯),
            'webpEffort':WEBP编码力度,
            'jpegQualities':list(图像编码质量阶梯),
            'order':['alpha:webp','opaque:jpeg'],
            'colourspace':'srgb',
        },
    },sort_keys=True,separators=(',',':'))#紧凑 JSON

def 请求图像变体标识(附件引用,策略):#确定性变体标识
    """完整确定性请求变换身份。"""
    return 图像变体标识(f"sha256:{_摘要(_描述符(附件引用,策略))}")#品牌摘要

def _源管线(已存储):#sRGB 源管线
    """从已验证字节构建 sRGB 源管线。"""
    图像=Image.open(BytesIO(已存储['data']))#打开
    if 图像.mode not in ('RGB','RGBA'):#统一到 sRGB 族
        图像=图像.convert('RGBA' if 'A' in 图像.mode else 'RGB')#转换
    return 图像#源图像

def _管线(已存储,宽,高):#带缩放的请求管线
    """在源管线上按内贴缩放。"""
    图像=_源管线(已存储)#源
    图像.thumbnail((宽,高),Image.Resampling.LANCZOS)#内贴不放大
    return 图像#已缩放

def _创建请求图像(已存储,策略,有alpha):#生成请求版本
    """从已存储规范化图像创建请求版本。"""
    尺寸=请求图像尺寸(已存储['ref']['width'],已存储['ref']['height'],策略['maxPixels'])#投影尺寸
    if (尺寸['width']==已存储['ref']['width'] and 尺寸['height']==已存储['ref']['height']
        and len(已存储['data'])<=策略['maxBytes']):#可直接通过
        return {
            'data':已存储['data'],
            'mediaType':已存储['ref']['mediaType'],
            'width':已存储['ref']['width'],
            'height':已存储['ref']['height'],
        }#原样
    编码结果=编码首个不超限(编码阶梯(_管线(已存储,尺寸['width'],尺寸['height']),有alpha),策略['maxBytes'])#阶梯
    return 编码结果['smallest'] if 是否耗尽编码(编码结果) else 编码结果#fitting 或最小

def _缓存路径(根,摘要):#缓存文件路径
    """请求图像缓存路径。"""
    return os.path.join(根,'request-images',摘要[:2],摘要)#分桶

def _读缓存(路径,已存储,策略,期望alpha,信号=None):#读缓存并验证
    """读取缓存文件并验证仍符合策略与 alpha 事实。"""
    try:#读盘
        with open(路径,'rb') as 文件:#打开
            数据=文件.read()#读字节
    except FileNotFoundError:#无缓存
        return None#未命中
    except OSError:#其他失败
        若已中止则抛出(信号)#取消检
        return None#视为未命中
    已检测=探测图像(数据)#探测
    上限=请求图像尺寸(已存储['ref']['width'],已存储['ref']['height'],策略['maxPixels'])#上限尺寸
    if (已检测['depth']!='uchar' or 已检测['space']!='srgb'
        or 已检测['width']>上限['width'] or 已检测['height']>上限['height']
        or not 编码alpha是否兼容(期望alpha,已检测)):#不符
        return None#丢弃坏缓存
    return {'data':数据,'mediaType':已检测['mediaType'],'width':已检测['width'],'height':已检测['height'],'hasAlpha':已检测['hasAlpha']}#命中

def _验证请求图像(图像,期望alpha):#验证编码请求事实
    """验证编码请求图像的 8 位 sRGB 元数据。"""
    已检测=检测图像(图像['data'])#全检测
    if (已检测['depth']!='uchar' or 已检测['space']!='srgb'
        or 已检测['width']!=图像['width'] or 已检测['height']!=图像['height']
        or 已检测['mediaType']!=图像['mediaType']
        or not 编码alpha是否兼容(期望alpha,已检测)):#不符
        raise 附件错误('Encoded model-request image does not match its verified 8-bit sRGB metadata.','ATTACHMENT_WRITE_FAILED')#拒绝
    return {**图像,'hasAlpha':已检测['hasAlpha']}#带 alpha 事实

def _写缓存(路径,数据):#原子写缓存
    """原子写请求图像缓存文件。"""
    os.makedirs(os.path.dirname(路径),mode=0o700,exist_ok=True)#父目录
    临时=f"{路径}.{uuid.uuid4()}.tmp"#随机临时
    try:#写临时再改名
        描述符=os.open(临时,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)#独占创建
        try:#写入
            os.write(描述符,数据)#写完整
        finally:#关闭
            os.close(描述符)#关掉
        os.replace(临时,路径)#原子替换
    finally:#清理临时
        try:#删临时
            os.unlink(临时)#尽力删
        except OSError:#可能已搬走
            pass#吞掉

def 读取请求图像文件(根,已存储,策略,信号=None):#生成或复用请求图像
    """在本地附件根下生成或复用一条请求图像。"""
    若已中止则抛出(信号)#取消优先
    _验证策略(策略)#策略合法
    源=探测图像(已存储['data'])#源事实
    变体标识=请求图像变体标识(已存储['ref'],策略)#变体身份
    摘要=str(变体标识)[len('sha256:'):]#十六进制
    路径=_缓存路径(根,摘要)#缓存路径
    缓存=_读缓存(路径,已存储,策略,源['hasAlpha'],信号)#尝试缓存
    新建=_创建请求图像(已存储,策略,源['hasAlpha']) if 缓存 is None else None#未命中则创建
    版本=缓存 if 缓存 is not None else ({**新建,'hasAlpha':源['hasAlpha']} if 新建['data'] is 已存储['data'] else _验证请求图像(新建,源['hasAlpha']))#选用
    若已中止则抛出(信号)#变换后再检
    if 缓存 is None and 版本['data'] is not 已存储['data']:#需写缓存
        _写缓存(路径,版本['data'])#落盘
    return {#请求附件
        'variantId':变体标识,
        'attachment':已存储['ref'],
        'data':版本['data'],
        'mediaType':版本['mediaType'],
        'bytes':len(版本['data']),
        'width':版本['width'],
        'height':版本['height'],
        'depth':'uchar',
        'space':'srgb',
        'hasAlpha':版本['hasAlpha'],
    }#返回
