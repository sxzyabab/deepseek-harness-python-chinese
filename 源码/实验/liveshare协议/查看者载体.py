'查看页载体。Python 没有浏览器函数源，安装写在页面全局上'
import json,re,secrets
from urllib.parse import quote,urlsplit

__all__=['查看者全局名','安装查看者载体','查看者载体脚本','页面全局']

查看者全局名='__DSH_LIVESHARE_VIEWER__'
页面全局={'fetch':None,'document':None,'location':None}
码形=re.compile(r'^[a-z][a-z0-9-]*(?:/[a-z0-9-]+)*$')
载体状态={408,429,502,503,504}
载体码={'stream-not-found','gateway/cancelled'}
转发路由=('/open-in-app/apps','/api/present.host')

class 载体错误(Exception):
    '线路失败。dshRemoteStreamFailure 是页面消费的标记'
    def __init__(自身,消息,失败):
        '记下标记'
        super().__init__(消息)
        自身.dshRemoteStreamFailure=失败

def 是记录(值):
    '普通对象'
    return isinstance(值,dict)

def 已中止(信号):
    '无信号视为未中止'
    if 信号 is None:
        return False
    if hasattr(信号,'aborted'):
        return bool(信号.aborted)
    if hasattr(信号,'is_set'):
        return 信号.is_set()
    return False

def 段偏移(路径名,路由):
    '路由从路径段开始的偏移。只出现在更长段里则没有'
    起点=0
    while True:
        位置=路径名.find(路由,起点)
        if 位置==-1:
            return None
        下一=路径名[位置+len(路由):位置+len(路由)+1]
        if 下一=='' or 下一=='/':
            return 位置
        起点=位置+1

def 转发路径(路径名,方法):
    '只转发列出的只读所有者路由'
    if 方法!='GET':
        return None
    for 路由 in 转发路由:
        位置=段偏移(路径名,路由)
        if 位置 is not None:
            return 路径名[位置:]
    return None

def 安装查看者载体(选项):
    '在当前页面全局上安装查看者标记和传输。取回由页面全局的 fetch 提供'
    下一流=[(secrets.randbits(32)%0x7fffff00)+1]
    目标=选项['basePath']+'/__share/rpc' if 选项['shareId']=='' else 选项['basePath']+'/__share/rpc?shareId='+quote(选项['shareId'],safe="-_.!~*'()")
    def 载体(消息):
        '可重试的载体丢失'
        return 载体错误(消息,{'kind':'carrier'})
    def 拒绝说明(应答):
        '从应答里取出码和消息'
        if not 是记录(应答.get('body')):
            return {}
        值=应答['body'].get('error')
        嵌套=是记录(值)
        码=值.get('code') if 嵌套 else 值
        消息=值.get('message') if 嵌套 else 应答['body'].get('message')
        结果={}
        if isinstance(码,str) and 码形.fullmatch(码) is not None:
            结果['code']=码
        if isinstance(消息,str):
            结果['message']=消息
        return 结果
    def 远程(应答,主题):
        '终态拒绝'
        说明=拒绝说明(应答)
        码=说明.get('code','liveshare/read-refused')
        消息=说明.get('message',主题+' refused (HTTP '+str(应答['status'])+')')
        错误=载体错误(消息,{'kind':'remote','code':码,'details':{'status':应答['status']}})
        错误.name=码
        return 错误
    def 投递(请求,主题,信号=None):
        '向中继发一帧。页面自己的取消不是丢失'
        取回=页面全局.get('原fetch') or 页面全局.get('fetch')
        if not callable(取回):
            raise 载体(主题+': Relay unreachable')
        try:
            应答=取回(目标,请求,信号)
        except Exception as 错误:
            if 已中止(信号):
                raise
            raise 载体(主题+': Relay unreachable') from 错误
        if not 是记录(应答) or 'status' not in 应答:
            raise 载体(主题+': Relay answered without a body')
        return {'status':应答['status'],'body':应答.get('body')}
    def 可读(应答,主题):
        '200 且有对象体才可读，否则按状态决定重试或拒绝'
        if 应答['status']==200:
            if 是记录(应答.get('body')):
                return 应答['body']
            raise 载体(主题+': Relay answered without a body')
        码=拒绝说明(应答).get('code')
        if 应答['status'] not in (401,403) and (应答['status'] in 载体状态 or (码 is not None and 码 in 载体码)):
            raise 载体(主题+': '+(码 if 码 is not None else 'HTTP '+str(应答['status'])))
        raise 远程(应答,主题)
    def 失败帧(帧,主题):
        '帧里的 failure。没有则不是失败'
        值=帧.get('failure')
        if not 是记录(值):
            return None
        码=值['code'] if isinstance(值.get('code'),str) else 'liveshare/read-refused'
        消息=值['message'] if isinstance(值.get('message'),str) else 主题
        if 码 in 载体码:
            return 载体(消息)
        细节=值['details'] if 是记录(值.get('details')) else {}
        错误=载体错误(消息,{'kind':'remote','code':码,'details':细节})
        错误.name=码
        return 错误
    def 转发(路径,初始):
        '读一条转发的所有者路由，按普通 HTTP 应答交回'
        体={}
        if isinstance(初始,dict) and isinstance(初始.get('body'),str):
            体=json.loads(初始['body'])
        信号=初始.get('signal') if isinstance(初始,dict) else None
        应答=投递({'op':'call','path':路径,'body':体},路径,信号)
        return {'status':应答['status'],'body':应答.get('body'),'headers':{'content-type':'application/json'}}
    原取回=页面全局.get('fetch')
    页面全局['原fetch']=原取回
    def 载体取回(输入,初始=None):
        '转发集合里的同源 GET 走所有者，其余交给原来的 fetch'
        路径名=None
        方法='GET'
        try:
            页源=None if not isinstance(页面全局.get('location'),dict) else 页面全局['location'].get('origin')
            网址=输入['url'] if isinstance(输入,dict) and 'url' in 输入 else str(输入)
            基准=None if not isinstance(页面全局.get('document'),dict) else 页面全局['document'].get('baseURI')
            解析=urlsplit(网址 if '://' in 网址 or 基准 is None else 基准.rstrip('/')+'/'+网址.lstrip('/'))
            if 页源 is not None and (解析.scheme+'://'+解析.netloc)==页源:
                路径名=解析.path
            方法名=None if not isinstance(初始,dict) else 初始.get('method')
            if 方法名 is None and isinstance(输入,dict):
                方法名=输入.get('method')
            方法=(方法名 or 'GET').upper()
        except Exception:
            路径名=None
        路径=None if 路径名 is None else 转发路径(路径名,方法)
        if 路径 is None:
            if not callable(原取回):
                raise 载体('fetch: Relay unreachable')
            return 原取回(输入,初始)
        return 转发(路径,初始)
    def 取调用(输入,初始):
        '连接调用。拒绝按所有者给出的码交回'
        基准=None if not isinstance(页面全局.get('document'),dict) else 页面全局['document'].get('baseURI')
        网址=输入['url'] if isinstance(输入,dict) and 'url' in 输入 else str(输入)
        解析=urlsplit(网址 if '://' in 网址 or 基准 is None else 基准.rstrip('/')+'/'+网址.lstrip('/'))
        标记=解析.path.rfind('/api/')
        路径=解析.path if 标记==-1 else 解析.path[标记:]
        体=None
        if isinstance(初始,dict) and isinstance(初始.get('body'),str):
            体=json.loads(初始['body'])
        信号=初始.get('signal') if isinstance(初始,dict) else None
        应答=投递({'op':'call','path':路径,'body':体},路径,信号)
        if 应答['status']==200 and 是记录(应答.get('body')):
            return {'status':200,'body':应答['body']}
        说明=拒绝说明(应答)
        码=说明.get('code','liveshare/relay-error')
        消息=说明.get('message','Relay answered HTTP '+str(应答['status']))
        关联=''
        if 是记录(体) and isinstance(体.get('rpcId'),str):
            关联=体['rpcId']
        return {'status':200,'body':{
            'type':'server-response',
            'rpcId':关联,
            'result':{'ok':False,'error':{'code':码,'message':消息,'details':{'status':应答['status']}}},
        }}
    def 打开流(端点,载荷,信号):
        '轮询一条逻辑流。拒绝打开时不把丢失流当成可重试'
        标识=下一流[0]
        下一流[0]+=1
        if 已中止(信号):
            raise 载体错误('aborted',{'kind':'carrier'})
        已取消=[False]
        def 取消():
            '至多通知所有者一次'
            if 已取消[0]:
                return
            已取消[0]=True
            try:
                投递({'op':'stream-cancel','id':标识},端点)
            except Exception:
                return
        try:
            打开=投递({'op':'stream-open','id':标识,'endpoint':端点,'payload':载荷},端点,信号)
        except Exception:
            if 已中止(信号):
                取消()
            raise
        if 已中止(信号):
            取消()
            raise 载体错误('aborted',{'kind':'carrier'})
        try:
            打开体=可读(打开,端点)
        except Exception:
            if 打开['status']==200:
                取消()
            raise
        拒绝打开=失败帧(打开体,端点)
        if 拒绝打开 is not None:
            raise 拒绝打开
        try:
            while not 已中止(信号):
                帧=可读(投递({'op':'stream-next','id':标识},端点,信号),端点)
                if 已中止(信号):
                    raise 载体错误('aborted',{'kind':'carrier'})
                失败=失败帧(帧,端点)
                if 失败 is not None:
                    raise 失败
                if 帧.get('end') is True:
                    return
                if 帧.get('pending') is True:
                    continue
                if isinstance(帧.get('values'),list):
                    for 值 in 帧['values']:
                        if 已中止(信号):
                            raise 载体错误('aborted',{'kind':'carrier'})
                        yield 值
                    continue
                yield 帧.get('value')
        finally:
            if not 已中止(信号):
                取消()
    页面全局[查看者全局名]={'basePath':选项['basePath'],'shareId':选项['shareId'],'sessionId':选项['sessionId']}
    页面全局['__DSH_TRANSPORT__']={'fetch':取调用,'openStream':打开流}
    页面全局['fetch']=载体取回

def 查看者载体脚本(选项):
    '转义选项里的小于号，避免它关掉外面的 script 标签。Python 没有浏览器函数源，返回值不能放进页面'
    参数=json.dumps(选项,ensure_ascii=True,separators=(',',':')).replace('<','\\u003c')
    return '(安装查看者载体)('+参数+');'
