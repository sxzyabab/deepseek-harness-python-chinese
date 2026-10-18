'浏览器、桌面和已认证 Node 连接选用的物理套接字'
from ...模块.客户端.通告 import 取握手窗口
import urllib.parse#把逻辑路径接到基址上
from pywebbridge.基础 import undefined as 未定义#页面上没有该值
from ..异常 import 连接错误#文档外没有基址


def 浏览器套接字(地址):
    '这个网页引擎不再通过浏览器打开套接字'
    raise 连接错误('connection: 这个网页引擎不再通过浏览器打开套接字 '+str(地址))#拒绝


def 打开连接套接字(路径,工厂=None,基址=None):
    '按显式宿主基址或页面文档基址打开套接字'
    if 工厂 is None:#没给工厂
        工厂=浏览器套接字#浏览器 API
    if 基址 is None:#没给基址
        窗口=取握手窗口()#页面
        读到=窗口.document['baseURI']#文档基址
        if 读到 is 未定义 or 读到 is None or 读到 is Ellipsis:#没有文档
            基址=None#缺失
        else:#有
            基址=读到#基址
    if 基址 is None:#文档外必须自己给
        raise 连接错误('connection: WebSocket carrier requires streamBaseUrl outside a document')#拒绝
    合并=urllib.parse.urljoin(基址,路径[1:])#去掉前导斜杠再相对解析
    拆=urllib.parse.urlsplit(合并)#拆开
    方案='wss' if 拆.scheme=='https' else 'ws'#https 升到 wss，其余升到 ws
    地址=urllib.parse.urlunsplit((方案,拆.netloc,拆.path,拆.query,拆.fragment))#套接字地址
    return 工厂(地址)#交给工厂
