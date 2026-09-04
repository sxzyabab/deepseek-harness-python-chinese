"""面向传输、协议与语义空 LLM 恢复测试的可编脚本 OpenAI 兼容 HTTP/SSE 服务器。

对齐上游 `llm-mock-server/src/index.ts`。公开面仅中文名。
每个已接受的 chat-completions 请求消费一个行为；服务器从不重试或解读 harness 策略。
同步 + ThreadingHTTPServer，无 asyncio。
"""
import json,os,socket,threading,time#JSON、随机种子、网络、线程与延迟
from http.server import BaseHTTPRequestHandler as 基处理器,ThreadingHTTPServer as 线程HTTP服务器#HTTP 服务

__all__=[#仅中文公开名
    '模拟LLM行为名表','默认模拟LLM随机权重','模拟LLM定时器延迟上限毫秒',
    '启动模拟LLM服务器','应用',
]#公开面结束

模拟LLM行为名表=(#全部可脚本行为名
    'connection_reset','stream_disconnect','empty','empty_body','stream_eof',
    'partial_eof','partial_disconnect','stall','malformed_json','malformed_event',
    'wrong_content_type','rate_limit','server_error','service_unavailable',
    'auth_error','invalid_request','context_overflow','quota_exceeded',
    'success','reasoning_success','tool_call_success','max_tokens','slow_success','random',
)#行为名结束
默认模拟LLM随机权重={#默认随机权重
    'success':48,'slow_success':10,'max_tokens':2,'connection_reset':5,
    'stream_disconnect':5,'partial_disconnect':10,'empty':5,'stall':2,
    'rate_limit':5,'server_error':4,'service_unavailable':2,'partial_eof':1,'malformed_json':1,
}#默认权重结束
模拟LLM定时器延迟上限毫秒=2_147_483_647#定时器上限
默认成功文本='mock response recovered'#默认成功文本
默认部分文本='discarded partial response'#默认部分文本
默认推理文本='mock reasoning'#默认推理文本
具体行为集=frozenset(名 for 名 in 模拟LLM行为名表 if 名!='random')#具体行为集
Error=Exception#错误别名

def 有界整数(名称,值,最小,最大):#校验有界整数
    """校验有界整数。"""
    if not isinstance(值,int) or isinstance(值,bool) or 值<最小 or 值>最大:#越界
        raise Error(f'llm-mock-server: {名称} must be an integer between {最小} and {最大}')#越界
    return 值#返回有界整数

def 解析选项(选项):#解析服务器选项
    """解析并校验服务器选项。"""
    主机=选项.get('host') or '127.0.0.1'#主机
    端口=有界整数('port',选项.get('port',0),0,65_535)#端口
    分片大小=有界整数('chunkSize',选项.get('chunkSize',8),1,2**53-1)#分片大小
    分片延迟=有界整数('chunkDelayMs',选项.get('chunkDelayMs',25),0,模拟LLM定时器延迟上限毫秒)#分片延迟
    断开延迟=有界整数('disconnectDelayMs',选项.get('disconnectDelayMs',10),0,模拟LLM定时器延迟上限毫秒)#断开延迟
    重试等待=有界整数('retryAfterMs',选项.get('retryAfterMs',1_000),1,模拟LLM定时器延迟上限毫秒)#重试等待
    种子源=选项.get('randomSeed')#随机种子
    if 种子源 is None:#生成种子
        种子源=int.from_bytes(os.urandom(4),'little')#4 字节种子
    随机种子=有界整数('randomSeed',种子源,0,0xffff_ffff)#种子
    成功文本=选项.get('successText') or 默认成功文本#成功文本
    部分文本=选项.get('partialText') or 默认部分文本#部分文本
    推理文本=选项.get('reasoningText') or 默认推理文本#推理文本
    工具名=选项.get('toolName') or 'mock_tool'#工具名
    工具参数=选项.get('toolArguments') or '{"value":"mock"}'#工具参数
    序列=选项.get('sequence')#行为序列
    if 主机=='':#空主机
        raise Error('llm-mock-server: host must not be empty')#空主机
    if not 序列:#空序列
        raise Error('llm-mock-server: sequence must not be empty')#空序列
    末项=序列[-1]#末项行为
    if 选项.get('apiKey')=='':#空密钥
        raise Error('llm-mock-server: apiKey must not be empty')#空密钥
    if 成功文本=='' or 部分文本=='' or 推理文本=='' or 工具名=='':#空文本
        raise Error('llm-mock-server: successText/partialText/reasoningText/toolName must not be empty')#空文本
    if 选项.get('requestId')=='':#空请求 id
        raise Error('llm-mock-server: requestId must not be empty')#空请求 id
    try:#校验 JSON
        json.loads(工具参数)#校验工具参数 JSON
    except Exception:#解析失败
        raise Error('llm-mock-server: toolArguments must be valid JSON')#JSON 非法
    配置权重=选项.get('randomWeights') or 默认模拟LLM随机权重#配置权重
    随机权重=[]#正权重列表
    for 行为,权重 in 配置权重.items():#逐项权重
        if 行为 not in 具体行为集:#未知行为
            raise Error(f'llm-mock-server: randomWeights contains unknown concrete behavior {行为!r}')#未知行为
        if not isinstance(权重,(int,float)) or isinstance(权重,bool) or 权重<0:#权重非法
            raise Error(f'llm-mock-server: random weight for {行为} must be a non-negative finite number')#权重非法
        if 权重>0:#正权重
            随机权重.append((行为,权重))#收集
    if len(随机权重)==0:#无正权重
        raise Error('llm-mock-server: randomWeights must contain at least one positive weight')#无正权重
    已解析={#返回已解析选项
        'host':主机,'port':端口,'sequence':list(序列),'lastBehavior':末项,
        'repeatLast':选项.get('repeatLast') or False,'randomSeed':随机种子,
        'randomWeights':随机权重,'successText':成功文本,'partialText':部分文本,
        'reasoningText':推理文本,'chunkSize':分片大小,'chunkDelayMs':分片延迟,
        'disconnectDelayMs':断开延迟,'retryAfterMs':重试等待,'toolName':工具名,
        'toolArguments':工具参数,
    }#已解析结束
    if 'apiKey' in 选项 and 选项['apiKey'] is not None:#可选密钥
        已解析['apiKey']=选项['apiKey']#写入
    if 'requestId' in 选项 and 选项['requestId'] is not None:#可选请求 id
        已解析['requestId']=选项['requestId']#写入
    if 'onEvent' in 选项 and 选项['onEvent'] is not None:#可选观察者
        已解析['onEvent']=选项['onEvent']#写入
    return 已解析#返回

def 发出(选项,事件):#发出遥测
    """通知观察者；观察者失败不改线上行为。"""
    观察=选项.get('onEvent')#观察者
    if 观察 is None:#无观察者
        return#结束
    try:#观察者
        观察(事件)#通知
    except Exception:#观察者失败
        return#忽略

def 切分文本(文本,大小):#按码点切分
    """按 Unicode 码点切分文本。"""
    点们=list(文本)#按码点拆
    return [''.join(点们[索引:索引+大小]) for 索引 in range(0,len(点们),大小)]#按大小切

def 结束记录(选项,记录,结局):#结束请求记录
    """写入结局并发出 result 事件。"""
    if 记录.get('outcome') is not None:#已有结局
        return#幂等
    记录['outcome']=结局#写入结局
    发出(选项,{#发出结果
        'type':'result','attempt':记录['attempt'],'scriptBehavior':记录['scriptBehavior'],
        'behavior':记录['behavior'],'outcome':结局,'chunksSent':记录['chunksSent'],
    })#结果事件

def 写SSE(记录,写出,载荷):#写 SSE 事件
    """写一条 data 事件。"""
    正文=载荷 if isinstance(载荷,str) else json.dumps(载荷,ensure_ascii=False)#载荷文本
    写出(f'data: {正文}\n\n'.encode('utf-8'))#写 data 事件
    记录['chunksSent']+=1#计数

def 写完成哨兵(记录,写出):#写 DONE
    """写结束哨兵。"""
    写SSE(记录,写出,'[DONE]')#写结束哨兵

def 终止分片(原因,输出令牌):#终止分片
    """构造终止分片载荷。"""
    return {#终止载荷
        'choices':[{'index':0,'delta':{'content':''},'finish_reason':原因}],
        'usage':{'prompt_tokens':3,'completion_tokens':输出令牌},
    }#终止分片

def 可取消等待(毫秒,已关闭):#可取消等待
    """等待毫秒；连接已关则返回 False。"""
    if 毫秒==0:#零延迟
        return not 已关闭()#仅检查存活
    截止=time.monotonic()+毫秒/1000#截止时刻
    while time.monotonic()<截止:#等待
        if 已关闭():#已关
            return False#已关闭
        time.sleep(0.01)#短睡
    return not 已关闭()#仍存活

def 带种子随机(种子):#带种子 PRNG
    """返回 [0,1) 随机函数。"""
    状态=[种子&0xffffffff]#PRNG 状态
    def 抽():#抽随机
        """一步混合。"""
        状态[0]=(状态[0]+0x6d2b79f5)&0xffffffff#步进
        混合=状态[0]#混合
        混合=(混合^(混合>>15))*(混合|1)&0xffffffff#混1
        混合^=(混合+((混合^(混合>>7))*(混合|61)&0xffffffff))&0xffffffff#混2
        return ((混合^(混合>>14))&0xffffffff)/0x100000000#[0,1)
    return 抽#返回函数

def 按权重抽行为(权重表,随机):#按权重抽行为
    """按相对权重抽取具体行为。"""
    总=sum(项[1] for 项 in 权重表)#总权重
    抽签=随机()*总#抽签
    for 行为,权重 in 权重表:#逐项
        if 抽签<权重:#命中
            return 行为#命中
        抽签-=权重#扣减
    return 权重表[-1][0]#兜底末项

def 工具调用分片(选项):#工具调用分片
    """构造两段工具调用增量。"""
    中点=max(1,len(选项['toolArguments'])//2)#参数中点
    return [#两段增量
        {'choices':[{'index':0,'delta':{'tool_calls':[{
            'index':0,'id':'mock-call-1','type':'function',
            'function':{'name':选项['toolName'],'arguments':选项['toolArguments'][:中点]},
        }]},'finish_reason':None}]},
        {'choices':[{'index':0,'delta':{'tool_calls':[{
            'index':0,'function':{'arguments':选项['toolArguments'][中点:]},
        }]},'finish_reason':None}]},
    ]#两段结束

def 启动模拟LLM服务器(选项):#启动服务器
    """启动本地 chat-completions 服务器，每个已接受请求消费一个配置行为。"""
    已解析=解析选项(选项)#解析选项
    请求们=[]#捕获记录
    随机=带种子随机(已解析['randomSeed'])#带种子 PRNG
    游标=[0]#脚本游标
    关闭门闩=threading.Event()#关闭门闩
    活动连接=set()#活动响应集合

    def 选行为():#选行为
        """消费脚本并解析具体行为。"""
        索引=游标[0]#当前索引
        游标[0]=索引+1#推进
        选中=已解析['sequence'][索引] if 索引<len(已解析['sequence']) else None#当前条目
        if 选中 is None:#耗尽
            脚本行为=已解析['lastBehavior'] if 已解析['repeatLast'] else 'script_exhausted'#耗尽处理
        else:#有条目
            脚本行为=选中#脚本行为
        行为=按权重抽行为(已解析['randomWeights'],随机) if 脚本行为=='random' else 脚本行为#具体或耗尽
        return {'scriptBehavior':脚本行为,'behavior':行为}#返回选择

    class 处理器(基处理器):#请求处理器
        """处理单个 HTTP 请求。"""
        def log_message(自身,_格式,*_参数):#静默日志
            """抑制默认访问日志。"""
            return#静默

        def do_POST(自身):#处理 POST
            """处理 chat-completions POST。"""
            自身._处理()#委托

        def do_GET(自身):#拒绝 GET
            """非 POST 一律 405。"""
            自身.send_response(405)#方法不允许
            自身.send_header('Allow','POST')#允许 POST
            自身.end_headers()#结束头

        def _已关闭(自身):#连接是否已关
            """连接已关或服务器关闭。"""
            return 关闭门闩.is_set() or 自身.close_connection#已关

        def _写头(自身,状态,头表=None,内容类型=None):#写响应头
            """写状态与头。"""
            自身.send_response(状态)#状态
            if 内容类型 is not None:#内容类型
                自身.send_header('Content-Type',内容类型)#写类型
            for 键,值 in (头表 or {}).items():#其余头
                自身.send_header(键,值)#写头
            自身.end_headers()#结束头

        def _开SSE(自身,内容类型='text/event-stream; charset=utf-8'):#打开 SSE
            """写 SSE 头。"""
            自身._写头(200,{'Cache-Control':'no-cache','Connection':'keep-alive'},内容类型)#写 SSE 头

        def _写出(自身,数据):#写字节
            """写响应体。"""
            自身.wfile.write(数据)#写
            自身.wfile.flush()#冲刷

        def _HTTP错误(自身,记录,状态,消息,码,类型名='mock_error'):#写 HTTP 错误
            """写 JSON 错误并结束记录。"""
            头表={'Content-Type':'application/json'}#默认头
            if 记录['behavior']=='rate_limit':#限流
                头表['Retry-After']=str((已解析['retryAfterMs']+999)//1000)#限流 Retry-After
            if 'requestId' in 已解析:#可选请求 id
                头表['X-Request-Id']=已解析['requestId']#写请求 id
            正文=json.dumps({'error':{'message':消息,'type':类型名,'code':码}},ensure_ascii=False)#错误体
            自身._写头(状态,头表)#写状态
            自身._写出(正文.encode('utf-8'))#写错误体
            结束记录(已解析,记录,'completed')#记为完成

        def _流文本(自身,记录,文本,延迟毫秒):#流式发文本
            """流式发出文本；客户端关闭返回 False。"""
            for 片 in 切分文本(文本,已解析['chunkSize']):#逐分片
                写SSE(记录,自身._写出,{'choices':[{'index':0,'delta':{'content':片},'finish_reason':None}]})#写文本增量
                if not 可取消等待(延迟毫秒,自身._已关闭):#客户端已关
                    return False#已关
            return True#全部发出

        def _完成文本(自身,记录,原因,延迟毫秒):#完成文本流
            """完成文本流并结束。"""
            if not 自身._流文本(记录,已解析['successText'],延迟毫秒):#客户端关闭
                结束记录(已解析,记录,'client_closed')#客户端关闭
                return#结束
            写SSE(记录,自身._写出,终止分片(原因,len(list(已解析['successText']))))#终止分片
            写完成哨兵(记录,自身._写出)#DONE
            结束记录(已解析,记录,'completed')#完成

        def _断开(自身,记录):#延迟断开
            """延迟后销毁连接。"""
            if not 可取消等待(已解析['disconnectDelayMs'],自身._已关闭):#等待中客户端已关
                结束记录(已解析,记录,'client_closed')#客户端已关
                return#结束
            结束记录(已解析,记录,'reset')#记重置
            自身.close_connection=True#标记关闭
            try:#销毁
                自身.connection.close()#销毁连接
            except Exception:#忽略
                return#忽略

        def _跑行为(自身,记录):#执行行为
            """按行为分支执行。"""
            行为=记录['behavior']#具体行为
            if 行为=='script_exhausted':#脚本耗尽
                自身._HTTP错误(记录,500,'mock script exhausted','MOCK_SCRIPT_EXHAUSTED')#脚本耗尽
            elif 行为=='connection_reset':#连接重置
                结束记录(已解析,记录,'reset')#记重置
                自身.close_connection=True#关
                try:#销毁
                    自身.connection.close()#销毁 socket
                except Exception:#忽略
                    return#忽略
            elif 行为=='stream_disconnect':#流断开
                自身._开SSE()#开 SSE
                自身._断开(记录)#再断开
            elif 行为=='empty':#空完成
                自身._开SSE()#开 SSE
                写SSE(记录,自身._写出,终止分片('stop',0))#空 stop
                写完成哨兵(记录,自身._写出)#DONE
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='empty_body':#空正文
                自身._开SSE()#开 SSE
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='stream_eof':#流 EOF
                自身._开SSE()#开 SSE
                写SSE(记录,自身._写出,{'choices':[{'index':0,'delta':{'role':'assistant'},'finish_reason':None}]})#角色增量
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='partial_eof':#部分 EOF
                自身._开SSE()#开 SSE
                自身._流文本(记录,已解析['partialText'],0)#部分文本后 EOF
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='partial_disconnect':#部分后断开
                自身._开SSE()#开 SSE
                if not 自身._流文本(记录,已解析['partialText'],已解析['chunkDelayMs']):#客户端已关
                    return#结束
                自身._断开(记录)#部分后重置
            elif 行为=='stall':#停滞
                自身._开SSE()#开 SSE
                结束记录(已解析,记录,'stalled')#保持空闲
                活动连接.add(自身)#记账停滞连接
            elif 行为=='malformed_json':#畸形 JSON
                自身._开SSE()#开 SSE
                写SSE(记录,自身._写出,'{not-json')#非法 JSON
                写完成哨兵(记录,自身._写出)#DONE
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='malformed_event':#畸形事件
                自身._开SSE()#开 SSE
                写SSE(记录,自身._写出,{'choices':[None]})#畸形分片
                写完成哨兵(记录,自身._写出)#DONE
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='wrong_content_type':#错误内容类型
                自身._开SSE('application/json')#错误 Content-Type
                自身._完成文本(记录,'stop',0)#仍走完成路径
            elif 行为=='rate_limit':#限流
                自身._HTTP错误(记录,429,'mock rate limit','rate_limit')#限流错误
            elif 行为=='server_error':#服务器错误
                自身._HTTP错误(记录,500,'mock server error','server_error')#服务器错误
            elif 行为=='service_unavailable':#服务不可用
                自身._HTTP错误(记录,503,'mock service unavailable','service_unavailable')#不可用错误
            elif 行为=='auth_error':#认证错误
                自身._HTTP错误(记录,401,'mock authentication failed','invalid_api_key')#认证失败
            elif 行为=='invalid_request':#非法请求
                自身._HTTP错误(记录,400,'mock invalid request','invalid_request')#非法请求
            elif 行为=='context_overflow':#上下文溢出
                自身._HTTP错误(记录,400,'mock input exceeds the model context window','context_length_exceeded','invalid_request_error')#上下文溢出
            elif 行为=='quota_exceeded':#配额耗尽
                自身._HTTP错误(记录,429,'mock insufficient quota','insufficient_quota')#配额耗尽
            elif 行为=='success':#成功
                自身._开SSE()#开 SSE
                自身._完成文本(记录,'stop',0)#成功补全
            elif 行为=='reasoning_success':#带推理成功
                自身._开SSE()#开 SSE
                for 片 in 切分文本(已解析['reasoningText'],已解析['chunkSize']):#逐推理分片
                    写SSE(记录,自身._写出,{'choices':[{'index':0,'delta':{'reasoning_content':片},'finish_reason':None}]})#推理增量
                自身._完成文本(记录,'stop',0)#再发正文
            elif 行为=='tool_call_success':#工具调用成功
                自身._开SSE()#开 SSE
                for 片 in 工具调用分片(已解析):#工具调用
                    写SSE(记录,自身._写出,片)#写分片
                写SSE(记录,自身._写出,终止分片('tool_calls',2))#工具终止
                写完成哨兵(记录,自身._写出)#DONE
                结束记录(已解析,记录,'completed')#完成
            elif 行为=='max_tokens':#达 token 上限
                自身._开SSE()#开 SSE
                自身._完成文本(记录,'length',0)#length 结束
            elif 行为=='slow_success':#慢速成功
                自身._开SSE()#开 SSE
                自身._完成文本(记录,'stop',已解析['chunkDelayMs'])#慢速成功

        def _处理(自身):#请求处理主路径
            """鉴权、读体、选行为并执行。"""
            路径=自身.path.split('?',1)[0]#路径
            if not 路径.endswith('/chat/completions'):#路径不符
                自身.send_response(404)#路径不符
                自身.end_headers()#结束
                return#结束
            授权=自身.headers.get('Authorization')#授权头
            if 'apiKey' in 已解析 and 授权!=f"Bearer {已解析['apiKey']}":#鉴权失败
                自身._写头(401,内容类型='application/json')#写 401 头
                自身._写出(json.dumps({'error':{'message':'invalid mock bearer token','code':'invalid_api_key'}},ensure_ascii=False).encode('utf-8'))#鉴权失败
                return#结束
            长度=int(自身.headers.get('Content-Length') or 0)#正文长度
            原始=自身.rfile.read(长度) if 长度>0 else b''#读正文
            try:#解析 JSON
                体=json.loads(原始.decode('utf-8')) if 原始 else None#解析
            except Exception:#JSON 非法
                自身._写头(400,内容类型='application/json')#写 400 头
                自身._写出(json.dumps({'error':{'message':'request body must be valid JSON','code':'invalid_json'}},ensure_ascii=False).encode('utf-8'))#JSON 非法
                return#结束
            选中=选行为()#消费脚本
            记录={#新建记录
                'attempt':len(请求们)+1,'scriptBehavior':选中['scriptBehavior'],
                'behavior':选中['behavior'],'path':路径,
                'headers':dict(自身.headers.items()),'body':体,'chunksSent':0,
            }#新建记录
            请求们.append(记录)#入列
            发出(已解析,{#发出请求事件
                'type':'request','attempt':记录['attempt'],
                'scriptBehavior':记录['scriptBehavior'],'behavior':记录['behavior'],'path':路径,
            })#请求事件
            try:#执行行为
                自身._跑行为(记录)#执行
            except Exception as 错误:#处理器失败
                结束记录(已解析,记录,'server_error')#记服务器错误
                if 自身.headers_sent:#头已发
                    try:#销毁
                        自身.connection.close()#销毁
                    except Exception:#忽略
                        return#忽略
                    return#结束
                自身._写头(500,内容类型='application/json')#写 500 头
                自身._写出(json.dumps({'error':{'message':'mock server handler failed','code':'MOCK_HANDLER_FAILED'}},ensure_ascii=False).encode('utf-8'))#处理器失败
                raise 错误#再抛

    服务器=线程HTTP服务器((已解析['host'],已解析['port']),处理器)#创建服务器
    线程=threading.Thread(target=服务器.serve_forever,daemon=True)#服务线程
    线程.start()#启动
    主机,端口号=服务器.server_address[:2]#实际地址
    广告主机=f'[{主机}]' if ':' in str(主机) and not str(主机).startswith('[') else 主机#IPv6 括号
    关闭锁=threading.Lock()#关闭锁
    已关闭=[False]#是否已关

    def 关闭():#关闭句柄
        """停止接受并强制关闭停滞连接。"""
        with 关闭锁:#串行关闭
            if 已关闭[0]:#幂等
                return#结束
            已关闭[0]=True#标记
            关闭门闩.set()#通知等待
            for 连接 in list(活动连接):#强制关停滞
                try:#关
                    连接.connection.close()#关连接
                except Exception:#忽略
                    pass#忽略
            活动连接.clear()#清空
            服务器.shutdown()#停接受
            服务器.server_close()#关套接字
            线程.join(timeout=5)#等线程

    return {#返回句柄
        'baseURL':f'http://{广告主机}:{端口号}',#基 URL
        'port':端口号,#端口
        'randomSeed':已解析['randomSeed'],#种子
        'requests':请求们,#请求记录
        'close':关闭,#关闭
    }#句柄结束

def 应用(上下文对象):#测试支持入口
    """模拟服务器由 harness 直接调用，无 Cordis 挂载面。"""
    return#空 apply

apply=应用#入口
startMockLlmServer=启动模拟LLM服务器#上游名
MOCK_LLM_BEHAVIORS=模拟LLM行为名表#上游名
DEFAULT_MOCK_LLM_RANDOM_WEIGHTS=默认模拟LLM随机权重#上游名
MAX_MOCK_LLM_TIMER_DELAY_MS=模拟LLM定时器延迟上限毫秒#上游名
