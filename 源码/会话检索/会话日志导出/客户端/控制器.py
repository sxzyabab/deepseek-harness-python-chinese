'会话页眉按钮和 /export 共用的浏览器下载状态'
from ....客户端.模块.客户端.通告 import 取握手窗口
import re#文件名净化
import urllib.parse#查询串
from ....客户端.存储 import 创建快照存储#对话框状态
from ....客户端.连接.rpc import 同步等待#把页面期约收成同步结果
from ..路由列表 import 会话日志导出路由#文档相对路径


def 会话日志zip文件名(会话标识):
    '把未信任的会话标识收成宿主下载端点使用的文件名'
    段=re.sub(r'[^A-Za-z0-9_-]','_',str(会话标识))#一个安全段
    return 'dsh-session-'+段+'.zip'#固定前缀


def 下载网址(网址,文件名):
    '把宿主下载路由交给浏览器下载管理器，由文档自己的基址解析'
    锚=取握手窗口().document.createElement('a')#临时锚点
    锚.href=网址#文档相对地址
    锚.download=文件名#下载名
    锚.click()#交给下载管理器


def 读取(对象,键):
    '字典用键，页面对象用同名属性'
    if isinstance(对象,dict):#映射
        return 对象.get(键)#键
    return getattr(对象,键)#属性


def 默认请求(输入,初始化):
    '这个网页引擎不再通过浏览器请求宿主'
    raise RuntimeError('这个网页引擎不再通过浏览器请求宿主 '+str(输入))


class 会话日志下载控制器:
    '每个会话至多一个在途下载，并向对话框发布状态'
    def __init__(自身,请求器=默认请求,保存=下载网址):
        '记下 HTTP 载体和保存操作'
        自身.store=创建快照存储({'bySession':{}})#按会话的对话框状态
        自身._活跃={}#会话到中止控制器
        自身._已拆除=False#插件已拆
        自身._请求器=请求器#HEAD
        自身._保存=保存#真正开始下载

    def download(自身,会话标识):
        '下载一棵会话树。同一会话的并发手势共享这一次，拆掉之后的请求忽略'
        if 会话标识 in 自身._活跃:#已经在跑
            return#共享这一次
        if 自身._已拆除:#插件已拆
            return#忽略
        中止=取握手窗口().AbortController()#这一次的取消
        自身._活跃[会话标识]={'abort':中止}#登记
        try:#结束就摘掉
            自身._运行(会话标识,中止.signal)#HEAD 然后保存
        finally:#无论成败
            自身._活跃.pop(会话标识,None)#不再占着

    def dismiss(自身,会话标识):
        '关掉这一会话的对话框，不取消已经交给浏览器的下载'
        当前=自身.store.getSnapshot()['bySession'].get(str(会话标识))#这一条
        if 当前 is None or 当前.get('open') is not True:#没开
            return#无事
        下一=dict(当前)#拷贝
        下一['open']=False#关上
        自身._发布(会话标识,下一)#仍保留状态

    def dispose(自身):
        '中止还在飞的请求'
        自身._已拆除=True#之后的下载忽略
        for 操作 in list(自身._活跃.values()):#当前在途
            操作['abort'].abort()#中止这一次

    def _运行(自身,会话标识,信号):
        '先 HEAD 探测，成功再把同一地址交给浏览器保存'
        自身._发布(会话标识,{'open':True,'status':'downloading','error':None})#准备中
        try:#探测或保存失败都进错误态
            查询=urllib.parse.urlencode([('sessionId',str(会话标识)),('includeDescendants','true')])#含后代和附件
            路由=会话日志导出路由+'?'+查询#文档相对
            响应=同步等待(自身._请求器(路由,{'method':'HEAD','signal':信号}))#探测
            if 读取(响应,'ok') is not True:#HTTP 失败
                细节=''#正文
                try:#读正文失败就当没有细节
                    文本=同步等待(读取(响应,'text')())#响应正文
                except Exception:#读不出来
                    文本=''#空
                if isinstance(文本,str) and 文本!='':#有字
                    细节=' '+文本#附在状态后面
                raise RuntimeError('Export failed: HTTP '+str(读取(响应,'status'))+细节)#失败句
            自身._保存(路由,会话日志zip文件名(会话标识))#交给下载管理器
            打开=自身._仍开着(会话标识)#关掉了就保持关
            自身._发布(会话标识,{'open':打开,'status':'success','error':None})#已开始
        except Exception as 错误:#探测失败或取消
            if 信号.aborted:#拆掉或断开
                return#不改成错误态
            打开=自身._仍开着(会话标识)#关掉了就保持关
            自身._发布(会话标识,{'open':打开,'status':'error','error':str(错误)})#失败

    def _仍开着(自身,会话标识):
        '对话框如果已经被关掉，成功或失败都不要再把它打开'
        当前=自身.store.getSnapshot()['bySession'].get(str(会话标识))#这一条
        if 当前 is None:#还没有条目
            return True#保持打开
        打开=当前.get('open')#当前开合
        if 打开 is None:#空值按仍开
            return True#仍开
        return 打开#原值

    def _发布(自身,会话标识,条目):
        '写入这一会话的对话框状态'
        def 变更(状态):
            '换掉这一条，其余会话保留'
            按会话=dict(状态['bySession'])#拷出
            按会话[str(会话标识)]=条目#这一条
            状态['bySession']=按会话#整表换上
        自身.store.update(变更)#通知订阅


__all__=['会话日志下载控制器','会话日志zip文件名','下载网址']
