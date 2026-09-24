import base64,hashlib,hmac,platform,secrets,sys,threading,time,uuid
from urllib.parse import urlparse,parse_qs,urlencode,urlunparse
from ...依赖.cordis import 服务
from ...依赖.schemastery import (
    字符串字段,布尔字段,数字字段,字典字段,复合类型字段,常量字段,
)
from ...工具.超时 import 已中止,若已中止则抛出,截止,中止控制器
from ...内核.作用域 import 操作任务
from ..凭据 import 凭证键
from ..deepseek账号 import deepseek账号,合并平台Cookie,桌面客户端头
from .细节列表 import 投影配置档,读账号细节
from .登出 import 吊销账号
from .协议 import (
    平台认证错误,平台头,平台来源,浏览器网址,请求平台,初始化形态,交换形态,登录来源 as 规范化登录来源,
)

__all__=['包名','名称','依赖','默认','配置','平台账号','平台认证错误']

包名='@deepseek-ai/dsh-deepseek-account-platform'
名称='deepseek-account-platform'
依赖=['credentials','authorization']

授予键=凭证键('deepseek-account-platform','default')
设备键=凭证键('deepseek-account-platform','device')

配置={
    'platformOrigin':字符串字段(默认值='https://platform.deepseek.com'),
    'desktopPlatform':复合类型字段(常量字段('darwin'),常量字段('win32'),常量字段(None),默认值=None),
    'embeddedPageDist':字符串字段(默认值=''),
    'inferenceOrigin':字符串字段(默认值='https://api.deepseek.com'),
    'allowLoopbackHttp':布尔字段(默认值=False),
    'rewriteBrowserOrigin':布尔字段(默认值=False),
    'requestHeaders':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),
    'accountRequestHeaders':字典字段(键值结构=(字符串字段(),字符串字段()),默认值={}),
    'requestTimeoutMs':数字字段(最小=1,最大=120000,默认值=30000),
    'logoutMaxRetries':数字字段(最小=0,最大=5,默认值=5),
    'logoutRetryDelayMs':数字字段(最小=1,最大=60000,默认值=1000),
    'attemptTimeoutMs':数字字段(最小=1,最大=3600000,默认值=600000),
}

def 解析授予(载荷):
    """version=1 的授予。"""
    if not isinstance(载荷,dict):
        return None
    if 载荷.get('version')!=1:
        return None
    令牌=载荷.get('token')
    签发=载荷.get('issuer')
    if not isinstance(令牌,str) or 令牌=='' or not isinstance(签发,str) or 签发=='':
        return None
    return {'version':1,'token':令牌,'issuer':签发}

class 静默交互:
    """登录流程不走提示面。"""
    def notify(自身,通知):
        """忽略。"""
        return
    def prompt(自身,提示):
        """拒绝。"""
        raise 平台认证错误('protocol')

class 平台账号(deepseek账号):
    """PKCE 账号提供方。"""
    def __init__(自身,上下文,配置值=None):
        """登记流程并监听记录变更。"""
        super().__init__(上下文)
        if 配置值 is None:
            配置值={}
        自身._嵌入发行=配置值['embeddedPageDist'] if 'embeddedPageDist' in 配置值 else ''
        允许回环=配置值['allowLoopbackHttp'] if 'allowLoopbackHttp' in 配置值 else False
        自身._来源=平台来源(配置值['platformOrigin'] if 'platformOrigin' in 配置值 else 'https://platform.deepseek.com',允许回环)
        推理=urlparse(配置值['inferenceOrigin'] if 'inferenceOrigin' in 配置值 else 'https://api.deepseek.com')
        if (推理.scheme not in ('http','https') or 推理.username or 推理.password
                or 推理.path not in ('','/') or 推理.query or 推理.fragment):
            raise ValueError('account: inferenceOrigin 必须是不含凭证、路径、查询或片段的 HTTP(S) 来源')
        自身._推理来源=推理.scheme+'://'+推理.netloc
        自身._改写浏览器=配置值['rewriteBrowserOrigin'] if 'rewriteBrowserOrigin' in 配置值 else False
        自身._客户端头={'x-client-platform':'web',**桌面客户端头(配置值['desktopPlatform'] if 'desktopPlatform' in 配置值 else None)}
        自身._请求头=平台头(配置值['requestHeaders'] if 'requestHeaders' in 配置值 else {})
        账号头=平台头(配置值['accountRequestHeaders'] if 'accountRequestHeaders' in 配置值 else {})
        自身._账号头={**自身._请求头,**账号头}
        if 'cookie' in 账号头:
            自身._账号头['cookie']=合并平台Cookie(自身._请求头['cookie'] if 'cookie' in 自身._请求头 else '',账号头['cookie'])
        自身._请求超时=配置值['requestTimeoutMs'] if 'requestTimeoutMs' in 配置值 else 30000
        自身._尝试超时=配置值['attemptTimeoutMs'] if 'attemptTimeoutMs' in 配置值 else 600000
        自身._登出政策={
            'maxRetries':配置值['logoutMaxRetries'] if 'logoutMaxRetries' in 配置值 else 5,
            'delayMs':配置值['logoutRetryDelayMs'] if 'logoutRetryDelayMs' in 配置值 else 1000,
            'requestTimeoutMs':自身._请求超时,
        }
        自身._登出寿命=中止控制器()
        自身._吊销表=set()
        自身._尝试=None
        自身._监听者=set()
        自身._最近配置档=None
        自身._细节寿命=中止控制器()
        自身._已关闭=False
        自身._移除中=None
        自身.__dict__[服务.初始化]=自身._初始化
        def 运行流程(会话):
            """授权流程体。"""
            尝试=自身._尝试
            if 尝试 is None:
                raise 平台认证错误('protocol')
            自身._运行(会话,尝试)
        上下文.authorization.注册流程({
            'key':授予键,
            'label':'DeepSeek',
            'methods':[{'id':'browser','label':'DeepSeek'}],
            'run':运行流程,
        })
        def 记录已更新(键,*剩余):
            """本键变更则作废细节。"""
            if 键!=授予键:
                return
            自身._作废细节()
            自身._已变()
        上下文.监听('credentials/record-updated',记录已更新)
        def 拆除效果():
            """关掉在途尝试与吊销。"""
            def 清理():
                """等待在途结束。"""
                自身._已关闭=True
                自身._登出寿命.中止()
                自身._作废细节()
                活动=自身._尝试
                if 活动 is not None:
                    if 活动['view']['phase']!='committing':
                        活动['controller'].中止()
                    活动['done'].wait()
                if 自身._移除中 is not None:
                    自身._移除中.wait()
                for 项 in list(自身._吊销表):
                    项.wait()
                自身._已变()
            return 清理
        上下文.副作用(拆除效果,'account: active attempt lifetime')

    def _初始化(自身):
        """校验已存授予的签发方。"""
        记录=自身.ctx.credentials.读记录(授予键)
        if 记录 is None:
            return
        if 记录.get('kind')!='grant':
            raise 平台认证错误('storage')
        解析=解析授予(记录.get('payload'))
        if 解析 is None:
            raise 平台认证错误('storage')
        if 解析['issuer']==自身._来源:
            return
        自身.ctx.credentials.删除记录(授予键)
        print('[deepseek-account] 已丢弃存储授予',{'reason':'issuer-mismatch'})

    def 获取状态(自身):
        """已存账号与最近尝试。"""
        记录=自身.ctx.credentials.读记录(授予键)
        if 记录 is not None and (记录.get('kind')!='grant' or 解析授予(记录.get('payload')) is None):
            raise 平台认证错误('storage')
        尝试视图=自身._尝试['view'] if 自身._尝试 is not None else None
        return {
            'status':'signed-out' if 记录 is None else 'credential-stored',
            'attempt':尝试视图,
            'links':{
                'usageUrl':自身._来源+'/usage',
                'topUpUrl':自身._来源+'/top_up',
            },
        }

    def 获取配置档(自身):
        """独立查询配置档。"""
        寿命=自身._细节寿命
        结果=自身._取细节('profile')
        if 自身._细节寿命 is not 寿命:
            return None
        if 结果 is not None and 结果.get('status')=='ready':
            自身._最近配置档=结果
        if 结果 is not None and 结果.get('status')=='failed':
            return 自身._最近配置档 if 自身._最近配置档 is not None else 结果
        return 结果

    def 获取平衡(自身):
        """独立查询钱包。"""
        return 自身._取细节('balance')

    def _取细节(自身,字段):
        """读一项平台字段。"""
        寿命=自身._细节寿命
        已存=自身._读当前授予(寿命)
        if 已存 is None or 已中止(寿命.信号):
            return None
        if 字段=='profile' and 自身._尝试 is not None:
            初=自身._尝试.get('initialProfile')
            if 初 is not None and 初.get('token')==已存['token']:
                自身._尝试.pop('initialProfile',None)
                return 初['value']
        句柄=截止(寿命.信号,自身._请求超时,'account-detail')
        try:
            细节=读账号细节(字段,自身._来源,已存['token'],句柄.信号,{**自身._账号头,**自身._客户端头})
        finally:
            句柄.释放()
        if 自身._细节寿命 is not 寿命:
            return None
        return 细节

    def 获取平台会话(自身):
        """宿主专用会话快照。"""
        寿命=自身._细节寿命
        已存=自身._读当前授予(寿命)
        if 已存 is None or 已中止(寿命.信号):
            return None
        结果={'origin':自身._来源,'token':已存['token'],'requestHeaders':{**自身._账号头,**自身._客户端头}}
        if 自身._嵌入发行:
            结果['embeddedPageDist']=自身._嵌入发行
        return 结果

    def _读当前授予(自身,寿命):
        """匹配当前来源的授予。"""
        if 自身._已关闭:
            return None
        记录=自身.ctx.credentials.读记录(授予键)
        if 记录 is None or 已中止(寿命.信号):
            return None
        if 记录.get('kind')!='grant':
            raise 平台认证错误('storage')
        解析=解析授予(记录.get('payload'))
        if 解析 is None:
            raise 平台认证错误('storage')
        if 解析['issuer']!=自身._来源:
            raise 平台认证错误('protocol')
        return 解析

    def 解析令牌(自身,网址):
        """仅推理来源。"""
        目的=urlparse(网址)
        目的来源=目的.scheme+'://'+目的.netloc
        if 目的来源!=自身._推理来源 or 目的.username or 目的.password:
            return None
        记录=自身.ctx.credentials.读记录(授予键)
        if 记录 is None:
            return None
        if 记录.get('kind')!='grant':
            raise 平台认证错误('storage')
        结果=解析授予(记录.get('payload'))
        if 结果 is None:
            raise 平台认证错误('storage')
        签发=urlparse(结果['issuer'])
        if 结果['token'].startswith('dsh_mock_'):
            return None
        if 自身._推理来源=='https://api.deepseek.com':
            主机=签发.hostname or ''
            if 主机 in ('localhost','127.0.0.1','::1'):
                return None
        elif (签发.scheme+'://'+签发.netloc)!=自身._来源:
            return None
        return 结果['token']

    def 开始登录(自身,区域,回调来源,登录来源):
        """加入在途或新开浏览器授权。"""
        if 自身._移除中 is not None:
            自身._移除中.wait()
        来源=规范化登录来源(回调来源)
        if 自身._已关闭:
            raise 平台认证错误('protocol')
        if 自身._尝试 is not None and 自身._尝试['view']['phase'] in ('initializing','waiting-browser','exchanging','committing'):
            return 自身.获取状态()
        先前=自身._尝试
        if 先前 is not None:
            先前['done'].wait()
            if 自身._已关闭:
                raise 平台认证错误('protocol')
            if 自身._尝试 is not 先前:
                return 自身.获取状态()
        首段=区域.lower().replace('-','_').split('_')[0]
        尝试={
            'origin':来源,
            'loginSource':登录来源,
            'locale':'zh_CN' if 首段=='zh' else 'en_US',
            'view':{'id':str(uuid.uuid4()),'phase':'initializing'},
            'controller':中止控制器(),
            'done':threading.Event(),
        }
        自身._尝试=尝试
        def 后台():
            """跑完授权开始。"""
            try:
                结果=自身.所属上下文.authorization.开始({
                    'key':授予键,
                    'signal':尝试['controller'].信号,
                    'interaction':静默交互(),
                })
                自身._更新(尝试,{'phase':'succeeded' if 结果['status']=='authorized' else 'cancelled'})
                回调=尝试.get('callback')
                if 结果['status']=='authorized' and 尝试.get('completionUrl') is not None and 回调 is not None:
                    回调.writeHead(302,{'location':尝试['completionUrl'],'cache-control':'no-store'}).end()
                elif 回调 is not None:
                    回调.writeHead(204,{'cache-control':'no-store'}).end()
            except Exception as 错误:
                码=错误.code if isinstance(错误,平台认证错误) else 'protocol'
                print('[deepseek-account] 登录失败',{'errorCode':码})
                自身._更新(尝试,{'phase':'expired' if 码=='expired' else 'failed','errorCode':码})
                自身._失败回调(尝试)
            finally:
                拆除=尝试.get('disposeCallback')
                if 拆除 is not None:
                    拆除()
                尝试['done'].set()
        threading.Thread(target=后台,daemon=True).start()
        自身._已变()
        return 自身.获取状态()

    def 取消登录(自身,标识):
        """取消指定尝试。"""
        尝试=自身._尝试
        if 尝试 is not None and 尝试['view']['id']==标识:
            if 尝试['view']['phase']!='committing':
                尝试['controller'].中止()
                自身.ctx.authorization.取消(授予键)
            尝试['done'].wait()
        return 自身.获取状态()

    def 登出(自身):
        """去掉本地授予并后台吊销。"""
        if 自身._移除中 is not None:
            自身._移除中.wait()
            return 自身.获取状态()
        完成=threading.Event()
        自身._移除中=完成
        try:
            if 自身._已关闭:
                raise 平台认证错误('protocol')
            if 自身._尝试 is not None:
                自身.取消登录(自身._尝试['view']['id'])
            记录=自身.ctx.credentials.读记录(授予键)
            if 记录 is not None:
                if 记录.get('kind')!='grant':
                    raise 平台认证错误('storage')
                解析=解析授予(记录.get('payload'))
                if 解析 is None:
                    raise 平台认证错误('storage')
                if 解析['issuer']!=自身._来源:
                    raise 平台认证错误('protocol')
                自身.ctx.credentials.删除记录(授予键)
                自身._吊销(解析['token'])
            自身._尝试=None
            自身._已变()
            return 自身.获取状态()
        finally:
            自身._移除中=None
            完成.set()

    def 监视(自身,信号):
        """含完整初值的快照流。"""
        已改=[True]
        唤醒=threading.Event()
        def 变更():
            """标脏。"""
            已改[0]=True
            唤醒.set()
        自身._监听者.add(变更)
        try:
            while not 自身._已关闭 and not 已中止(信号):
                if 已改[0]:
                    已改[0]=False
                    yield 自身.获取状态()
                    continue
                唤醒.wait(0.05)
                唤醒.clear()
        finally:
            自身._监听者.discard(变更)

    def _吊销(自身,令牌):
        """后台吊销。"""
        if 自身._已关闭:
            return
        完成=threading.Event()
        自身._吊销表.add(完成)
        def 跑():
            """吊销结束即摘掉。"""
            try:
                吊销账号(自身._来源,令牌,自身._登出政策,自身._登出寿命.信号,{**自身._请求头,**自身._客户端头})
            finally:
                自身._吊销表.discard(完成)
                完成.set()
        threading.Thread(target=跑,daemon=True).start()

    def _作废细节(自身):
        """换寿命。"""
        自身._最近配置档=None
        自身._细节寿命.中止()
        自身._细节寿命=中止控制器()

    def _已变(自身):
        """通知监视者。"""
        for 监听 in list(自身._监听者):
            监听()

    def _更新(自身,尝试,值):
        """合并尝试视图；授权 URL 不保留到后续阶段。"""
        其余=dict(尝试['view'])
        其余.pop('authorizeUrl',None)
        其余.update(值)
        尝试['view']=其余
        自身._已变()

    def _运行(自身,会话,尝试):
        """浏览器回调与换码。"""
        网页服务=自身.所属上下文.获取服务('webServer',False)
        if 网页服务 is None:
            raise 平台认证错误('protocol')
        校验器=secrets.token_urlsafe(32)
        状态=secrets.token_urlsafe(32)
        挑战=base64.urlsafe_b64encode(hashlib.sha256(校验器.encode('ascii')).digest()).rstrip(b'=').decode('ascii')
        授权标识=[None]
        码任务=操作任务()
        截止控制=中止控制器()
        过期于=int(time.time()*1000)+自身._尝试超时
        句柄=截止(会话['signal'],自身._尝试超时,'account-attempt')
        信号=句柄.信号
        def 中止码():
            """过期则拒绝换码。"""
            码任务.拒绝(平台认证错误('expired'))
        def 看中止():
            """上游中止时拒绝。"""
            while not 已中止(信号):
                time.sleep(0.05)
            中止码()
        threading.Thread(target=看中止,daemon=True).start()
        try:
            def 处理(请求,响应):
                """OAuth 回调。"""
                原始=请求.url if hasattr(请求,'url') else (请求.get('url') if isinstance(请求,dict) else '/')
                try:
                    解析=urlparse(原始 if '://' in str(原始) else 'http://127.0.0.1'+str(原始))
                except ValueError:
                    响应.writeHead(400,{'cache-control':'no-store'}).end()
                    return
                查询=parse_qs(解析.query)
                收到码=(查询.get('code') or [None])[0]
                收到状态=(查询.get('state') or [''])[0]
                状态字节=收到状态.encode('utf-8')
                期望字节=状态.encode('utf-8')
                合法状态=len(状态字节)==len(期望字节) and hmac.compare_digest(状态字节,期望字节)
                方法=请求.method if hasattr(请求,'method') else (请求['method'] if isinstance(请求,dict) else '')
                if (方法!='GET' or 解析.path!='/oauth/callback' or not 合法状态 or not 收到码
                        or len(查询.get('state') or [])!=1 or len(查询.get('code') or [])!=1):
                    响应.writeHead(400,{'cache-control':'no-store'}).end()
                    return
                if 已中止(信号) or 尝试.get('callback') is not None or 尝试['view']['phase']!='waiting-browser':
                    响应.writeHead(410,{'cache-control':'no-store'}).end()
                    return
                尝试['callback']=响应
                码任务.兑现(收到码)
            def 登记效果():
                """挂精确回调路由。"""
                return 网页服务.register({'kind':'exact','path':'/oauth/callback','handler':处理})
            尝试['disposeCallback']=自身.所属上下文.副作用(登记效果,'account: browser callback')
            若已中止则抛出(信号)
            重定向=尝试['origin']+'/oauth/callback'
            句柄2=截止(信号,自身._请求超时,'account-init')
            try:
                初值=初始化形态(自身._请求('auth_init',{
                    'code_challenge':挑战,
                    'code_challenge_method':'S256',
                    'state':状态,
                    'redirect_uri':重定向,
                    'locale':尝试['locale'],
                    'login_source':尝试['loginSource'],
                },句柄2.信号))
            finally:
                句柄2.释放()
            if 初值 is None:
                自身._拒绝载荷('auth_init')
            授权网址=浏览器网址(初值['authorize_url'],自身._来源,'/dsh/authorize',自身._改写浏览器)
            授权标识[0]=初值['authorize_id']
            若已中止则抛出(信号)
            现在=int(time.time()*1000)
            过期于=min(过期于,现在+int(初值['expires_in']*1000))
            剩余=过期于-现在
            if 剩余<=0:
                raise 平台认证错误('expired')
            自身._更新(尝试,{'phase':'waiting-browser','authorizeUrl':授权网址,'expiresAt':过期于})
            收到码=码任务.等待()
            若已中止则抛出(信号)
            自身._更新(尝试,{'phase':'exchanging'})
            def 设备变更(当前):
                """没有设备记录则新建。"""
                if 当前 is None:
                    return {'kind':'grant','payload':{'id':str(uuid.uuid4())}}
                return None
            设备记录=自身.ctx.credentials.修改记录(设备键,设备变更)
            if 设备记录 is None or 设备记录.get('kind')!='grant':
                raise 平台认证错误('storage')
            身份=设备记录['payload']
            if not isinstance(身份,dict) or not isinstance(身份.get('id'),str):
                raise 平台认证错误('storage')
            系统=sys.platform
            句柄3=截止(信号,自身._请求超时,'account-exchange')
            try:
                换得=交换形态(自身._请求('auth_exchange',{
                    'code':收到码,
                    'code_verifier':校验器,
                    'redirect_uri':重定向,
                    'device_id':身份['id'],
                    'device_model':系统+'-'+platform.machine(),
                    'os_version':系统+' '+platform.release(),
                },句柄3.信号))
            finally:
                句柄3.释放()
            if 换得 is None:
                自身._拒绝载荷('auth_exchange')
            完成=浏览器网址(换得['authorized_url'],自身._来源,'/dsh/authorized',自身._改写浏览器)
            完成解析=urlparse(完成)
            查询=parse_qs(完成解析.query)
            查询['login_source']=[尝试['loginSource']]
            扁=[]
            for 键,值列表 in 查询.items():
                for 值 in 值列表:
                    扁.append((键,值))
            尝试['completionUrl']=urlunparse((完成解析.scheme,完成解析.netloc,完成解析.path,'',urlencode(扁),''))
            if int(time.time()*1000)>=过期于:
                raise 平台认证错误('expired')
            若已中止则抛出(信号)
            if 换得.get('user') is not None:
                try:
                    尝试['initialProfile']={'token':换得['token'],'value':{'status':'ready','value':投影配置档(换得['user'])}}
                except 平台认证错误:
                    pass
            自身._更新(尝试,{'phase':'committing'})
            try:
                def 写入授予(当前):
                    """提交授予记录。"""
                    return {'kind':'grant','payload':{'version':1,'token':换得['token'],'issuer':自身._来源}}
                自身.ctx.credentials.修改记录(授予键,写入授予)
            except Exception:
                raise 平台认证错误('storage')
        except Exception as 错误:
            if 已中止(截止控制.信号) or (isinstance(错误,平台认证错误) and 错误.code=='expired'):
                raise 平台认证错误('expired')
            raise
        finally:
            if 已中止(信号) and 授权标识[0] is not None:
                自身._取消请求(授权标识[0],校验器)
            句柄.释放()

    def _拒绝载荷(自身,阶段):
        """载荷校验失败。"""
        print('[deepseek-account] 载荷已拒绝',{'stage':阶段})
        raise 平台认证错误('protocol')

    def _取消请求(自身,授权标识,校验器):
        """后台取消远端授权。"""
        if 自身._已关闭:
            return
        完成=threading.Event()
        自身._吊销表.add(完成)
        def 跑():
            """失败不回滚本地取消。"""
            try:
                自身._请求('auth_cancel',{'authorize_id':授权标识,'code_verifier':校验器},自身._登出寿命.信号)
            except 平台认证错误:
                pass
            finally:
                自身._吊销表.discard(完成)
                完成.set()
        threading.Thread(target=跑,daemon=True).start()

    def _请求(自身,方法,体,信号):
        """带超时的平台请求。"""
        句柄=截止(信号,自身._请求超时,'account-request')
        try:
            return 请求平台(自身._来源,方法,体,句柄.信号,{**自身._请求头,**自身._客户端头})
        finally:
            句柄.释放()

    def _失败回调(自身,尝试):
        """失败页或 204。"""
        回调=尝试.get('callback')
        if 回调 is None:
            return
        if 尝试['loginSource']=='web':
            一次性=secrets.token_urlsafe(16)
            消息='登录失败，请关闭此标签页并在原页面重试。' if 尝试['locale']=='zh_CN' else 'Sign-in failed. Close this tab and try again in the original tab.'
            语言='zh-CN' if 尝试['locale']=='zh_CN' else 'en'
            正文='<!doctype html><html lang="'+语言+'"><meta charset="utf-8"><title>'+消息+'</title>'+'<body><p>'+消息+'</p><script nonce="'+一次性+'">window.close()</script></body></html>'
            回调.writeHead(200,{
                'content-type':'text/html; charset=utf-8',
                'cache-control':'no-store',
                'content-security-policy':"default-src 'none'; script-src 'nonce-"+一次性+"'; frame-ancestors 'none'",
                'referrer-policy':'no-referrer',
            }).end(正文)
        else:
            回调.writeHead(204,{'cache-control':'no-store'}).end()

默认=平台账号
Config=配置
name=名称
inject=依赖
default=默认
平台账号.inject=依赖
平台账号.Config=配置
