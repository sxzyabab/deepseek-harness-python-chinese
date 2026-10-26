'一次插件激活里的文件传递。调用方只拿到已经备好的起拖和释放'
import hashlib
import threading
import urllib.request
from uuid import uuid4 as 随机标识
from ....基础设施.js特性.promise import PromiseEX
from ....工具.文件拖拽 import 文件拖拽令牌类型,解析拖拽文件名
from ...模块.客户端.通告 import 取握手窗口

__all__=['文件拖拽令牌类型','解析拖拽文件名','文件传递','中止信号','等远程']

class 中止信号:
    '一次准备可以被调用方取消'
    def __init__(自身):
        '一开始没有取消'
        自身.已中止=False
        自身.原因=None
        自身.监听=[]

    def 中止(自身,原因=None):
        '只生效一次，并通知监听'
        if 自身.已中止:
            return
        自身.已中止=True
        自身.原因=原因
        for 回调 in list(自身.监听):
            回调()

    def 若已中止则抛(自身):
        '已取消则拒绝继续准备'
        if 自身.已中止:
            raise RuntimeError('The operation was aborted')

    def addEventListener(自身,种类,回调,选项=None):
        '只接 abort。已经取消则立刻回调'
        if 种类!='abort':
            return
        if 自身.已中止:
            回调()
            return
        自身.监听.append(回调)

    def removeEventListener(自身,种类,回调):
        '卸掉一次 abort 监听'
        if 种类=='abort' and 回调 in 自身.监听:
            自身.监听.remove(回调)

class 外来中止:
    '包住调用方传来的中止信号'
    def __init__(自身,信号):
        '记下原信号'
        自身.信号=信号

    def 若已中止则抛(自身):
        '原信号已取消则拒绝'
        已中止=getattr(自身.信号,'aborted',False) or getattr(自身.信号,'已中止',False)
        if 已中止:
            raise RuntimeError('The operation was aborted')

    def addEventListener(自身,种类,回调,选项=None):
        '转给原信号'
        if hasattr(自身.信号,'addEventListener'):
            自身.信号.addEventListener(种类,回调,选项)

    def removeEventListener(自身,种类,回调):
        '从原信号卸掉'
        if hasattr(自身.信号,'removeEventListener'):
            自身.信号.removeEventListener(种类,回调)

def 包中止(信号):
    '没有信号时给一个不会自己取消的空信号'
    if 信号 is None:
        return 中止信号()
    if isinstance(信号,中止信号):
        return 信号
    return 外来中止(信号)

def 合并中止(甲,乙):
    '任一侧取消，合并后的信号也取消'
    合并=中止信号()
    def 挂(信号):
        '一侧已取消则立刻取消合并信号'
        包装=包中止(信号)
        def 回调():
            '跟着这一侧取消'
            合并.中止()
        try:
            包装.若已中止则抛()
        except RuntimeError:
            合并.中止()
            return
        包装.addEventListener('abort',回调)
    挂(甲)
    挂(乙)
    return 合并

def 等远程(值):
    '期约结算后再往下走。普通值原样返回'
    if 值 is None:
        return None
    然后=None
    if hasattr(值,'然后'):
        然后=值.然后
    elif hasattr(值,'then'):
        然后=值.then
    if 然后 is None:
        return 值
    盒={'值':None,'错误':None,'完成':threading.Event()}
    def 成功(数据=None):
        '记下兑现'
        盒['值']=数据
        盒['完成'].set()
    def 失败(错误=None):
        '记下拒绝'
        盒['错误']=错误
        盒['完成'].set()
    然后(成功,失败)
    盒['完成'].wait()
    if 盒['错误'] is not None:
        raise 盒['错误']
    return 盒['值']

def 读字节(内容):
    'Blob、字节或带 arrayBuffer 的对象都收成 bytes'
    if isinstance(内容,(bytes,bytearray)):
        return bytes(内容)
    if hasattr(内容,'arrayBuffer'):
        缓冲=等远程(内容.arrayBuffer())
        if isinstance(缓冲,(bytes,bytearray)):
            return bytes(缓冲)
        if hasattr(缓冲,'tobytes'):
            return 缓冲.tobytes()
        return bytes(缓冲)
    if hasattr(内容,'read'):
        return 内容.read()
    raise RuntimeError('File read failed')

class 简易文件:
    '当前页没有 File 时，自己保住字节、名字和媒体类型'
    def __init__(自身,数据,名称,媒体):
        '记下字节'
        自身.数据=数据
        自身.name=名称
        自身.type=媒体
        自身.size=len(数据)

    def arrayBuffer(自身):
        '把字节交回去'
        return 自身.数据

def 造文件(数据,名称,媒体):
    '优先用页面的 File。没有则用 Blob，再没有则用简易文件'
    窗口=取握手窗口()
    文件类=getattr(窗口,'File',None)
    if 文件类 is not None:
        return 文件类([数据],名称,{'type':媒体})
    二进制类=getattr(窗口,'Blob',None)
    if 二进制类 is not None:
        体=二进制类([数据],{'type':媒体})
        体.name=名称
        return 体
    return 简易文件(数据,名称,媒体)

class 文件传递:
    '这一次激活拥有的浏览器传递。源节点卸掉之后，拖放结束仍由这里收口'
    def __init__(自身,桌面,报告失败):
        '桌面桥可以没有。失败回调由插件词典提供'
        自身.桌面=桌面
        自身.报告失败=报告失败
        自身.活动=None
        自身.已备=set()
        自身.已拆除=False
        自身.寿命=中止信号()

    def 读取(自身,传递):
        '只有当前令牌对得上才交还原文件'
        活动=自身.活动
        if 活动 is None:
            return None
        if 活动['token']==传递.getData(文件拖拽令牌类型):
            return 活动['file']
        return None

    def 准备(自身,来源,信号):
        '准备字节，或向桌面借用已授权的原文件。返回可以起拖和释放的操作'
        合并=合并中止(信号,自身.寿命)
        def 执行(解决,拒绝):
            '在线程里准备，结算后交给期约'
            def 跑():
                '准备失败则拒绝期约'
                try:
                    解决(自身.备好(来源,合并))
                except Exception as 错误:
                    拒绝(错误)
            线=threading.Thread(target=跑)
            线.start()
        return PromiseEX(执行)

    def 准备原生(自身,桌面,源,信号):
        '取消会传到这一次原生请求'
        信号.若已中止则抛()
        请求标识=str(随机标识())
        def 取消():
            '调用方取消则通知桌面'
            桌面.cancel(请求标识)
        信号.addEventListener('abort',取消)
        try:
            return 等远程(桌面.prepare(源,请求标识))
        finally:
            信号.removeEventListener('abort',取消)

    def 备好(自身,来源,信号):
        '浏览器直接读内容。桌面先试借用，借用失败再用字节'
        信号.若已中止则抛()
        桌面=自身.桌面
        if 桌面 is None:
            文件=自身.读来源(来源,信号)
            信号.若已中止则抛()
            return 自身.浏览器(文件)
        句柄=None
        try:
            if 来源.get('resourceAddress') is not None:
                字节=None
                if 来源.get('kind')=='blob':
                    字节=读字节(来源['blob'])
                摘要=None if 字节 is None else hashlib.sha256(字节).hexdigest()
                信号.若已中止则抛()
                try:
                    源={
                        'kind':'resource',
                        'address':来源['resourceAddress'],
                        'name':来源.get('name'),
                        'mediaType':来源.get('mediaType'),
                        'outputExtension':来源.get('outputExtension'),
                    }
                    if 摘要 is not None:
                        源['sha256']=摘要
                    if 来源.get('kind')=='blob':
                        大小=getattr(来源['blob'],'size',None)
                        if 大小 is None and 字节 is not None:
                            大小=len(字节)
                        if 大小 is not None:
                            源['size']=大小
                    句柄=自身.准备原生(桌面,源,信号)
                except Exception as 借用错误:
                    借用错误=None#借用可选，取消不回退，其余仍用传入内容
                    信号.若已中止则抛()
                    句柄=None
            if 句柄 is None:
                文件=自身.读来源(来源,信号)
                字节=读字节(文件)
                句柄=自身.准备原生(桌面,{
                    'kind':'bytes',
                    'bytes':字节,
                    'name':getattr(文件,'name','file'),
                    'mediaType':getattr(文件,'type',''),
                    'outputExtension':来源.get('outputExtension'),
                },信号)
                if 句柄 is None:
                    raise RuntimeError('File preparation unavailable')
            信号.若已中止则抛()
            return 自身.原生(桌面,句柄)
        except Exception:
            if 句柄 is not None:
                桌面.release(句柄)
            raise

    def 读来源(自身,来源,信号):
        '网址先取回字节。Blob 直接用。名字按导出规则收干净'
        信号.若已中止则抛()
        if 来源.get('kind')=='url':
            数据,类型=自身.读网址(来源['url'],信号)
        else:
            数据=读字节(来源['blob'])
            类型=getattr(来源['blob'],'type','') or ''
        信号.若已中止则抛()
        媒体=来源.get('mediaType') or 类型
        名称=解析拖拽文件名({
            'name':来源.get('name'),
            'mediaType':媒体,
            'outputExtension':来源.get('outputExtension'),
        })
        return 造文件(数据,名称,媒体)

    def 读网址(自身,网址,信号):
        '不带引用页。非成功状态拒绝'
        信号.若已中止则抛()
        请求=urllib.request.Request(网址,method='GET')
        响应=urllib.request.urlopen(请求)
        try:
            状态=getattr(响应,'status',None)
            if 状态 is None:
                状态=响应.getcode()
            if 状态<200 or 状态>=300:
                raise RuntimeError('File read failed')
            数据=响应.read()
            类型=''
            头=getattr(响应,'headers',None)
            if 头 is not None:
                类型=头.get('Content-Type') or ''
        finally:
            响应.close()
        信号.若已中止则抛()
        return 数据,类型

    def 原生(自身,桌面,句柄):
        '起拖交给桌面。没开始就释放；已经开始则等启动结算后再释放'
        盒={'启动':None}
        def 释放():
            '这一次准备只释放一次'
            if 释放 not in 自身.已备:
                return
            自身.已备.discard(释放)
            if 盒['启动'] is None:
                桌面.release(句柄)
                return
            def 之后(值=None):
                '启动结算后再放掉句柄'
                桌面.release(句柄)
            期=盒['启动']
            if hasattr(期,'然后'):
                期.然后(之后,之后)
            elif hasattr(期,'then'):
                期.then(之后,之后)
            else:
                桌面.release(句柄)
        自身.已备.add(释放)
        def 启动(传递=None,源节点=None):
            '桌面接管拖放，浏览器这次不起拖'
            if 释放 not in 自身.已备:
                return False
            def 成功(已启动):
                '系统没有接受这次拖放则提示重试'
                if 已启动 is not True:
                    自身.报告失败()
            def 失败(错误=None):
                '启动失败则提示重试'
                自身.报告失败()
            期=桌面.start(句柄)
            盒['启动']=期
            if hasattr(期,'然后'):
                期.然后(成功,失败)
            elif hasattr(期,'then'):
                期.then(成功,失败)
            elif 期 is not True:
                自身.报告失败()
            return False
        return {'start':启动,'release':释放}

    def 浏览器(自身,文件):
        '用一次性令牌和 Blob 地址起拖。外部只看到 DownloadURL'
        窗口=取握手窗口()
        地址=窗口.URL.createObjectURL(文件)
        盒={'已放':False,'已起':False}
        def 放地址():
            '撤销这次准备的对象地址'
            自身.已备.discard(释放)
            窗口.URL.revokeObjectURL(地址)
        def 释放():
            '还没起拖就马上撤销。已经起拖则等拖放结束'
            盒['已放']=True
            if 盒['已起'] is not True:
                放地址()
        自身.已备.add(释放)
        def 启动(传递,源节点):
            '写下令牌和 DownloadURL。拖放结束或投放后清掉'
            if 盒['已放'] or 自身.已拆除:
                return False
            if 自身.活动 is not None:
                自身.活动['end']()
            盒['已起']=True
            令牌=str(随机标识())
            结束盒={'过':False}
            def 结束():
                '拖放结束只收一次'
                if 结束盒['过']:
                    return
                结束盒['过']=True
                源节点.removeEventListener('dragend',结束)
                窗口.removeEventListener('drop',放下)
                自身.活动=None
                盒['已起']=False
                if 盒['已放']:
                    放地址()
            def 放下():
                '投放后的微任务里收口，让投放处理先读到文件'
                def 微():
                    '收口'
                    结束()
                微任务=getattr(窗口,'queueMicrotask',None)
                if callable(微任务):
                    微任务(微)
                    return
                定时=threading.Timer(0,微)
                定时.daemon=True
                定时.start()
            自身.活动={'token':令牌,'file':文件,'end':结束}
            源节点.addEventListener('dragend',结束,{'once':True})
            窗口.addEventListener('drop',放下,{'once':True})
            传递.items.clear()
            传递.effectAllowed='copy'
            传递.setData(文件拖拽令牌类型,令牌)
            类型=getattr(文件,'type',None) or 'application/octet-stream'
            名=getattr(文件,'name',None) or 'file'
            传递.setData('DownloadURL',类型+':'+名+':'+地址)
            return True
        return {'start':启动,'release':释放}

    def 拆除(自身):
        '结束还在进行的传递，并释放每一次准备'
        自身.已拆除=True
        自身.寿命.中止(RuntimeError('File transfers disposed'))
        if 自身.活动 is not None:
            自身.活动['end']()
        for 释放 in list(自身.已备):
            释放()
