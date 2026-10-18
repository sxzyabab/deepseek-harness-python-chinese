'浏览器上的一元 RPC 调用方'
from ...模块.客户端.通告 import 取握手窗口
import json,re#附件元数据与通道规则
from ..rpc import Rpc标识,编码json,同步等待,取进程内网关,中止控制器#关联、正文、宿主网关与取消
from ..异常 import 连接错误#目标、传输和关联不符

通道规则=re.compile(r'^/[A-Za-z0-9._~-]+\Z')#绝对通道
端点段规则=re.compile(r'^[A-Za-z0-9_$.-]+\Z')#端点一段


def 读取(对象,键):
    '字典用键，页面对象用同名属性'
    if isinstance(对象,dict):#字典
        return 对象[键]#键
    return getattr(对象,键)#属性


def 是否记录(值):
    '普通对象。数组和空值都不是'
    return isinstance(值,dict)#字典


def 断言目标(通道,端点):
    '通道名和端点各段都必须合法'
    段=端点.split('/')#分段
    非法=False#先当合法
    if 通道规则.fullmatch(通道) is None:#通道
        非法=True#非法
    for 片 in 段:#每一段
        if 片=='' or 片=='.' or 片=='..' or 端点段规则.fullmatch(片) is None:#空、点或非法字符
            非法=True#非法
    if 非法:#不能发
        raise 连接错误('connection: invalid RPC target '+编码json(通道+'/'+端点))#拒绝


def 解析连接响应(值):
    '校验 server-response 信封，交出 rpcId 和业务结果'
    if not 是否记录(值) or 值.get('type')!='server-response' or not isinstance(值.get('rpcId'),str):#不是信封
        raise TypeError('connection: invalid server-response envelope')#拒绝
    结果=值.get('result')#结果
    if not 是否记录(结果):#不是对象
        raise TypeError('connection: invalid server-response result')#拒绝
    if 结果.get('ok') is True:#成功
        return {'rpcId':Rpc标识(值['rpcId']),'result':{'ok':True,'value':结果.get('value')}}#带上值，缺席为 None
    if 结果.get('ok') is not False or not 是否记录(结果.get('error')):#不是失败对象
        raise TypeError('connection: invalid server-response result')#拒绝
    错误=结果['error']#错误
    if not isinstance(错误.get('code'),str) or not isinstance(错误.get('message'),str) or not 是否记录(错误.get('details')):#三项
        raise TypeError('connection: invalid server-response failure')#拒绝
    return {#失败
        'rpcId':Rpc标识(值['rpcId']),#关联
        'result':{'ok':False,'error':{'code':错误['code'],'message':错误['message'],'details':错误['details']}},#错误
    }#结果结束


def 页面发送(输入,初始化):
    '这个网页引擎不再通过浏览器请求宿主'
    raise 连接错误('connection: 这个网页引擎不再通过浏览器请求宿主 '+str(输入))#拒绝


class 网页连接rpc:
    '拥有请求关联和响应信封校验的调用方'
    def __init__(自身,发送,打开流):
        '绑定一元发送。只有给出了流载体才有 open'
        自身.发送=发送#unary
        if 打开流 is not None:#有进程内流
            自身.open=自身._打开#暴露 open
            自身._打开流=打开流#流载体

    def call(自身,通道,端点,载荷,信号=None):
        '断言目标后 POST。校验回显的 rpcId，交出业务结果'
        断言目标(通道,端点)#目标
        窗口=取握手窗口()#页面
        原始=窗口.crypto.getRandomValues(窗口.Uint8Array(16))#16 个随机字节
        缓冲=bytearray(16)#本地副本
        for 下标 in range(16):#逐字节
            缓冲[下标]=int(原始[下标])&255#0 到 255
        缓冲[6]=(缓冲[6]&0x0f)|0x40#版本 4
        缓冲[8]=(缓冲[8]&0x3f)|0x80#变体
        十六=''.join(format(值,'02x') for 值 in 缓冲)#三十二位
        标识=Rpc标识(十六[0:8]+'-'+十六[8:12]+'-'+十六[12:16]+'-'+十六[16:20]+'-'+十六[20:])#关联
        消息={'type':'client-request','rpcId':标识,'method':端点,'payload':载荷}#信封
        路由=(通道+'/'+端点)[1:]#去掉前导斜杠的文档相对地址
        初始化={'method':'POST','headers':{'content-type':'application/json'},'body':编码json(消息)}#请求
        if 信号 is not None:#调用方要取消
            初始化['signal']=信号#带上
        响应=同步等待(自身.发送(路由,初始化))#等到响应
        if not 读取(响应,'ok'):#HTTP 失败
            raise 连接错误('transport failure for '+通道+'/'+端点+': HTTP '+str(读取(响应,'status')))#原文
        头=读取(响应,'headers')#响应头
        类型头=头.get('content-type') if hasattr(头,'get') else None#类型
        媒体=类型头.split(';',1)[0].strip().lower() if isinstance(类型头,str) else None#媒体
        if 媒体=='multipart/form-data':#带附件
            表单=同步等待(读取(响应,'formData')())#表单
            字段={}#名到值
            迭代=表单.items() if isinstance(表单,dict) else 表单#成对
            for 名,值 in 迭代:#逐段
                if 名 in 字段:#重复
                    raise TypeError('connection: invalid binary response fields')#拒绝
                字段[名]=值#收下
            元文=字段.get('metadata')#元数据
            if 'metadata' in 字段:#用过
                del 字段['metadata']#摘掉
            if not isinstance(元文,str):#必须是字符串
                raise TypeError('connection: invalid binary response fields')#拒绝
            信封=json.loads(元文)#对象
            完整=解析连接响应(信封)#信封
            if (not 完整['result']['ok']) or (not 是否记录(信封)) or (not isinstance(信封.get('attachments'),list)) or len(信封['attachments'])==0:#不是带附件的成功
                raise TypeError('connection: invalid binary response result')#拒绝
            根={'value':完整['result']['value']}#从 value 起按路径写入
            for 附件 in 信封['attachments']:#逐个附件
                if (not 是否记录(附件)) or 附件.get('codec')!='bytes' or (not isinstance(附件.get('part'),str)) or (not isinstance(附件.get('path'),list)):#说明不合法
                    raise TypeError('connection: invalid binary response attachment')#拒绝
                数据=字段.get(附件['part'])#分段
                if 附件['part'] in 字段:#用过
                    del 字段[附件['part']]#摘掉
                if isinstance(数据,(bytes,bytearray)):#已经是字节
                    字节=bytes(数据)#拷贝
                elif not isinstance(数据,str) and 数据 is not None and hasattr(数据,'arrayBuffer'):#Blob
                    字节=bytes(同步等待(数据.arrayBuffer()))#字节
                else:#不是字节段
                    raise TypeError('connection: invalid binary response fields')#拒绝
                父=根#从根走
                键='value'#先到 value
                for 段 in 附件['path']:#路径
                    值=父[键]#当前节点
                    if not isinstance(值,(dict,list)) or 值 is None:#不是容器
                        raise TypeError('connection: invalid binary response path')#拒绝
                    if isinstance(值,list):#数组
                        if isinstance(段,bool) or not isinstance(段,int) or 段<0 or 段>=len(值):#下标不合法
                            raise TypeError('connection: invalid binary response path')#拒绝
                    elif not isinstance(段,str):#对象键必须是字符串
                        raise TypeError('connection: invalid binary response path')#拒绝
                    if isinstance(值,dict) and 段 not in 值:#没有这个键
                        raise TypeError('connection: invalid binary response path')#拒绝
                    父=值#下降
                    键=段#下一段
                if 父[键] is not None:#占位必须是 null
                    raise TypeError('connection: invalid binary response placeholder')#拒绝
                父[键]=字节#写入字节
            if len(字段)!=0:#还有没用到的段
                raise TypeError('connection: invalid binary response fields')#拒绝
            完整={'rpcId':完整['rpcId'],'result':{'ok':True,'value':根['value']}}#换上字节后的值
        else:#JSON 信封
            完整=解析连接响应(同步等待(读取(响应,'json')()))#解析
        if 信号 is not None:#调用方的取消
            抛出=getattr(信号,'throwIfAborted',None)#已中止则抛
            if callable(抛出):#有这个方法
                抛出()#抛出
        if 完整['rpcId']!=标识:#关联不符
            raise 连接错误('rpcId mismatch for '+端点+': sent '+标识+', got '+str(完整['rpcId']))#原文
        return 完整['result']#业务结果

    def _打开(自身,通道,端点,载荷,信号,上行=None):
        '进程内流只接受 /api。浏览器页面不走这里'
        断言目标(通道,端点)#目标
        if 通道!='/api':#不是共享通道
            raise 连接错误('connection: worker-local streams require the /api channel, got '+编码json(通道))#拒绝
        return 自身._打开流(端点,载荷,信号,上行)#交给载体


def 进程内对等():
    '本进程的所有者。信号不中止，交互是 answer'
    return {'principal':{'kind':'owner'},'interactions':'answer','signal':中止控制器().signal}#对等端


class 进程内调用:
    '一元和流都交给本进程的宿主网关'
    进程内=True#网关据此不打开浏览器套接字

    def call(自身,通道,端点,载荷,信号=None):
        '一元调用。没有宿主网关就拒绝，不走页面 fetch'
        网关=取进程内网关()#宿主
        if 网关 is None:#还没起来
            raise 连接错误('connection: 本进程没有宿主网关')#拒绝
        if 通道!='/api':#只走共享通道
            raise 连接错误('connection: 进程内调用只走 /api')#拒绝
        return 网关.分发RPC(端点,载荷,信号,进程内对等())#信封

    def open(自身,通道,端点,载荷,信号,上行=None):
        '逻辑流。没有宿主网关就拒绝，不走浏览器套接字'
        网关=取进程内网关()#宿主
        if 网关 is None:#还没起来
            raise 连接错误('connection: 本进程没有宿主网关')#拒绝
        if 通道!='/api':#只走共享通道
            raise 连接错误('connection: 进程内流只走 /api')#拒绝
        return 网关.打开线路流(端点,载荷,上行,进程内对等(),信号,中止控制器())#迭代


def 创建网页连接rpc(执行fetch=None,打开流=None):
    '创建调用方。可以换成别的 fetch，也可以带上进程内流'
    发送=页面发送 if 执行fetch is None else 执行fetch#默认页面 fetch
    return 网页连接rpc(发送,打开流)#调用方
