'线上 base64 图像上传准入'
from ...基础设施.通用工具.序列化编码 import 严格解码base64
from .异常 import 附件错误#附件失败
__all__=['准入编码图像批次']#仅中文公开名

def _解码base64(数据):#解码并拒绝非规范 base64
    '解码一条上传载荷并拒绝非规范 base64 形式'
    try:#尝试解码
        return 严格解码base64(数据)#规范 base64
    except (ValueError,TypeError):
        raise 附件错误('Image upload is not canonical base64.','INVALID_IMAGE_BASE64')

def _保存输入(图像):#构造单条解码后的存储输入
    '为一条解码上传构造存储输入'
    输入={'data':_解码base64(图像['data']),'mediaType':图像['mediaType']}#必填字段
    if 'name' in 图像:#可选显示名
        输入['name']=图像['name']#带上
    return 输入#存储输入

def 准入编码图像批次(附件存储,图像列表):#准入一批线上图像
    '准入一批线上图像：每条强制规范 base64，再委托批次准入与提交'
    return 附件存储.保存图像批次([_保存输入(图像) for 图像 in 图像列表])#同序提交
