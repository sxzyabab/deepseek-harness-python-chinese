"""模型请求的确定性缓存图像版本。"""
import hashlib,json,os,uuid#摘要、描述符与原子写
from io import BytesIO#内存缓冲
from ..附件 import 附件错误,图像变体标识,若已中止则抛出#附件缝
from .编码 import WEBP编码力度,图像编码质量阶梯,编码首个不超限,编码阶梯,是否耗尽编码#编码阶梯
from .图像 import 探测图像,检测图像,编码alpha是否兼容#图像事实
from .锐化 import 取锐化#惰性栅格入口
__all__=['请求图像变换版本','请求图像变体标识','读取请求图像文件']#仅中文公开名

请求图像变换版本='request-image-v6'#缓存与上传索引身份版本

def _摘要(值):
    """对字符串或字节计算 sha256 十六进制摘要。"""
    if isinstance(值,str):#字符串
        值=值.encode('utf-8')#转字节
    return hashlib.sha256(值).hexdigest()#十六进制

def _检查正整数(值,名称):
    """检查正整数策略字段。"""
    if isinstance(值,bool) or not isinstance(值,int) or 值<=0:#非法
        raise 附件错误(名称+' must be a positive integer.','INVALID_ATTACHMENT_REF')#拒绝
    return 值#通过

def _验证目标(目标):
    """验证请求图像目标字段。"""
    _检查正整数(目标['width'],'Image request width')#宽
    _检查正整数(目标['height'],'Image request height')#高
    _检查正整数(目标['maxBytes'],'Image request maxBytes')#字节预算

def _描述符(附件引用,目标):
    """构造变体标识覆盖的完整描述符。"""
    return json.dumps({#键序与上游一致
        'transformVersion':请求图像变换版本,
        'attachmentId':附件引用['attachmentId'],
        'targetWidth':目标['width'],
        'targetHeight':目标['height'],
        'encodedByteBudget':目标['maxBytes'],
        'encoding':{
            'webpQualities':list(图像编码质量阶梯),
            'webpEffort':WEBP编码力度,
            'jpegQualities':list(图像编码质量阶梯),
            'order':['alpha:webp','opaque:jpeg'],
            'colourspace':'srgb',
        },
    },ensure_ascii=False,separators=(',',':'),allow_nan=False)#紧凑 JSON

def 请求图像变体标识(附件引用,目标):
    """完整确定性请求变换身份。"""
    return 图像变体标识('sha256:'+_摘要(_描述符(附件引用,目标)))#品牌摘要

def _源管线(已存储):
    """从已验证字节构建 sRGB 源管线。"""
    图像=取锐化().open(BytesIO(已存储['data']))#打开
    if 图像.mode not in ('RGB','RGBA'):#统一到 sRGB 族
        图像=图像.convert('RGBA' if 'A' in 图像.mode else 'RGB')#转换
    return 图像#源图像

def _管线(已存储,目标):
    """只按源长边缩放，让编码器按路由预测的短边推导。"""
    图像=_源管线(已存储)#源
    重采样=取锐化().Resampling.LANCZOS#不放大滤波
    if 已存储['ref']['width']>=已存储['ref']['height']:#长边是宽
        图像.thumbnail((目标['width'],已存储['ref']['height']),重采样)#按宽
    else:#长边是高
        图像.thumbnail((已存储['ref']['width'],目标['height']),重采样)#按高
    return 图像#已缩放

def _创建请求图像(已存储,目标,有alpha):
    """从已存储规范化图像创建请求版本。"""
    if (目标['width']>=已存储['ref']['width']
            and 目标['height']>=已存储['ref']['height']
            and len(已存储['data'])<=目标['maxBytes']):#可直接通过
        return {
            'data':已存储['data'],
            'mediaType':已存储['ref']['mediaType'],
            'width':已存储['ref']['width'],
            'height':已存储['ref']['height'],
        }#原样
    编码结果=编码首个不超限(编码阶梯(_管线(已存储,目标),有alpha),目标['maxBytes'])#阶梯
    return 编码结果['smallest'] if 是否耗尽编码(编码结果) else 编码结果#fitting 或最小

def _缓存路径(根,摘要):
    """请求图像缓存路径。"""
    return os.path.join(根,'request-images',摘要[:2],摘要)#分桶

def _读缓存(路径,目标,期望alpha,信号=None):
    """读取缓存文件并验证仍符合目标与 alpha 事实。"""
    try:#读盘
        文件=open(路径,'rb')#打开
        try:#读
            数据=文件.read()#读字节
        finally:#关
            文件.close()#关掉
    except FileNotFoundError:#无缓存
        return None#未命中
    except OSError:#其他失败
        若已中止则抛出(信号)#取消检
        return None#视为未命中
    已检测=探测图像(数据)#探测
    if (已检测['depth']!='uchar' or 已检测['space']!='srgb'
            or 已检测['width']>目标['width'] or 已检测['height']>目标['height']
            or not 编码alpha是否兼容(期望alpha,已检测)):#不符
        return None#丢弃坏缓存
    return {'data':数据,'mediaType':已检测['mediaType'],'width':已检测['width'],'height':已检测['height'],'hasAlpha':已检测['hasAlpha']}#命中

def _验证请求图像(图像,期望alpha):
    """验证编码请求图像的 8 位 sRGB 元数据。"""
    已检测=检测图像(图像['data'])#全检测
    if (已检测['depth']!='uchar' or 已检测['space']!='srgb'
            or 已检测['width']!=图像['width'] or 已检测['height']!=图像['height']
            or 已检测['mediaType']!=图像['mediaType']
            or not 编码alpha是否兼容(期望alpha,已检测)):#不符
        raise 附件错误('Encoded model-request image does not match its verified 8-bit sRGB metadata.','ATTACHMENT_WRITE_FAILED')#拒绝
    return {**图像,'hasAlpha':已检测['hasAlpha']}#带 alpha 事实

def _写缓存(路径,数据):
    """原子写请求图像缓存文件。"""
    os.makedirs(os.path.dirname(路径),mode=0o700,exist_ok=True)#父目录
    临时=路径+'.'+str(uuid.uuid4())+'.tmp'#随机临时
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
            pass#已不在

def 读取请求图像文件(根,已存储,目标,信号=None):
    """在本地附件缓存根下生成或复用一条请求图像。"""
    若已中止则抛出(信号)#取消优先
    _验证目标(目标)#目标合法
    源=探测图像(已存储['data'])#源事实
    变体标识=请求图像变体标识(已存储['ref'],目标)#变体身份
    摘要=str(变体标识)[len('sha256:'):]#十六进制
    路径=_缓存路径(根,摘要)#缓存路径
    缓存=_读缓存(路径,目标,源['hasAlpha'],信号)#尝试缓存
    新建=_创建请求图像(已存储,目标,源['hasAlpha']) if 缓存 is None else None#未命中则创建
    if 缓存 is not None:#命中
        版本=缓存#用缓存
    elif 新建['data'] is 已存储['data']:#原样通过
        版本={**新建,'hasAlpha':源['hasAlpha']}#带源 alpha
    else:#重编码
        版本=_验证请求图像(新建,源['hasAlpha'])#验证
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
