"""原生系统消息字段，在物理恢复丢弃该行之前检查。"""
from ..会话格式 import 会话格式错误,是否会话格式json对象,会话格式计数#从会话格式导入

def 记录(值,主语):#记录对象
    """要求值为对象。"""
    if not 是否会话格式json对象(值):#须对象
        raise 会话格式错误('format v4 '+主语+' requires an object')#错误
    return 值#返回

def 字符串(值,主语,非空=False):#断言字符串
    """要求值为字符串，可选非空。"""
    if not isinstance(值,str) or (非空 and len(值)==0):#非法
        raise 会话格式错误('format v4 '+主语+' requires a string'+(' with content' if 非空 else ''))#错误

def 正数(值,主语):#断言正计数
    """要求值为正计数。"""
    if 会话格式计数(值,主语)==0:#须为正
        raise 会话格式错误('format v4 '+主语+' must be positive')#错误

def 图像(值):#断言系统图像附件
    """校验系统图像附件字段。"""
    附件=记录(值,'system image attachment')#附件
    字符串(附件.get('attachmentId'),'system image attachmentId',True)#附件标识
    if 附件.get('mediaType') not in ('image/png','image/jpeg','image/webp','image/gif'):#媒体类型
        raise 会话格式错误('format v4 system image requires a supported mediaType')#错误
    会话格式计数(附件['bytes'],'system image bytes')#字节数
    正数(附件.get('width'),'system image width')#宽
    正数(附件.get('height'),'system image height')#高
    if 'name' in 附件:#可选名
        字符串(附件['name'],'system image name')#名
    if 'originalDimensions' in 附件:#原始尺寸
        原始=记录(附件['originalDimensions'],'system image originalDimensions')#原始
        正数(原始.get('width'),'system image original width')#宽
        正数(原始.get('height'),'system image original height')#高

def 断言v4系统消息字段(行):#断言v4系统消息字段
    """独立于历史消息表示校验系统字段，额外 JSON 字段予以保留。"""
    if not 是否会话格式json对象(行) or 行.get('type')!='system/message':#非系统消息
        return#返回
    数据=记录(行.get('data'),'system/message data')#载荷
    正数(数据.get('turn'),'system/message turn')#回合
    正数(数据.get('step'),'system/message step')#步骤
    消息=记录(数据.get('message'),'system message')#消息
    字符串(消息.get('id'),'system message id',True)#标识
    if 消息.get('role')!='system':#须系统角色
        raise 会话格式错误('format v4 system message requires system role')#错误
    内容=消息.get('content')#内容
    if not isinstance(内容,list):#须数组
        raise 会话格式错误('format v4 system message requires content array')#错误
    for 值 in 内容:#逐块
        块=记录(值,'system content block')#块
        字符串(块.get('type'),'system content type',True)#类型
        类型=块['type']#类型
        if 类型=='text' or 类型=='reasoning':#文本类
            字符串(块.get('text'),'system content text')#文本
        elif 类型=='tool-call':#工具调用
            字符串(块.get('id'),'system tool-call id',True)#标识
            字符串(块.get('name'),'system tool-call name',True)#名
            字符串(块.get('arguments'),'system tool-call arguments')#参数
        elif 类型=='image':#图像
            图像(块.get('attachment'))#附件
        elif 类型=='tool-result':#退役包装
            raise 会话格式错误('format v4 system content rejects retired tool-result wrappers')#错误
