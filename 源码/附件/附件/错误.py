"""附件失败类。对齐上游 attachment/src/error.ts。"""
__all__=['图像准入错误码集合','附件错误码','附件错误','是否图像准入错误']#仅中文公开名

图像准入错误码集合=frozenset([#图像准入阶段可纠正失败码
    'TOO_MANY_IMAGES',#图像过多
    'IMAGES_TOO_LARGE',#批次字节过大
    'UNSUPPORTED_IMAGE_TYPE',#不支持的媒体类型
    'INVALID_IMAGE_BASE64',#非规范 base64
    'INVALID_IMAGE',#无效图像
    'IMAGE_TYPE_MISMATCH',#声明类型与字节不符
    'IMAGE_TOO_LARGE',#单图字节过大
    'IMAGE_TOO_MANY_PIXELS',#解码像素过多
    'IMAGE_DIMENSION_TOO_LARGE',#单边尺寸过大
])#集合结束

附件错误码=图像准入错误码集合|frozenset([#全部附件错误码
    'INVALID_ATTACHMENT_REF',#无效附件引用
    'ATTACHMENT_CORRUPT',#附件损坏
    'ATTACHMENT_WRITE_FAILED',#写入失败
    'ATTACHMENT_NOT_FOUND',#对象缺失
    'ATTACHMENT_READ_FAILED',#读取失败
    'ATTACHMENT_PROJECTION_UNSUPPORTED',#不支持请求投影
])#联合结束

class 附件错误(Exception):#稳定协议路由失败
    """适合宿主 RPC 错误映射的稳定失败。故意不继承 HarnessError 基类以避免循环依赖；消费方只按 code 路由。"""
    def __init__(自身,消息,码,选项=None):#构造带码失败
        super().__init__(消息)#人类可读描述
        if 选项 is not None and 'cause' in 选项:#链式原因
            自身.__cause__=选项['cause']#挂上原因
        自身.name='AttachmentError'#错误名
        自身.code=码#稳定机器路由码

def 是否图像准入错误(错误):#是否图像准入可纠正失败
    """区分图像准入可纠正失败与存储故障。"""
    return isinstance(错误,Exception) and hasattr(错误,'code') and isinstance(错误.code,str) and 错误.code in 图像准入错误码集合#成员检测
