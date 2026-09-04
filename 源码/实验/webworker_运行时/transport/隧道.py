"""postMessage 隧道的 worker 端。它拥有分发通道，以及在宿主树就绪前
暂存请求的队列。

对齐上游 `webworker-runtime/src/transport/tunnel.ts`。公开面仅中文名。
"""
import json as _json#序列化boot载荷
from urllib.parse import urlparse as 解析网址#解析请求URL
from .帧 import 解析入站帧#帧解析
from .合成http import 创建合成交换#合成HTTP

__all__=['api前缀','合成主机','描述失败','隧道服务器']#仅中文公开名

api前缀='/api'#API路径前缀
合成主机='127.0.0.1'#合成Host

def 描述失败(原因):#渲染嵌套失败
    """把失败及其嵌套内容全部渲染出来。"""
    已见=set()#防环集合
    行们=[]#输出行
    def 行走(值,深度):#深度遍历
        """递归展开错误。"""
        if 值 is None or id(值) in 已见 or 深度>6:#跳过空环过深
            return#结束
        已见.add(id(值))#标记已见
        缩进='  '*深度#缩进
        if not isinstance(值,BaseException):#非Error
            渲染=值 if isinstance(值,str) else repr(值)#可读渲染
            行们.append(f'{缩进}{渲染}')#记一行
            return#结束
        行们.append(f'{缩进}{type(值).__name__}: {值}')#记错误行
        内错误们=getattr(值,'exceptions',None)#聚合错误列表
        if 内错误们 is not None:#展开聚合
            for 内 in 内错误们:#逐条
                行走(内,深度+1)#展开
        行走(getattr(值,'__cause__',None),深度+1)#展开cause
    行走(原因,0)#从根走
    return '\n'.join(行们)#拼多行

def 转可转移(字节们):#拷为可转移缓冲
    """把字节拷进精确大小的缓冲，以便可转移。"""
    return bytes(字节们)#精确拷贝

class 缓冲汇:#缓冲汇
    """记录响应帧，便于丢弃路由通道的认证拒绝。"""

    def __init__(自身):#构造
        """空记录。"""
        自身._调用们=[]#已记录调用
        自身._目标=None#冲刷目标
        自身._落定结果=None#落定结果
        自身.汇={#对外汇
            'head':自身._记头,#记头
            'chunk':自身._记块,#记块
            'end':自身._记结束,#记结束
            'fail':自身._记失败,#记失败
        }#汇结束

    def _记录(自身,调用):#记录或转发
        """尚未冲刷则入队，已冲刷则立即。"""
        if 自身._目标 is None:#尚未冲刷则入队
            自身._调用们.append(调用)#入队
        else:#已冲刷则立即
            调用()#立即

    def _记头(自身,状态,头们):#记头
        """延后或立即发头并流式落定。"""
        def 调用():#延后调用
            """转发头。"""
            if 自身._目标 is not None:#有目标
                自身._目标['head'](状态,头们)#发头
        自身._记录(调用)#记录
        自身._落定结果={'streamed':True,'status':状态}#流式落定

    def _记块(自身,字节们):#记块
        """延后或立即发块。"""
        def 调用():#延后调用
            """转发块。"""
            if 自身._目标 is not None:#有目标
                自身._目标['chunk'](字节们)#发块
        自身._记录(调用)#记录

    def _记结束(自身,载荷=None):#记结束
        """延后或立即结束。"""
        def 调用():#延后调用
            """转发结束。"""
            if 自身._目标 is not None:#有目标
                自身._目标['end'](载荷)#结束
        自身._记录(调用)#记录
        自身._落定结果={'streamed':载荷 is None,'status':200 if 载荷 is None else 载荷.get('status',200)}#落定

    def _记失败(自身,消息):#记失败
        """延后或立即失败。"""
        def 调用():#延后调用
            """转发失败。"""
            if 自身._目标 is not None:#有目标
                自身._目标['fail'](消息)#失败
        自身._记录(调用)#记录
        自身._落定结果={'streamed':True,'status':500}#失败落定

    def 冲刷到(自身,目标):#冲刷到真实汇
        """把已记录的一切发给真实 sink，并透传后续调用。"""
        自身._目标=目标#绑定目标
        for 调用 in 自身._调用们[:]:#回放记录
            自身._调用们.pop(0)#取出
            调用()#执行

class 隧道服务器:#隧道服务器
    """每个 worker 一条隧道；先把 handleMessage 接到 onmessage。"""

    def __init__(自身,选项):#构造
        """记下端口与监听器工厂。"""
        自身._端口=选项['port']#记下端口
        自身._请求监听器=选项['requestListener']#记下监听器工厂
        自身._特权方法=选项.get('privilegedMethods')#记下特权集
        自身._一元api通道=选项.get('unaryApiLane') or 'route'#默认走路由
        自身._队列=[]#启动前队列
        自身._进行中={}#进行中表
        自身._缝合=None#宿主缝合
        自身._失败=None#启动失败文案
        自身._监听器=None#已解析监听器

    def 处理消息(自身,数据):#处理入站消息
        """接受一个 postMessage 载荷。"""
        帧=解析入站帧(数据)#校验帧
        if 帧['t']=='init':#重复init
            raise Exception('webworker tunnel: duplicate init frame; the tunnel is already open')#拒绝
        if 帧['t']=='abort':#中止
            进行=自身._进行中.get(帧['id'])#取进行中
            if 进行 is not None:#有
                进行['abort']()#中止
            自身._进行中.pop(帧['id'],None)#从表移除
            for 索引,请求 in enumerate(自身._队列):#找队列项
                if 请求['id']==帧['id']:#命中
                    自身._队列.pop(索引)#移除排队
                    break#停止
            return#结束
        if 自身._失败 is not None:#已失败则拒绝
            自身._拒绝(帧,自身._失败)#拒绝
            return#结束
        if 自身._缝合 is None:#尚未serve
            自身._队列.append(帧)#入队
            return#等待
        自身._分发帧(帧)#立即分发

    def 服务(自身,缝合):#开始服务
        """开始服务：排空启动期间入队的一切。"""
        自身._缝合=缝合#挂缝合面
        print(f"webworker tunnel: serving (unary /api lane={自身._一元api通道}"
              f"{' with 401/403 retry' if 自身._一元api通道=='route' else ''}, "
              f"privileged set={'none' if 自身._特权方法 is None else len(自身._特权方法)}, "
              f"queued={len(自身._队列)})")#日志
        while 自身._队列:#排空队列
            自身._分发帧(自身._队列.pop(0))#分发

    def 失败(自身,原因):#启动失败
        """拒绝所有已排队与未来请求。"""
        消息=描述失败(原因)#渲染文案
        自身._失败=消息#记下失败
        while 自身._队列:#拒绝排队项
            自身._拒绝(自身._队列.pop(0),消息)#拒绝

    def _发送(自身,帧,转移=None):#发帧
        """经端口发出。"""
        自身._端口['postMessage'](帧,转移) if isinstance(自身._端口,dict) else 自身._端口.postMessage(帧,转移)#发帧

    def _拒绝(自身,帧,消息):#拒绝一帧
        """以流错误或 503 拒绝。"""
        if 帧['t']=='stream-open':#开流拒绝
            自身._发送({'t':'stream-error','id':帧['id'],'failure':{'kind':'carrier','message':消息}})#发流错误
            return#结束
        正文=转可转移(消息.encode('utf-8'))#编码正文
        自身._发送({'t':'res','id':帧['id'],'status':503,'headers':{'content-type':'text/plain; charset=utf-8'},'body':正文,'message':消息},[正文])#发503

    def _分发帧(自身,帧):#分发帧
        """开流或普通请求。"""
        if 帧['t']=='stream-open':#开流
            自身._服务流(帧)#开流
        else:#普通请求
            自身._服务请求(帧)#请求

    def _服务流(自身,帧):#服务开流
        """打开并转发 Gateway Remote 流。"""
        if 自身._缝合 is None:#尚未就绪
            自身._拒绝(帧,'webworker tunnel: Remote stream requested before the host tree is serving')#拒绝
            return#结束
        缝合=自身._缝合#锁定缝合
        已中止=[False]#取消标志
        def 中止():#中止
            """标记中止。"""
            已中止[0]=True#中止
        自身._进行中[帧['id']]={'abort':中止}#登记中止
        try:#打开并转发
            源=缝合['openStream'](帧['endpoint'],帧['payload'],{'aborted':False})#开源
            for 值 in 源:#逐项
                if 已中止[0]:#已中止
                    return#结束
                自身._发送({'t':'stream-item','id':帧['id'],'value':值})#发项
            if not 已中止[0]:#正常结束
                自身._发送({'t':'stream-end','id':帧['id']})#结束帧
        except Exception as 错误:#失败
            if not 已中止[0]:#未中止才报错
                失败=缝合['streamFailure'](错误)#映射失败
                自身._发送({'t':'stream-error','id':帧['id'],'failure':{'kind':'remote',**失败}})#发流错误
        finally:#清理
            自身._进行中.pop(帧['id'],None)#移除登记

    def _为请求建汇(自身,标识):#为请求建汇
        """构建响应汇。"""
        def 发头(状态,头们):#发流式头
            """头帧。"""
            自身._发送({'t':'res-head','id':标识,'status':状态,'headers':头们})#头帧
        def 发块(字节们):#发块
            """块帧。"""
            缓冲=转可转移(字节们)#可转移
            自身._发送({'t':'res-chunk','id':标识,'chunk':缓冲},[缓冲])#块帧
        def 结束(载荷=None):#结束
            """结束帧或一元应答。"""
            if 载荷 is None:#流式结束
                自身._发送({'t':'res-end','id':标识})#结束帧
            else:#一元应答
                正文=None if 载荷.get('body') is None else 转可转移(载荷['body'])#可选正文
                自身._发送({'t':'res','id':标识,'status':载荷['status'],'headers':载荷['headers'],'body':正文},None if 正文 is None else [正文])#完整响应
            自身._进行中.pop(标识,None)#清理登记
        def 失败(消息):#失败
            """错误帧。"""
            自身._发送({'t':'res-err','id':标识,'message':消息})#错误帧
            自身._进行中.pop(标识,None)#清理登记
        return {'head':发头,'chunk':发块,'end':结束,'fail':失败}#响应汇

    def _路径帧(自身,帧):#规范化路径帧
        """页面发绝对 URL；路由处理器把 req.url 当路径读。"""
        解析=解析网址(帧['url'] if '://' in 帧['url'] else f'http://{合成主机}{帧["url"]}')#解析
        路径=解析.path#纯路径
        查询=f'?{解析.query}' if 解析.query else ''#查询
        头={**帧['headers'],'host':合成主机}#补host
        return {'frame':{**帧,'url':f'{路径}{查询}','headers':头},'path':路径}#返回

    def _服务请求(自身,帧):#服务普通请求
        """路由 boot、API 或监听器。"""
        汇=自身._为请求建汇(帧['id'])#响应汇
        try:#路由
            规范=自身._路径帧(帧)#规范化
            if 规范['path']=='/__boot__':#启动载荷
                自身._服务boot(帧,汇)#boot
                return#结束
            if 规范['path'].startswith(f'{api前缀}/'):#API
                自身._服务api(帧,规范['frame'],规范['path'],汇)#API
                return#结束
            自身._喂入(规范['frame'],汇)#其余走路由表
        except Exception as 原因:#异常
            汇['fail'](str(原因) if isinstance(原因,BaseException) else str(原因))#失败帧

    def _取监听器(自身):#获取监听器
        """监听器捕获一次后复用。"""
        if 自身._监听器 is None:#惰性解析
            自身._监听器=自身._请求监听器()#解析
        return 自身._监听器#返回

    def _喂入(自身,帧,汇,进入=None):#喂入监听器
        """经被捕获的监听器喂入真实路由表。"""
        交换=创建合成交换(帧,进入 or 汇)#合成对
        自身._进行中[帧['id']]=交换#登记可中止
        监听器=自身._监听器#已缓存监听器
        if 监听器 is not None:#已就绪
            监听器(交换['req'],交换['res'])#同步调用
            return 交换#返回
        解析=自身._取监听器()#等待绑定
        中止面=交换['aborted']#中止读取
        已中止=中止面() if callable(中止面) else 中止面#是否中止
        if not 已中止:#未中止才喂
            解析(交换['req'],交换['res'])#喂入
        return 交换#先返回交换

    def _服务boot(自身,帧,汇):#服务启动载荷
        """GET /__boot__ 的启动载荷。"""
        if 自身._缝合 is None:#须已serve
            raise Exception('webworker tunnel: boot payload requested before the host tree is serving')#拒绝
        if 帧['method']!='GET':#仅GET
            汇['end']({'status':405,'headers':{'allow':'GET'}})#方法不允许
            return#结束
        正文=_json.dumps(自身._缝合['bootPayload']()).encode('utf-8')#序列化载荷
        汇['end']({'status':200,'headers':{'content-type':'application/json; charset=utf-8','cache-control':'no-store'},'body':正文})#200应答

    def _服务api(自身,原始,路径化,路径,汇):#服务API
        """一元 /api：保留路由通道围栏，401/403 时回退直达。"""
        方法=路径[len(api前缀)+1:]#方法名
        if 自身._一元api通道=='direct' or (自身._特权方法 is not None and 方法 in 自身._特权方法):#直达或特权
            自身._服务直达(原始,汇)#直达通道
            return#结束
        缓冲=缓冲汇()#缓冲拒绝决策
        交换=自身._喂入(路径化,汇,缓冲.汇)#先走路由
        结果=缓冲._落定结果#落定结果
        中止面=交换['aborted']#中止
        已中止=中止面() if callable(中止面) else 中止面#是否中止
        if 结果 is None or 已中止:#已中止或未落定
            return#结束
        if 结果['status'] in (401,403):#认证/信任拒绝
            print(f"webworker tunnel: route lane refused {方法} with {结果['status']}; answering on the direct lane")#调试
            自身._服务直达(原始,汇)#改直达
            return#结束
        缓冲.冲刷到(汇)#接受则冲刷到页

    def _服务直达(自身,帧,汇):#直达fetch
        """直达 fetch 处理器。"""
        if 自身._缝合 is None:#须已serve
            raise Exception('webworker tunnel: direct fetch requested before the host tree is serving')#拒绝
        已中止=[False]#取消标志
        def 中止():#中止
            """标记中止。"""
            已中止[0]=True#中止
        自身._进行中[帧['id']]={'abort':中止}#登记中止
        响应=自身._缝合['directFetch']({'method':帧['method'],'url':帧['url'],'headers':帧['headers'],'body':帧.get('body')})#直达调用
        响应头=dict(响应.get('headers') or {})#响应头字典
        类型=响应头.get('content-type','')#内容类型
        流式=响应.get('body') is not None and 类型.startswith('text/event-stream')#是否SSE
        if not 流式:#一元
            缓冲=响应.get('body')#正文
            汇['end']({'status':响应.get('status',200),'headers':响应头,'body':None if not 缓冲 else 缓冲})#一帧答完
            return#结束
        汇['head'](响应.get('status',200),响应头)#流式头
        for 块 in 响应.get('body') or ():#泵流
            if 已中止[0]:#已中止
                break#停止
            汇['chunk'](块)#发块
        汇['end']()#流式结束
