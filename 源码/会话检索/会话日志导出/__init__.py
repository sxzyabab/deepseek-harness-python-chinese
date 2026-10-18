'登记 Web 的 /export 命令，以及带认证的 ZIP 下载路由'
import urllib.parse#查询串
from ...依赖.schemastery import 字典字段,整数字段#压缩级别
from ...交互.命令.标识构造 import 命令定义标识#命令定义身份
from ...客户端.连接.http桥 import 连接响应#桥认识的响应
from . import (
    归档,#ZIP
    路由列表,#路径
    异常,#本包没有异常类
    客户端,#浏览器半边，不转发里面的类
)

名称='session-log-download'#插件名
依赖=['commands','connection']#命令和连接
默认会话日志压缩级别=归档.默认会话日志压缩级别#缺省级别
冲刷活会话日志=归档.冲刷活会话日志#冲刷
读会话日志文本=归档.读会话日志文本#读日志
序列化会话日志=归档.序列化会话日志#JSONL
会话日志文件名=归档.会话日志文件名#规范文件名
会话日志导出依赖=归档.会话日志导出依赖#服务
会话日志zip条目=归档.会话日志zip条目#条目
会话日志zip文件名=归档.会话日志zip文件名#下载名
流式会话日志zip=归档.流式会话日志zip#ZIP 流
会话日志导出路径=路由列表.会话日志导出路径#绝对路径
配置模式=字典字段(字典结构={'compressionLevel':整数字段(最小=0,最大=9,默认值=默认会话日志压缩级别)})#0 到 9，默认 6

__all__=[#包根导出同目录模块，以及 index 再导出的值。不转发客户端里的类
    '名称','依赖','配置','应用','客户端','异常','归档','路由列表',
    '会话日志导出路径','默认会话日志压缩级别','冲刷活会话日志','读会话日志文本',
    '序列化会话日志','会话日志文件名','会话日志导出依赖','会话日志zip条目',
    '会话日志zip文件名','流式会话日志zip',
]


def 应用(上下文,配置值=None):
    '登记仅 Web 的 /export 命令，以及 GET、HEAD 下载路由'
    if 配置值 is None:#没传配置
        配置值={}#空配置
    压缩=配置值['compressionLevel'] if 'compressionLevel' in 配置值 else 默认会话日志压缩级别#级别

    def 处理导出(调用):
        '没有尾部参数才请求下载。带路径则拒绝'
        原始=调用['rawInput'].strip()#逐字尾部
        if 原始=='':#无路径
            return {'kind':'success','text':'Session log download requested.'}#成功回执
        return {'kind':'error','text':'The Web /export command does not accept a path.'}#不接受路径

    def 登记命令():
        '登记 export，拆除时卸掉'
        return 上下文.commands.登记({#命令
            'definitionId':命令定义标识('@deepseek-ai/dsh-session-log-export'),#定义身份
            'name':'export',#命令名
            'description':'Download this Session log as a ZIP archive',#说明
            'handler':处理导出,#处理
        })

    上下文.副作用(登记命令,'session-log-download: command')#随纤程拆除

    def 处理请求(请求):
        '校验查询，读出根日志，GET 交 ZIP，HEAD 只回状态和头'
        查询={}#最后一次出现的查询值
        for 键,值 in urllib.parse.parse_qsl(urllib.parse.urlsplit(请求.url).query,keep_blank_values=True):#查询
            查询[键]=值#后者覆盖
        会话标识值=查询['sessionId'] if 'sessionId' in 查询 else None#会话
        后代值=查询['includeDescendants'] if 'includeDescendants' in 查询 else None#是否含后代
        if 会话标识值 is None or len(会话标识值)==0 or (后代值 is not None and 后代值!='true' and 后代值!='false'):#查询非法
            return 连接响应('missing or invalid sessionId query parameter',400)#400
        依赖=会话日志导出依赖(上下文)#服务
        if 依赖['sessionQuery'] is None or 依赖['sessionPersistence'] is None or 依赖['attachments'] is None:#缺服务
            return 连接响应('session log export is unavailable: missing session-query, session-persistence, or attachments service',500)#500
        信号=请求.signal#连接断开即中止
        try:#根日志准备失败不把宿主机路径回给浏览器
            冲刷活会话日志(依赖,会话标识值,信号)#活的先冲
            根内容=读会话日志文本(依赖['sessionPersistence'],会话标识值,信号)#读根
        except Exception:#冲刷、打开或读取失败
            信号.throwIfAborted()#取消则继续抛
            return 连接响应('session log export failed to read the stored log',500)#固定句，不回显错误
        if 根内容 is None:#没有这份会话
            return 连接响应('session not found',404)#404
        头={#下载头
            'content-type':'application/zip',
            'content-disposition':'attachment; filename="'+会话日志zip文件名(会话标识值)+'"',
        }
        if 请求.method!='GET':#HEAD 不带正文
            return 连接响应(None,200,头)#状态和头
        响应=连接响应(None,200,头)#先有头
        响应.body=流式会话日志zip(依赖,根内容,会话标识值,后代值=='true',压缩,信号)#迭代时才压缩
        return 响应#GET

    上下文.connection.fetch.register({#精确路由，登记自己挂在纤程上
        'path':会话日志导出路径,#路径
        'methods':['GET','HEAD'],#方法
        'requestBody':'buffered',#正文缓冲
        'fetch':处理请求,#处理
    })


配置=配置模式#配置模式
默认=应用#默认导出
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=默认#框架槽
