"""共享质量阶梯与惰性候选执行。对齐上游 attachment-local/src/encoding.ts。"""
from io import BytesIO#内存缓冲
__all__=[#仅中文公开名
    '图像编码质量阶梯','WEBP编码力度','编码图像','编码阶梯',
    '是否耗尽编码','编码首个不超限','阶梯编码','附件编码错误',
]#公开面结束

图像编码质量阶梯=(85,75,60)#两编码器共用阶梯
WEBP编码力度=0#固定 WebP 力度

class 附件编码错误(Exception):
    """图像编码候选为空或无法执行。"""

class 阶梯编码:
    """惰性质量阶梯上的一次编码。"""
    def __init__(自身,图像,媒体类型,质量):
        """记下已拷贝的图像、媒体类型与质量。"""
        自身.图像=图像.copy()#候选各自一份
        自身.媒体类型=媒体类型#JPEG 或 WebP
        自身.质量=质量#阶梯质量

    def 运行(自身):
        """编码本档质量。"""
        return 编码(自身.图像,自身.媒体类型,自身.质量)#执行

def 编码(图像,媒体类型,质量):
    """把 PIL 图像编码为 JPEG 或 WebP 并返回字节与尺寸。"""
    缓冲=BytesIO()#内存目标
    if 媒体类型=='image/webp':#带 alpha 走 WebP
        图像.save(缓冲,format='WEBP',quality=质量,method=WEBP编码力度)#WebP
    else:#不透明走 JPEG
        图像.save(缓冲,format='JPEG',quality=质量)#JPEG
    数据=缓冲.getvalue()#取字节
    return {'data':数据,'mediaType':媒体类型,'width':图像.width,'height':图像.height}#完整事实

def 编码阶梯(已准备图像,有alpha):
    """为已准备管线构建惰性质量阶梯：有 alpha 用 WebP，否则 JPEG。"""
    媒体类型='image/webp' if 有alpha else 'image/jpeg'#选编解码器
    return [阶梯编码(已准备图像,媒体类型,质量) for 质量 in 图像编码质量阶梯]#从高到低

def 编码首个不超限(尝试列表,最大字节):
    """按偏好顺序执行编码候选，首个不超限即停，否则保留最小输出。"""
    if len(尝试列表)==0:#至少一个候选
        raise 附件编码错误('image encoding requires at least one candidate')#拒绝
    最小=尝试列表[0].运行()#先跑首选
    if len(最小['data'])<=最大字节:#已 fitting；data 是字节
        return 最小#直接返回
    for 尝试 in 尝试列表[1:]:#其余阶梯
        候选=尝试.运行()#执行
        if len(候选['data'])<=最大字节:#fitting
            return 候选#返回
        if len(候选['data'])<len(最小['data']):#更小
            最小=候选#更新最小
    return {'smallest':最小}#耗尽阶梯

def 是否耗尽编码(结果):
    """惰性编码结果是否在同一尺寸下耗尽全部候选。"""
    return isinstance(结果,dict) and 'smallest' in 结果#耗尽形态
