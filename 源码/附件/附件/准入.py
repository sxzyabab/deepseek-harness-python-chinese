"""线上 base64 图像上传准入。对齐上游 attachment/src/admission.ts。"""
import base64#base64 编解码
from .错误 import 附件错误#附件失败
__all__=['准入编码图像们']#仅中文公开名

def _解码base64(数据):#解码并拒绝非规范 base64
    """解码一条上传载荷并拒绝非规范 base64 形式。"""
    try:#尝试解码
        解码字节=base64.b64decode(数据,validate=True)#严格 base64
    except Exception:#解码失败
        raise 附件错误('Image upload is not canonical base64.','INVALID_IMAGE_BASE64')#拒绝
    重编码=base64.b64encode(解码字节).decode('ascii')#再编码比对
    if len(数据)==0 or 重编码!=数据:#空或非规范
        raise 附件错误('Image upload is not canonical base64.','INVALID_IMAGE_BASE64')#拒绝
    return 解码字节#原始字节

def _保存输入(图像):#构造单条解码后的存储输入
    """为一条解码上传构造存储输入。"""
    输入={'data':_解码base64(图像['data']),'mediaType':图像['mediaType']}#必填字段
    if 'name' in 图像:#可选显示名
        输入['name']=图像['name']#带上
    return 输入#存储输入

def 准入编码图像们(附件存储,图像们):#准入一批线上图像
    """准入一批线上图像：每条强制规范 base64，再委托批次准入与提交。"""
    return 附件存储.保存图像们([_保存输入(图像) for 图像 in 图像们])#同序提交
