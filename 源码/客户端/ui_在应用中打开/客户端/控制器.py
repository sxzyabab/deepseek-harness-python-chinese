import json#页面 location / localStorage 与 JSON
from urllib.parse import urljoin as 拼接URL
from ....基础设施.js特性 import 请求#上游 fetch
from ....基础设施.js特性 import PromiseEX as 期约#中文别名的期约
from ....基础设施.通用工具 import 紧凑json编码,观察者集合
from ....宿主.在应用中打开.共享 import 应用列表路由,打开路由#线路径
from ..异常 import 在应用中打开错误#本包异常

__all__=['在应用中打开控制器','在应用中打开错误','快照存储','宿主基址']#仅中文公开名

选择持久化名='dsh.open-in-app.choice'#浏览器侧上次选择键（线协议字面量）

def 宿主基址():#解析 Host 基址
    '有页面 origin 则用，否则 http://dsh.internal'
    源=None#可选源
    try:#宿主可选 location
        页面=location#页面
        源=页面.origin#origin
        if not isinstance(源,str):#非串
            源=None#清空
    except (NameError,AttributeError):#非浏览器或无 origin
        源=None#清空
    if 源 is None or 源=='null':#缺源或空源
        return 'http://dsh.internal'#内部基
    return 源#页面源

def 接上(产出,成功,失败):#期约或上游 then
    '请求返回的原始期约走 then，本层期约走 然后；已是值则直接成功'
    if hasattr(产出,'然后'):#本层期约
        产出.然后(成功,失败)#接上
        return
    if hasattr(产出,'then'):#上游 fetch 期约
        产出.then(成功,失败)#接上
        return
    成功(产出)#已是值

def 默认同步fetch(网址,初始化=None):#请求并归一成 dict 期约
    '上游 fetch；响应冻结为 status / ok / json / text。返回期约'
    结算=期约()#归一结果
    本次响应=None#响应对象
    def 失败(错误):
        '请求失败'
        结算.拒绝(错误)#拒绝
    def 正文已到(文本):
        '冻成 dict'
        if isinstance(文本,bytes):#字节
            文本=文本.decode('utf-8')#解码
        elif not isinstance(文本,str):#其它
            文本='' if 文本 is None else str(文本)#串
        def 解析json():#懒解析
            'application/json 体'
            return json.loads(文本) if 文本!='' else None#解析
        if isinstance(本次响应,dict):#已是 dict
            状态=本次响应['status']#状态
            是否成功=本次响应['ok']#是否成功
        else:#Response
            状态=本次响应.status#状态
            是否成功=本次响应.ok#是否成功
        结算.解决({'status':状态,'ok':是否成功,'json':解析json,'text':文本})#dict
    def 已响应(响应):
        '再取正文'
        nonlocal 本次响应
        本次响应=响应#记下
        if isinstance(响应,dict) and 'text' in 响应:#已归一
            正文已到(响应['text'])#直接冻
            return
        接上(响应.text(),正文已到,失败)#正文期约
    接上(请求(str(网址),{} if 初始化 is None else 初始化),已响应,失败)#发出
    return 结算#期约

def 取本地存储():#可选 localStorage
    'localStorage；非浏览器则无'
    try:#可选
        return localStorage#存储
    except NameError:#未注入
        return None#无

class 快照存储:#本包自持快照存储
    """getSnapshot / subscribe / set；可选按名整值 JSON 持久化。

    对齐 createSnapshotStore 的同步面。不改 客户端/存储；本包自持一份
    """
    def __init__(自身,初值,持久化名=None):#播种
        '记下初值与可选持久化键'
        自身.状态=初值#当前值
        自身.监听者=观察者集合()#订阅者
        自身.持久化名=持久化名#键或 None
        自身._可持久化=持久化名 is not None#是否尝试持久化
        if 自身._可持久化:#有名则再水合
            自身._再水合()#读回

    def getSnapshot(自身):#读快照
        '返回当前状态引用'
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        '登记变更回调，返回退订'
        return 自身.监听者.订阅(回调)#退订器

    def set(自身,下一):#整值替换
        '写快照、持久化并广播'
        自身.状态=下一#替换
        自身._写出()#持久化
        自身.监听者.通知()#触发

    def _再水合(自身):#从 localStorage 读回
        '失败只关掉持久化，不打断存储'
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
        '配额/私密模式失败只关掉持久化'
        if not 自身._可持久化:#已关
            return#跳过
        存储=取本地存储()#可选
        if 存储 is None:#无
            自身._可持久化=False#关
            return
        try:#写
            存储.setItem(自身.持久化名,紧凑json编码(自身.状态))#整值
        except (TypeError,ValueError,AttributeError,OSError) as 错误:#写失败
            print("快照存储 '"+自身.持久化名+"' 持久化失败:",错误)#诊断
            自身._可持久化=False#关

class 在应用中打开控制器:#页面生命周期控制器
    '每页一次可用性、持久化选择与启动 POST'
    def __init__(自身,取数=None):#注入 HTTP 载体
        '缺省用请求'
        自身.取数=默认同步fetch if 取数 is None else 取数#载体
        自身.应用表=快照存储(None)#已装应用 id；None 表示尚未应答
        自身.选择=快照存储('',持久化名=选择持久化名)#上次选择；空串表示尚未选
        自身._加载已启动=False#每控制器生命只读一次

    def 加载(自身):#读可用性一次
        '并发调用折叠到同一次读取；失败发布空列表（不渲染按钮）'
        if 自身._加载已启动:#已启动
            return#共享
        自身._加载已启动=True#标记
        自身._执行可用性读取()#读

    def 选定(自身,应用标识):#记住一次挑选
        '目录 id 来自可用性列表'
        自身.选择.set(应用标识)#持久化选择

    def 启动(自身,应用标识,路径):#启动已装应用打开工作区目录
        '宿主确认后返回期约；任失败拒绝 在应用中打开错误'
        体={'app':应用标识,'path':路径}#OpenInAppOpenPayload
        网址=拼接URL(宿主基址().rstrip('/')+'/',打开路由.lstrip('/'))
        结算=期约()#本次启动
        def 失败(错误):
            '归一成在应用中打开错误'
            if isinstance(错误,在应用中打开错误):#已是
                结算.拒绝(错误)#拒绝
                return
            结算.拒绝(在应用中打开错误(str(错误)))#抛错
        def 已响应(响应):
            '非成功状态则拒绝'
            if not 响应['ok']:#失败
                失败(在应用中打开错误('open failed: HTTP '+str(响应['status'])))#抛错
                return
            结算.解决(None)#确认
        接上(自身.取数(网址,{#POST
            'method':'POST',#方法
            'headers':{'content-type':'application/json'},#头
            'body':紧凑json编码(体),#正文
        }),已响应,失败)#发出
        return 结算#期约

    def _执行可用性读取(自身):#可用性读取
        '网络失败吞掉：不可达主机等同无应用'
        网址=拼接URL(宿主基址().rstrip('/')+'/',应用列表路由.lstrip('/'))
        def 发布(应用列表):
            '发布列表'
            自身.应用表.set(应用列表)#发布
        def 失败(_错误):
            '不可达当无应用'
            发布([])#空列表
        def 已响应(响应):
            '成功则留字符串 id'
            if not 响应['ok']:#失败
                发布([])#空列表
                return
            try:#解析
                载荷=响应['json']()#OpenInAppAppsPayload
                if isinstance(载荷,dict) and 'apps' in 载荷 and isinstance(载荷['apps'],list):#形态对
                    发布([标识 for 标识 in 载荷['apps'] if isinstance(标识,str)])#只留串
                    return
            except (ValueError,TypeError,KeyError,json.JSONDecodeError):#解析失败
                pass#当无应用
            发布([])#空列表
        try:#读
            接上(自身.取数(网址,{#GET
                'headers':{'accept':'application/json'},#头
            }),已响应,失败)#发出
        except Exception:#取数同步失败
            发布([])#空列表
