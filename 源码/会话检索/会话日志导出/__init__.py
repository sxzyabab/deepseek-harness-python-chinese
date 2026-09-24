"""登记 export 命令与已认证 ZIP 下载路由。"""
from ...依赖.schemastery import 字典字段,数字字段#配置
from ...交互.命令.标识构造 import 命令定义标识#命令标识
from .归档 import (#归档
    默认会话日志压缩级别,#压缩级别
    冲刷活会话日志,#冲刷
    读会话日志文本,#读日志
    会话日志导出依赖,#依赖
    会话日志zip文件名,#文件名
    流式会话日志zip,#ZIP
    序列化会话日志,#序列化
    会话日志文件名,#文件名常量
    会话日志zip条目,#条目
)#归档
from .路由列表 import 会话日志导出路径#路由

包名='@deepseek-ai/dsh-session-log-export'
名称='session-log-download'
依赖=['commands','connection']

已请求={'kind':'success','text':'已请求下载会话日志。'}
路径拒绝={'kind':'error','text':'Web /export 命令不接受路径。'}
配置模式=字典字段(字典结构={
    'compressionLevel':数字字段(默认值=默认会话日志压缩级别),#DEFLATE 级别
})#配置

__all__=[#公开面
    '包名','名称','依赖','应用','默认','配置',
    '会话日志导出路径','默认会话日志压缩级别','冲刷活会话日志','读会话日志文本',
    '序列化会话日志','会话日志文件名','会话日志导出依赖','会话日志zip条目',
    '会话日志zip文件名','流式会话日志zip',
]#结束

def 处理导出(调用):#命令处理
    """无参数才请求下载。"""
    原始输入=调用['rawInput'] if 'rawInput' in 调用 else ''#输入
    原始=原始输入.strip() if isinstance(原始输入,str) else ''#修剪
    if 原始=='':#无路径
        return 已请求#成功
    return 路径拒绝#拒绝路径

def 会话日志导出响应(上下文,请求,压缩级别):#路由响应
    """读根日志并返回 ZIP 字节或错误状态。"""
    查询=请求.get('query') if isinstance(请求,dict) else {}#查询
    会话标识值=查询.get('sessionId') if isinstance(查询,dict) else None#id
    后代值=查询.get('includeDescendants') if isinstance(查询,dict) else None#后代
    信号=请求.get('signal') if isinstance(请求,dict) else None#取消
    方法=请求.get('method','GET') if isinstance(请求,dict) else 'GET'#方法
    if 会话标识值 is None or 会话标识值=='' or (后代值 not in (None,'true','false')):#非法
        return {'status':400,'body':'missing or invalid sessionId query parameter'}#400
    依赖=会话日志导出依赖(上下文)#服务
    if 依赖['sessionQuery'] is None or 依赖['sessionPersistence'] is None or 依赖['attachments'] is None:#缺服务
        return {'status':500,'body':'session log export is unavailable: missing session-query, session-persistence, or attachments service'}#500
    try:#读根
        冲刷活会话日志(依赖,会话标识值,信号)#冲刷
        根内容=读会话日志文本(依赖['sessionPersistence'],会话标识值,信号)#读
    except BaseException:
        return {'status':500,'body':'session log export failed to read the stored log'}#不回显路径
    if 根内容 is None:#缺席
        return {'status':404,'body':'session not found'}#404
    字节=流式会话日志zip(依赖,根内容,会话标识值,后代值=='true',压缩级别,信号)#ZIP
    头={#响应头
        'content-type':'application/zip',
        'content-disposition':f'attachment; filename="{会话日志zip文件名(会话标识值)}"',
    }#头结束
    if 方法=='HEAD':#HEAD 无体
        return {'status':200,'headers':头,'body':b''}#空体
    return {'status':200,'headers':头,'body':字节}#ZIP

def 应用(上下文,配置值=None):#加载
    """登记仅 Web 的 `/export` 命令与 ZIP 下载路由。"""
    if 配置值 is None:#缺省
        配置值={}#空
    压缩=配置值['compressionLevel'] if 'compressionLevel' in 配置值 else 默认会话日志压缩级别#级别
    def 挂命令():#登记命令
        """登记 export 命令并在拆除时注销。"""
        return 上下文.commands.register({'definitionId':命令定义标识('@deepseek-ai/dsh-session-log-export'),'name':'export','description':'把本会话日志下载为 ZIP 归档','handler':处理导出})
    上下文.副作用(挂命令,'session-log-download: command')#命令
    连接=getattr(上下文,'connection',None)#连接
    if 连接 is not None and hasattr(连接,'fetch') and hasattr(连接.fetch,'register'):#有 fetch
        def 处理请求(请求):#路由处理
            """转发到导出响应。"""
            return 会话日志导出响应(上下文,请求,压缩)#响应
        连接.fetch.register({#登记
            'path':会话日志导出路径,#路径
            'methods':('GET','HEAD'),#方法
            'requestBody':'buffered',#体
            'fetch':处理请求,#处理
        })#登记结束

默认=应用
配置=配置模式
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
