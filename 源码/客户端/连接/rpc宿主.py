'宿主上的通道登记和 HTTP 适配'
import re,urllib.parse,uuid#通道、路径与附件分段
from ...依赖.cordis.服务 import 服务#服务基类
from .http桥 import 桥接,连接响应#HTTP 桥与响应
from .rpc import Rpc标识,编码json,同步等待#关联、JSON 与期约
from .rpc数据架构 import 客户端请求模式#请求信封
from .接口路径 import 接口路径# /api
from .接口请求信任 import 是否受信任接口请求,是否远程权威#围栏
from .对等 import 对等#操作方
from .异常 import 连接错误#通道和路由登记失败

无效请求标识=Rpc标识('invalid-request')#信封里没有合法 rpcId 时使用
通道规则=re.compile(r'^/[A-Za-z0-9._~-]+\Z')#绝对通道
端点段规则=re.compile(r'^[A-Za-z0-9_$.-]+\Z')#端点的一段


def 纯文本(正文,状态):
    '一段纯文本响应'
    return 连接响应(正文,状态,{'content-type':'text/plain;charset=UTF-8'})#响应


def 编码json响应(正文,状态=200):
    'application/json 响应'
    return 连接响应(编码json(正文).encode('utf-8'),状态,{'content-type':'application/json'})#响应


def 路径切端点(通道,路径名):
    '从绝对路径切出通道相对端点。畸形则没有'
    前缀=通道+'/'#通道加斜杠
    if not 路径名.startswith(前缀):#不在这个通道下
        return None#没有
    端点=路径名[len(通道)+1:]#相对端点
    for 片 in 端点.split('/'):#每一段
        if 片=='' or 片=='.' or 片=='..' or 端点段规则.fullmatch(片) is None:#空、点或非法字符
            return None#拒绝
    return 端点#端点


def 完整响应(rpc标识,结果):
    '失败或没有附件时用 JSON。有附件时用 multipart'
    if not 结果['ok']:#失败
        return 编码json响应({'type':'server-response','rpcId':rpc标识,'result':结果})#JSON
    成功={'ok':True,'value':结果['value'] if 'value' in 结果 else None}#去掉附件后的成功结果
    正文={'type':'server-response','rpcId':rpc标识,'result':成功}#信封
    附件=结果.get('attachments')#附件
    if not 附件:#没有附件
        return 编码json响应(正文)#JSON
    边界='----dshconnection'+uuid.uuid4().hex#边界
    元数据=[]#附件说明
    字节表=[]#分段字节
    for 序号,一项 in enumerate(附件):#逐个附件
        段名='bytes-'+str(序号)#分段名
        元数据.append({'path':list(一项['path']),'codec':'bytes','part':段名})#说明
        字节表.append((段名,bytes(一项['bytes'])))#字节
    元文=编码json({'type':正文['type'],'rpcId':正文['rpcId'],'result':正文['result'],'attachments':元数据})#元数据
    块=[]#multipart

    def 加段(名,数据,类型):
        '追加一段 form-data'
        块.append(('--'+边界+'\r\n').encode('ascii'))#边界
        块.append(('content-disposition: form-data; name="'+名+'"\r\n').encode('utf-8'))#名字
        if 类型 is not None:#有类型
            块.append(('content-type: '+类型+'\r\n').encode('utf-8'))#类型
        块.append(b'\r\n')#空行
        if isinstance(数据,str):#文本
            数据=数据.encode('utf-8')#编码
        块.append(数据)#正文
        块.append(b'\r\n')#段尾

    加段('metadata',元文,'application/json')#元数据
    for 段名,数据 in 字节表:#字节段
        加段(段名,数据,'application/octet-stream')#一段
    块.append(('--'+边界+'--\r\n').encode('ascii'))#结束
    return 连接响应(b''.join(块),200,{'content-type':'multipart/form-data; boundary='+边界})#表单


def 错误响应(rpc标识,错误):
    '失败结果的 JSON 响应'
    return 完整响应(rpc标识,{'ok':False,'error':错误})#失败


def 远程取值处理(通道,处理函数):
    '把一条已解码通道收成 fetch 处理。正文一律缓冲'
    def 正文模式(请求):
        '这条通道的正文总是缓冲'
        return 'buffered'#缓冲

    def 取值(请求,对等体):
        'POST 且端点合法才交给处理函数'
        路径=urllib.parse.urlsplit(请求.url).path#路径
        端点=路径切端点(通道,路径)#端点
        if 请求.method!='POST' or 端点 is None:#不是这条通道的 POST
            return 纯文本('not found',404)#404
        类型头=请求.headers.get('content-type') if hasattr(请求.headers,'get') else None#类型
        媒体=类型头.split(';',1)[0].strip().lower() if isinstance(类型头,str) else None#媒体类型
        if 媒体!='application/json':#不是 JSON
            return 纯文本('content type must be application/json',415)#415
        try:#读 JSON
            体=同步等待(请求.json())#对象
        except Exception:#不是 JSON
            return 纯文本('body is not JSON',400)#400
        信封=客户端请求模式.safeParse(体)#信封
        if not 信封.success:#不合法
            原始=体.get('rpcId') if isinstance(体,dict) else None#原关联
            标识=Rpc标识(原始) if isinstance(原始,str) else 无效请求标识#能用则用
            return 错误响应(标识,{#坏请求
                'code':'gateway/bad-request',#码
                'message':'invalid client-request message',#说明
                'details':{'issues':信封.error.issues},#问题
            })#响应
        消息=信封.data#信封
        if 消息['method']!=端点:#方法和路径不一致
            return 错误响应(消息['rpcId'],{#坏请求
                'code':'gateway/bad-request',#码
                'message':'method '+编码json(消息['method'])+' does not match endpoint '+编码json(端点),#说明
                'details':{'issues':[]},#没有模式问题
            })#响应
        try:#交给端点
            结果=同步等待(处理函数(端点,消息['payload'],请求.signal,对等体))#结果
            return 完整响应(消息['rpcId'],结果)#信封
        except Exception as 错误:#处理函数抛了
            return 纯文本('handler failure: '+str(错误),500)#500

    return {'requestBodyMode':正文模式,'fetch':取值}#处理


class 宿主通道注册:
    '读到 connection.rpc 的那份上下文上的通道登记'
    def __init__(自身,服务,登记方):
        '记下服务和登记方'
        自身._服务=服务#宿主服务
        自身._登记方=登记方#调用方上下文

    def handle(自身,通道,处理函数):
        '登记一条绝对通道'
        return 自身._服务._登记通道(自身._登记方,通道,处理函数)#登记

    def intercept(自身,通道,匹配,处理函数):
        '在共享 /api 的回退之前拦截端点'
        return 自身._服务._登记拦截(自身._登记方,通道,匹配,处理函数)#登记


class 宿主取值注册:
    '读到 connection.fetch 的那份上下文上的精确路由'
    def __init__(自身,服务,登记方):
        '记下服务和登记方'
        自身._服务=服务#宿主服务
        自身._登记方=登记方#调用方上下文

    def register(自身,路由):
        '登记一条精确 Fetch 路由'
        return 自身._服务._登记精确路由(自身._登记方,路由)#登记


class 宿主连接服务(服务):
    '宿主 Connection。通道登记属于读取本服务的那条纤程'
    def __init__(自身,上下文,受信任主机表,浏览器认证):
        '在活动 HTTP 服务器上提供宿主半边'
        super().__init__(上下文,'connection')#服务名
        自身.拥有=上下文#插件自己的上下文，不随调用方改变
        自身._受信任主机表=list(受信任主机表)#受信任权威
        自身._认证=浏览器认证#浏览器认证
        自身.browserPeer=对等(上下文,{'principal':{'kind':'owner'}})#浏览器共用的拥有者
        自身._对等表={}#接口对等到是否占着套接字
        自身._已拆除=False#服务是否已拆除
        自身._拦截器={}#共享通道拦截
        自身._精确路由={}#精确 Fetch 路由
        自身.allowsRemoteAuthorities=any(是否远程权威(条目) for 条目 in 受信任主机表)#是否接受回环以外的权威

        def 寿命():
            '卸载时拆掉浏览器对等和还活着的接口对等'
            def 清理():
                '先标记，再清空，再逐个拆除'
                自身._已拆除=True#不再准入
                对等列=[自身.browserPeer]#浏览器
                对等列.extend(记录['peer'] for 记录 in 自身._对等表.values())#接口
                自身._对等表.clear()#清空
                for 一个 in 对等列:#逐个
                    一个.dispose()#拆除
            return 清理#拆除器

        上下文.副作用(寿命,'client-connection: Peer scopes')#随插件拆除

    @property
    def rpc(自身):
        '作用域落在读取本服务的上下文上'
        return 宿主通道注册(自身,自身.所属上下文)#登记表

    @property
    def fetch(自身):
        '精确路由也落在读取本服务的上下文上'
        return 宿主取值注册(自身,自身.所属上下文)#登记表

    def _载体(自身):
        '插件上下文上的网页服务器。没有则为空'
        return 自身.拥有.获取服务('webServer')#可选

    def _是否受信任(自身,请求):
        '按监听地址和方案做 Host 围栏'
        载体=自身._载体()#网页服务器
        if 载体 is None:#还没挂上
            绑定=None#没有绑定地址
            协议='http:'#默认 HTTP
        else:#有载体
            绑定=getattr(载体,'host',None)#绑定地址
            协议=getattr(载体,'protocol',None)#方案
            if 协议 is None:#没有这个字段
                协议='http:'#默认 HTTP
        return 是否受信任接口请求(请求,自身._受信任主机表,绑定,协议)#围栏

    def _是否安全(自身,用调用方=False):
        '只有监听自己声明 https: 才算 TLS'
        上下文=自身.所属上下文 if 用调用方 else 自身.拥有#authorizeIndex 用调用方
        载体=上下文.获取服务('webServer')#网页服务器
        return 载体 is not None and getattr(载体,'protocol',None)=='https:'#是不是 https

    def requestRejection(自身,请求):
        '先做围栏和认证。可以继续则为空'
        准入=自身.admit(请求)#准入
        if 'rejection' in 准入:#被拒绝
            return 准入['rejection']#401 或 403
        return None#可以继续

    def admit(自身,请求):
        '浏览器请求共用拥有者。接口 HTTP 不要求已经挂着套接字'
        if not 自身._是否受信任(请求):#围栏没过
            return {'rejection':403}#禁止
        if 自身._已拆除:#服务已拆
            return {'rejection':401}#未认证
        安全=自身._是否安全()#是不是 TLS
        if 自身._认证.是否已认证(请求,安全):#浏览器饼干
            return {'peer':自身.browserPeer}#共用拥有者
        标识=自身._认证.鉴别接口(请求,安全)#接口饼干
        记录=None if 标识 is None else 自身._对等表.get(标识)#活着的对等
        if 记录 is None:#没有
            return {'rejection':401}#未认证
        return {'peer':记录['peer']}#这一个

    def createPeer(自身,选项):
        '进程内对等，随读取 connection 的上下文拆除'
        return 对等(自身.所属上下文,选项)#新的

    def admitConnection(自身,请求):
        '接口套接字同步占有。浏览器套接字不占独立名额'
        准入=自身.admit(请求)#先准入
        if 'rejection' in 准入:#被拒绝
            return 准入#原样
        记录=自身._对等表.get(准入['peer'].id)#接口记录
        if 记录 is None:#浏览器或进程内，没有套接字名额

            def 释放空():
                '没有要拆除的接口对等'
                return None#完成

            return {'peer':准入['peer'],'release':释放空}#空释放
        if 记录['ownsSocket']:#已经有一条套接字
            return {'rejection':409}#冲突
        记录['ownsSocket']=True#占上
        已释放={'值':False}#只拆一次

        def 释放():
            '摘掉准入并拆除这个接口对等。不取消它已经发出的 HTTP'
            if 已释放['值']:#已经释放
                return None#同一结果
            自身._对等表.pop(记录['peer'].id,None)#摘掉
            已释放['值']=True#占上
            return 记录['peer'].dispose()#拆除

        return {'peer':记录['peer'],'release':释放}#释放器

    def _发布对等(自身,交互):
        '连接成功前先创建操作方，再把标识写进饼干'
        一个=对等(自身.拥有,{'principal':{'kind':'owner'},'interactions':交互})#拥有者
        自身._对等表[一个.id]={'peer':一个,'ownsSocket':False}#还没占套接字
        return 一个.id#标识

    def authorizeConnect(自身,请求,响应):
        '先过围栏，再交换启动令牌'
        if not 自身._是否受信任(请求) or 自身._已拆除:#围栏或已拆
            响应.writeHead(401 if 自身._已拆除 else 403)#状态
            响应.end('unauthorized' if 自身._已拆除 else 'forbidden')#正文
            return#结束
        自身._认证.授权连接(请求,响应,自身._是否安全(),自身._发布对等)#交换

    def authorizeIndex(自身,请求,响应):
        '索引认证。TLS 由调用方上下文上的网页服务器决定'
        return 自身._认证.授权索引(请求,响应,自身._是否安全(True))#是否可发索引

    def authenticatedUrl(自身,基址):
        '把本进程的启动令牌加到干净的应用网址上'
        return 自身._认证.已认证网址(基址)#带令牌的网址

    def createSharedFetchHandler(自身,通道):
        '精确路由优先，然后是拦截器，其余 404'
        def 正文模式(请求):
            '命中精确路由就用它的正文模式，否则缓冲'
            方法=请求['method'] if isinstance(请求,dict) else 请求.method#方法
            网址=请求['url'] if isinstance(请求,dict) else 请求.url#网址
            路径=网址.pathname if hasattr(网址,'pathname') else urllib.parse.urlsplit(str(网址)).path#路径
            路由=自身._精确路由.get(路径)#路由
            if 路由 is not None and 方法 in 路由['methods']:#方法命中
                return 路由['requestBody']#路由自己的模式
            return 'buffered'#默认缓冲

        def 取值(请求,对等体):
            '拥有者才能进精确路由'
            路径=urllib.parse.urlsplit(请求.url).path#路径
            路由=自身._精确路由.get(路径)#路由
            if 路由 is not None and 请求.method in 路由['methods']:#方法命中
                主体=对等体.principal#身份
                种类=主体['kind'] if isinstance(主体,dict) else 主体.kind#种类
                if 种类!='owner':#不是拥有者
                    return 纯文本('forbidden',403)#403
                return 同步等待(路由['fetch'](请求))#交给路由
            端点=路径切端点(通道,路径)#端点
            拦截=自身._拦截器.get(通道)#拦截器
            if 端点 is None or 拦截 is None or not 拦截['matches'](端点):#没有人认领
                return 纯文本('not found',404)#404
            return 拦截['fetchHandler']['fetch'](请求,对等体)#拦截器

        return {'requestBodyMode':正文模式,'fetch':取值}#处理

    def _登记精确路由(自身,登记方,路由):
        '路径必须在 /api 下，方法不能空也不能重复'
        路径=路由['path']#路径
        if 路径切端点(接口路径,路径) is None:#不是合法端点路径
            raise 连接错误('connection: invalid exact Fetch route '+编码json(路径))#拒绝
        方法表=list(路由['methods'])#方法
        if len(方法表)==0:#没有方法
            raise 连接错误('connection: exact Fetch route '+编码json(路径)+' declares no methods')#拒绝
        if len(set(方法表))!=len(方法表):#重复
            raise 连接错误('connection: exact Fetch route '+编码json(路径)+' repeats a method')#拒绝
        已登记={'methods':set(方法表),'requestBody':路由['requestBody'],'fetch':路由['fetch']}#记下

        def 执行():
            '重复路径在效应里失败，好跟纤程的回滚走'
            if 路径 in 自身._精确路由:#已经有
                raise 连接错误('connection: exact Fetch route '+编码json(路径)+' is already registered')#拒绝
            自身._精确路由[路径]=已登记#放入

            def 拆除():
                '摘掉这一条'
                自身._精确路由.pop(路径,None)#摘掉

            return 拆除#拆除器

        return 登记方.副作用(执行,'client-connection: '+路径+' Fetch route')#随纤程

    def _登记通道(自身,登记方,通道,处理函数):
        '/api 留给共享通道。其它绝对通道各挂一条前缀路由'
        if 通道规则.fullmatch(通道) is None or 通道=='/api':#非法或被保留
            raise 连接错误('connection: invalid or reserved RPC channel '+编码json(通道))#拒绝
        取值处理=远程取值处理(通道,处理函数)#fetch 处理

        def 处理(节点请求,节点响应):
            '准入之后桥接'
            准入=自身.admit(节点请求)#准入
            if 'rejection' in 准入:#被拒绝
                节点响应.writeHead(准入['rejection'])#状态
                节点响应.end('unauthorized' if 准入['rejection']==401 else 'forbidden')#正文
                return#结束
            桥接(节点请求,节点响应,取值处理,准入['peer'])#桥

        路由={'kind':'prefix','path':通道,'handler':处理}#前缀路由

        def 执行():
            '交给网页服务器'
            return 登记方.webServer.register(路由)#登记

        return 登记方.副作用(执行,'client-connection: '+通道+' rpc channel')#随纤程

    def _登记拦截(自身,登记方,通道,匹配,处理函数):
        '目前只接受 /api'
        if 通道!=接口路径:#不是共享通道
            raise 连接错误('connection: invalid shared RPC channel '+编码json(通道))#拒绝
        拦截={'matches':匹配,'fetchHandler':远程取值处理(通道,处理函数)}#拦截器

        def 执行():
            '一条共享通道只能有一个拦截器'
            if 通道 in 自身._拦截器:#已经有
                raise 连接错误('connection: shared RPC channel '+编码json(通道)+' already has an interceptor')#拒绝
            自身._拦截器[通道]=拦截#放入

            def 拆除():
                '摘掉拦截器'
                自身._拦截器.pop(通道,None)#摘掉

            return 拆除#拆除器

        return 登记方.副作用(执行,'client-connection: '+通道+' rpc interceptor')#随纤程
