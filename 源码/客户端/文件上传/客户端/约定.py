"""按一个 Session 身份寻址的浏览器上传服务约定。

对齐上游 `file-upload/src/client/contract.ts`。
"""
__all__=['文件上传进度字段','文件上传服务协议']#仅中文公开名

文件上传进度字段=('loaded','total')#已消费字节与可选总量

class 文件上传服务协议:#文件上传服务协议锚点
    """按一个 Session 身份寻址的浏览器上传服务。"""
    available=False#是否可用

    def 上传(自身,会话标识,数据,名=None,信号=None,进度回调=None):#上传并返回结果
        """为一个 Session 存储一个文件。"""
        raise NotImplementedError('FileUploadService.upload')#子类实现
