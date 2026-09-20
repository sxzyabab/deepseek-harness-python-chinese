import builtins,json#页面 location / localStorage 与 JSON
import urllib.error#URL 失败
from urllib.parse import urljoin as 拼接URL
import urllib.request as 请求库#默认同步 HTTP
from ....宿主.在应用中打开.共享 import 应用列表路由,打开路由#线路径

__all__=['在应用中打开控制器','在应用中打开错误','快照存储','宿主基址']#仅中文公开名

选择持久化名='dsh.open-in-app.choice'#浏览器侧上次选择键（线协议字面量）

class 在应用中打开错误(Exception):
    """本包在应用中打开失败。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

def 宿主基址():#解析 Host 基址
    """有页面 origin 则用，否则 http://dsh.internal。"""
    源=None#可选源
    try:#宿主可选 location
        页面=builtins.location#页面
        源=页面.origin#origin
        if not isinstance(源,str):#非串
            源=None#清空
    except AttributeError:#非浏览器或无 origin
        源=None#清空
    if 源 is None or 源=='null':#缺源或空源
        return 'http://dsh.internal'#内部基
    return 源#页面源

def 默认同步fetch(网址,初始化=None):#urllib 投递并归一成 dict
    """标准库 HTTP；响应冻结为 status / ok / json / text。"""
    初始化={} if 初始化 is None else 初始化#缺省
    方法=初始化['method'] if 'method' in 初始化 else 'GET'#方法
    头=dict(初始化['headers']) if 'headers' in 初始化 and 初始化['headers'] is not None else {}#头
    正文=初始化['body'] if 'body' in 初始化 else None#正文
    if isinstance(正文,str):#文本体
        正文=正文.encode('utf-8')#编码
    请求=请求库.Request(str(网址),data=正文,headers=头,method=方法)#构造
    try:#发出
        响应=请求库.urlopen(请求)#成功支
        状态=响应.getcode()#状态
        响应正文=响应.read()#正文
    except urllib.error.HTTPError as 错误:#非 2xx 仍有体
        状态=错误.code#状态
        响应正文=错误.read() if hasattr(错误,'read') else b''#正文
    if isinstance(响应正文,bytes):#字节
        文本=响应正文.decode('utf-8')#解码
    else:#已是文本
        文本=响应正文 or ''#串
    def 解析json():#懒解析
        """application/json 体。"""
        return json.loads(文本) if 文本!='' else None#解析
    return {'status':状态,'ok':200<=状态<300,'json':解析json,'text':文本}#dict 响应

def 取本地存储():#可选 localStorage
    """builtins.localStorage；非浏览器则无。"""
    try:#可选
        return builtins.localStorage#存储
    except AttributeError:#未注入
        return None#无

class 快照存储:#本包自持快照存储
    """getSnapshot / subscribe / set；可选按名整值 JSON 持久化。

    对齐 createSnapshotStore 的同步面。不改 客户端/存储；本包自持一份。
    """
    def __init__(自身,初值,持久化名=None):#播种
        """记下初值与可选持久化键。"""
        自身.状态=初值#当前值
        自身.监听者=set()#订阅者
        自身.持久化名=持久化名#键或 None
        自身._可持久化=持久化名 is not None#是否尝试持久化
        if 自身._可持久化:#有名则再水合
            自身._再水合()#读回

    def getSnapshot(自身):#读快照
        """返回当前状态引用。"""
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        """登记变更回调，返回退订。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一):#整值替换
        """写快照、持久化并广播。"""
        自身.状态=下一#替换
        自身._写出()#持久化
        for 回调 in list(自身.监听者):#每个
            回调()#触发

    def _再水合(自身):#从 localStorage 读回
        """失败只关掉持久化，不打断存储。"""
        存储=取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#读
            原始=存储.getItem(自身.持久化名)#读串
            if 原始 is not None:#有值
                自身.状态=json.loads(原始)#整值还原
        except (TypeError,ValueError,AttributeError) as 错误:#再水合失败
            print("快照存储 '"+自身.持久化名+"' 回灌失败:",错误)#诊断
            自身._可持久化=False#关

    def _写出(自身):#写入 localStorage
        """配额/私密模式失败只关掉持久化。"""
        if not 自身._可持久化:#已关
            return#跳过
        存储=取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#写
            存储.setItem(自身.持久化名,json.dumps(自身.状态,ensure_ascii=False,separators=(',',':'),allow_nan=False))#整值
        except (TypeError,ValueError,AttributeError,OSError) as 错误:#写失败
            print("快照存储 '"+自身.持久化名+"' 持久化失败:",错误)#诊断
            自身._可持久化=False#关

class 在应用中打开控制器:#页面生命周期控制器
    """每页一次可用性、持久化选择与启动 POST。"""
    def __init__(自身,取数=None):#注入 HTTP 载体
        """缺省用标准库同步 fetch。"""
        自身.取数=默认同步fetch if 取数 is None else 取数#载体
        自身.应用表=快照存储(None)#已装应用 id；None 表示尚未应答
        自身.选择=快照存储('',持久化名=选择持久化名)#上次选择；空串表示尚未选
        自身._加载已启动=False#每控制器生命只读一次

    def 加载(自身):#读可用性一次
        """并发调用折叠到同一次读取；失败发布空列表（不渲染按钮）。"""
        if 自身._加载已启动:#已启动
            return#共享
        自身._加载已启动=True#标记
        自身._执行可用性读取()#同步读

    def 选定(自身,应用标识):#记住一次挑选
        """目录 id 来自可用性列表。"""
        自身.选择.set(应用标识)#持久化选择

    def 启动(自身,应用标识,路径):#启动已装应用打开工作区目录
        """宿主确认后返回；任失败抛 在应用中打开错误。"""
        体={'app':应用标识,'path':路径}#OpenInAppOpenPayload
        网址=拼接URL(宿主基址().rstrip('/')+'/',打开路由.lstrip('/'))
        响应=自身.取数(网址,{#POST
            'method':'POST',#方法
            'headers':{'content-type':'application/json'},#头
            'body':json.dumps(体,ensure_ascii=False,separators=(',',':'),allow_nan=False),#正文
        })#发出
        if not 响应['ok']:#失败
            raise 在应用中打开错误('open failed: HTTP '+str(响应['status']))#抛错

    def _执行可用性读取(自身):#可用性读取
        """网络失败吞掉：不可达主机等同无应用。"""
        应用列表=[]#缺省空
        try:#读
            网址=拼接URL(宿主基址().rstrip('/')+'/',应用列表路由.lstrip('/'))
            响应=自身.取数(网址,{#GET
                'headers':{'accept':'application/json'},#头
            })#发出
            if 响应['ok']:#成功
                载荷=响应['json']()#OpenInAppAppsPayload
                if isinstance(载荷,dict) and 'apps' in 载荷 and isinstance(载荷['apps'],list):#形态对
                    应用列表=[标识 for 标识 in 载荷['apps'] if isinstance(标识,str)]#只留串
        except (OSError,ValueError,TypeError,KeyError,json.JSONDecodeError,urllib.error.URLError):#网络/解析失败
            应用列表=[]#空列表
        自身.应用表.set(应用列表)#发布
