import math,threading,time#有限判定、定时器与时间戳
from ...工具.超时 import 定时器延迟上限毫秒#定时器延迟上限
from ...基础设施.通用工具.时间工具 import 当前毫秒
from ...基础设施.通用工具.文本工具 import utf8字节数
from ...基础设施.js特性 import PromiseEX as 期约#就绪、同步链、世代关闭与连接尝试的期约
from .异常 import MCP错误#本包异常
from .传输 import 创建传输#传输工厂
from .工具桥接 import 同步工具#工具同步

__all__=['重连默认值','默认最大指令字节','解析重连策略','启动连接']

重连默认值={#冻结语义的重连默认值
    'enabled':True,#默认启用重连
    'initialDelayMs':500,#默认初始延迟 500 毫秒
    'maxDelayMs':30000,#默认上限与稳定窗口 30000 毫秒
    'maxAttempts':10,#默认最多 10 次
}#重连默认值结束

世代关闭超时毫秒=5000#世代关闭等待上限
默认最大指令字节=32768#归属服务器指令的 UTF-8 字节上限

def 解析重连策略(配置,路径):
    '从原始重连配置到监督器实际运行策略的唯一切确解析步骤。配置为 dict'
    if 配置 is not None:#调用方给出了重连配置
        for 键 in 配置.keys():#遍历调用方给出的键
            if 键 not in 重连默认值:#未知键则拒绝
                raise MCP错误(路径+'.'+键+' is not a reconnect option')#未知键
    启用=重连默认值['enabled'] if 配置 is None or 'enabled' not in 配置 else 配置['enabled']#是否启用
    初始=重连默认值['initialDelayMs'] if 配置 is None or 'initialDelayMs' not in 配置 else 配置['initialDelayMs']#初始延迟
    上限=重连默认值['maxDelayMs'] if 配置 is None or 'maxDelayMs' not in 配置 else 配置['maxDelayMs']#延迟上限
    次数=重连默认值['maxAttempts'] if 配置 is None or 'maxAttempts' not in 配置 else 配置['maxAttempts']#最大尝试次数
    if isinstance(初始,bool) or not isinstance(初始,(int,float)) or not math.isfinite(初始) or 初始<=0 or 初始>定时器延迟上限毫秒:#初始延迟非法
        raise MCP错误(路径+'.initialDelayMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#拒绝
    if isinstance(上限,bool) or not isinstance(上限,(int,float)) or not math.isfinite(上限) or 上限<=0 or 上限>定时器延迟上限毫秒:#延迟上限非法
        raise MCP错误(路径+'.maxDelayMs must be a positive finite number no greater than '+str(定时器延迟上限毫秒))#拒绝
    if 初始>上限:#初始延迟超过上限
        raise MCP错误(路径+'.initialDelayMs must be less than or equal to maxDelayMs')#拒绝颠倒的延迟对
    if isinstance(次数,bool) or not isinstance(次数,int) or 次数<1:#尝试次数非法
        raise MCP错误(路径+'.maxAttempts must be a positive integer')#拒绝非正整数
    return {'enabled':启用,'initialDelayMs':初始,'maxDelayMs':上限,'maxAttempts':次数}#已解析策略

def 启动连接(上下文,配置,策略):
    '为一台 MCP 服务器启动受监督连接，并按重连策略保持存活。配置为 dict'
    标签='mcp-client('+配置['serverName']+')'#日志前缀
    拆除不完整消息=标签+': transport closure could not be confirmed during disposal — server shutdown may be incomplete'#拆除诊断
    最大指令字节=配置['maxInstructionBytes'] if 'maxInstructionBytes' in 配置 else 默认最大指令字节#指令上限
    选项={#普通同步用桥接选项
        'registrationFailure':'contain',#冲突时包容
        'serverName':配置['serverName'],#服务器命名空间
        'toolCallTimeoutMs':配置['toolCallTimeoutMs'],#工具调用超时
    }#选项结束
    if 配置['failOnStartupError']:#启动同步选项
        启动选项=dict(选项)#拷贝
        启动选项['registrationFailure']='throw'#致命启动则冲突时抛出
    else:#否则沿用包容选项
        启动选项=选项#包容
    同步链起点=期约()#同步串行链的起点，此前没有任何同步
    同步链起点.解决(None)#起点已解决
    状态={#监督器可变状态
        'disposed':False,#是否已拆除
        'client':None,#当前 MCP 客户端
        'closeClient':None,#与当前世代配对的关闭函数，返回兑现布尔的期约
        'disposers':{},#当前工具 disposer
        'reconnectTimer':None,#已武装的重连定时器
        'failedAttempts':0,#连续失败计数
        'connectedAt':None,#连接成功时间戳
        'firstAttemptError':None,#初次失败原因
        'syncChain':同步链起点,#同步串行链的链尾期约
        'settling':None,#进行中的连接尝试期约
        'serverInstructions':'',#最近一次成功连通的指令快照
    }#状态结束

    def 仍是当前(世代):
        '一个世代仅在它仍是存活插件上的当前世代时才可行动'
        return (not 状态['disposed']) and 状态['client'] is 世代#仍是当前

    def 排队同步(世代,同步选项=None):
        '序列化每一次同步工具调用：接在同步链尾之后，返回本次同步的期约；链尾不因本次失败而断'
        if 同步选项 is None:#缺省用普通选项
            同步选项=选项#普通选项
        def 执行同步(链尾值):
            '前一次同步成功后才轮到本次；世代已过时则跳过'
            if not 仍是当前(世代):#世代已过时则跳过
                return#跳过
            状态['disposers']=同步工具(世代,上下文,同步选项,状态['disposers'])#交换工具世代
        def 保留链尾(错误):
            '本次失败由入队的调用方负责报告，链尾必须挺过失败'
            return None#链尾以已解决继续
        本次=状态['syncChain'].然后(执行同步)#接在链尾之后
        状态['syncChain']=本次.捕获(保留链尾)#新链尾，失败也继续
        return 本次#把本次同步交给调用方

    def 世代断开(世代):
        '每个世代一次断开判定'
        if not 仍是当前(世代):#过时信号忽略
            return#忽略
        状态['client']=None#清除当前客户端
        状态['closeClient']=None#清除关闭函数
        安排重连()#安排重连

    def 等待关闭(关闭):
        '返回期约，兑现布尔：传输拥有的关闭信号先到为 True，超时为 False，不让损坏的传输永远卡住拆除'
        def 执行器(解决,拒绝):
            '超时定时器与关闭信号谁先到谁决定结果'
            def 超时():
                '超时则失败关闭'
                解决(False)#失败关闭
            定时=threading.Timer(世代关闭超时毫秒/1000,超时)#超时定时器
            定时.daemon=True#不独自撑住进程
            定时.start()#武装
            def 关闭到达(关闭值):
                '关闭到达则取消超时并报告正常关闭'
                定时.cancel()#取消超时
                解决(True)#正常关闭
            关闭.然后(关闭到达)#关闭信号兑现时到达
        return 期约(执行器)#调用方链式取布尔

    def 安排重连():
        '按策略安排下一次连接尝试'
        曾连通=状态['connectedAt'] is not None#是否曾建立过连接
        if not 策略['enabled']:#重连已关闭
            if 曾连通:#曾连通后丢失
                消息='connection lost and reconnect is disabled — registered tools will fail until an HMR reload or Host restart'#曾连通
            else:#从未连通
                消息='connection failed and reconnect is disabled — no tools were registered; reload the plugin or restart the Host to connect'#从未连通
            上下文.日志.错误(标签+': '+消息)#记录致命停机
            return#不再尝试
        if 状态['connectedAt'] is not None and (time.time()*1000-状态['connectedAt'])>=策略['maxDelayMs']:#稳定存活则重置预算
            状态['failedAttempts']=0#重置
        状态['connectedAt']=None#离开连通状态
        状态['failedAttempts']+=1#计入本次失败
        if 状态['failedAttempts']>策略['maxAttempts']:#预算耗尽
            def 放弃拆除(链尾值):
                '同步链上的最后一步：注销全部工具，免得与进行中同步的换代撞车'
                for 注销 in 状态['disposers'].values():#注销全部工具
                    注销()#注销
                状态['disposers']={}#清空 disposer
                状态['serverInstructions']=''#清空指令
            状态['syncChain']=状态['syncChain'].然后(放弃拆除)#接到同步链尾
            上下文.日志.错误(标签+': giving up after '+str(策略['maxAttempts'])+' consecutive failed reconnect attempts — tools unregistered; reload the plugin or restart the Host to reconnect')#记录放弃
            return#停止重连
        延迟=min(策略['maxDelayMs'],策略['initialDelayMs']*(2**(状态['failedAttempts']-1)))#指数退避并封顶
        动作='connection lost; reconnecting' if 曾连通 else 'connection failed; retrying'#日志动词
        上下文.日志.警告(标签+': '+动作+' in '+str(延迟)+'ms (attempt '+str(状态['failedAttempts'])+'/'+str(策略['maxAttempts'])+')')#预告下次尝试
        def 到期():
            '非启动路径的连接尝试'
            状态['reconnectTimer']=None#定时器已触发
            状态['settling']=连接世代(False)#非启动路径
        定时=threading.Timer(延迟/1000,到期)#延迟毫秒
        定时.daemon=True#允许进程在等待期间退出
        状态['reconnectTimer']=定时#记下
        定时.start()#武装

    def 连接世代(启动):
        '一次连接尝试：全新传输 + 客户端，连接，然后排队初次工具同步。返回期约，兑现于尝试落定，从不拒绝；阻塞的连接调用在后台线程里跑'
        from mcp import ClientSession#MCP 客户端会话
        关闭=期约()#本代关闭栅栏，传输关闭后解决
        本次落定=期约()#本次尝试落定后解决
        世代容器={'session':None,'cm':None,'instructions':''}#会话、上下文管理器与指令快照
        def 关闭本代():
            '返回期约，兑现布尔：尽力关闭会话与传输后等关闭栅栏，True 表示已确认关闭'
            会话=世代容器['session']#会话
            管理器=世代容器['cm']#上下文管理器
            try:#尽力关闭
                if 会话 is not None:#有会话
                    会话.close()#关闭会话
                if 管理器 is not None:#有管理器
                    管理器.__exit__(None,None,None)#退出
                关闭.解决(None)#放行栅栏
            except MCP错误:#传输已消失，栅栏不放行，由等待关闭的超时判为未确认
                pass#对调用方无害：未确认关闭会被记录并停止重连
            return 等待关闭(关闭)#栅栏与超时先到先得
        def 关闭已落定(已安静):
            '本代关闭结果出来后，只有仍是当前世代才继续'
            if not 仍是当前(世代容器):#已不是当前则退出
                本次落定.解决(None)#尝试落定
                return#退出
            if not 已安静:#关闭超时
                状态['client']=None#放弃当前客户端
                状态['closeClient']=None#放弃关闭函数
                上下文.日志.错误(标签+': failed generation could not confirm transport closure — reconnect stopped to avoid overlapping server processes; reload the plugin or restart the Host to retry')#停止重连
                本次落定.解决(None)#尝试落定
                return#不再重连
            世代断开(世代容器)#正常转入断开以重连
            本次落定.解决(None)#尝试落定
        def 连接失败(错误):
            '记下首次错误，尽力关闭本代，确认静止后决定重连还是停止'
            if 状态['firstAttemptError'] is None:#只记下第一次错误
                状态['firstAttemptError']=错误#初次失败
            if 仍是当前(世代容器):#仍是当前则记警告
                上下文.日志.警告(标签+': connection attempt failed: '+str(错误))#记警告
            关闭本代().然后(关闭已落定)#等本代静止
        def 连接成功(同步值):
            '初次工具同步完成：记下指令快照与连通时刻'
            if 仍是当前(世代容器):#已不是当前则什么都不记
                状态['serverInstructions']=世代容器['instructions']#记下快照
                状态['connectedAt']=当前毫秒()#记下连通时刻
                if 状态['failedAttempts']>0:#重连成功则记信息
                    上下文.日志.信息(标签+': reconnected and re-synced tools (attempt '+str(状态['failedAttempts'])+'/'+str(策略['maxAttempts'])+')')#重连成功
            本次落定.解决(None)#尝试落定
        状态['client']=世代容器#设为当前世代
        状态['closeClient']=关闭本代#配对关闭函数
        def 发请求(载荷,选项=None):
            '把 JSON-RPC 方法名落到 SDK 调用，结果收成 dict'
            会话=世代容器['session']#本代会话，调用时已经写入
            方法=载荷['method']#方法名
            if 方法=='tools/call':#调用工具
                参数=载荷['params']#参数
                结果=会话.call_tool(参数['name'],参数['arguments'])#调用
                规范={'content':结果.content,'isError':结果.isError}#收成 dict
                if 结果.structuredContent is not None:#有结构化内容
                    规范['structuredContent']=结果.structuredContent#带上
                return 规范#返回
            列出=会话.list_tools()#列出
            工具列表=[]#工具页
            for 工具 in 列出.tools:#SDK 对象
                项={'name':工具.name,'inputSchema':工具.inputSchema}#必填
                if 工具.description is not None:#有描述
                    项['description']=工具.description#描述
                if 工具.outputSchema is not None:#有输出模式
                    项['outputSchema']=工具.outputSchema#输出模式
                if 工具.execution is not None:#有执行块
                    项['execution']=工具.execution#执行块
                工具列表.append(项)#收下
            页={'tools':工具列表}#本页
            if 列出.nextCursor is not None:#有下一页
                页['nextCursor']=列出.nextCursor#游标
            return 页#返回
        def 尝试连接():
            '后台线程里的连接与初次同步排队；同步结果由连接成功或连接失败接力'
            try:#连接并初次同步
                传输=创建传输(配置)#按配置创建传输
                if 传输['kind']=='stdio':#stdio
                    上下文管理器=传输['factory'](传输['params'])#stdio_client
                else:#HTTP
                    上下文管理器=传输['factory'](传输['url'],headers=传输['headers'])#streamablehttp_client
                读写=上下文管理器.__enter__()#进入传输
                读,写=读写[0],读写[1]#读写流
                会话=ClientSession(读,写)#构造本代客户端
                会话.initialize()#初始化
                世代容器['session']=会话#记下会话
                世代容器['cm']=上下文管理器#记下管理器
                世代容器['request']=发请求#请求面
                原文=(getattr(会话,'get_instructions',lambda:None)() or '')#SDK 指令
                if isinstance(原文,str):#有文本
                    原文=原文.rstrip()#去掉尾空白
                else:#无
                    原文=''#空
                世代容器['instructions']=('### MCP server: '+配置['serverName']+'\n\n'+原文) if 原文!='' else ''#带标题的指令快照
                if utf8字节数(世代容器['instructions'])>最大指令字节:#超上限
                    raise MCP错误(标签+': server instructions exceed maxInstructionBytes ('+str(最大指令字节)+')')#拒绝
                同步期约=排队同步(世代容器,启动选项 if 启动 else 选项)#排队初次同步
            except MCP错误 as 错误:#连接或指令校验失败
                连接失败(错误)#走失败收尾
                return#不再排队同步
            同步期约.然后(连接成功,连接失败)#同步成功记快照，失败走失败收尾
        threading.Thread(target=尝试连接,daemon=True).start()#阻塞的连接调用放到后台线程
        return 本次落定#调用方链式等尝试落定

    def 得出就绪结果(落定值):
        '初次尝试落定后给出结果：当前世代仍在则无错误，否则带上真实错误'
        if 状态['client'] is not None:#初次成功则无错误
            return {}#成功
        错误=状态['firstAttemptError'] or MCP错误(标签+': initial connection failed')#真实错误
        return {'error':错误}#带错误

    状态['settling']=连接世代(True)#插件激活时的那一次尝试，拆除要等它静止
    就绪=状态['settling'].然后(得出就绪结果)#初次尝试落定后报告结果

    def 拆除():
        '停止重连，关闭存活客户端，等待静默，然后注销本服务器仍拥有的全部工具。返回期约，兑现于全部完成'
        状态['disposed']=True#标记已拆除
        状态['serverInstructions']=''#清空指令
        定时=状态['reconnectTimer']#已武装定时器
        if 定时 is not None:#有定时器
            定时.cancel()#取消待发重连
            状态['reconnectTimer']=None#清除
        关闭当前=状态['closeClient']#捕获当前关闭函数
        状态['client']=None#放弃当前所有权
        状态['closeClient']=None#放弃关闭函数引用
        拆除完成=期约()#整个拆除落定后解决
        def 注销全部(链尾值):
            '进行中的尝试与同步链都静止后，注销本服务器仍拥有的全部工具'
            try:#注销失败要让拆除期约拒绝，不能悬空
                for 注销 in 状态['disposers'].values():#注销全部工具
                    注销()#注销
            except Exception as 错误:#某个工具注销失败
                拆除完成.拒绝(错误)#交给调用方
                return#不再往下
            状态['disposers']={}#清空 disposer
            拆除完成.解决(None)#拆除完成
        def 等同步链(尝试值):
            '进行中的尝试已静止，它在落定前已入队同步，所以此刻的链尾就是最终链尾'
            状态['syncChain'].然后(注销全部,拆除完成.拒绝)#同步链排空后注销
        def 等尝试静止(已确认关闭):
            '关闭结果出来后，等进行中的连接尝试静止'
            if not 已确认关闭:#关闭超时
                上下文.日志.错误(拆除不完整消息)#拆除时关闭不完整
            状态['settling'].然后(等同步链,拆除完成.拒绝)#等进行中的尝试
        if 关闭当前 is None:#没有存活世代
            等尝试静止(True)#无需关闭
        else:#仍有存活世代
            关闭当前().然后(等尝试静止)#尽力关闭并等关闭结果
        return 拆除完成#调用方链式等拆除结束

    def 读指令():
        '读最近一次成功连通的服务器指令'
        return 状态['serverInstructions']#快照

    def 资源请求(请求,执行):
        '经当前世代转发 MCP 资源请求。请求为 dict'
        世代=状态['client']#当前世代
        if 世代 is None or 状态['connectedAt'] is None:#未连通
            raise MCP错误(标签+': server is disconnected')#拒绝
        方法=请求['method']#方法
        选项={'signal':执行['signal'] if 'signal' in 执行 else None,'timeout':配置['toolCallTimeoutMs']}#超时
        会话=世代['session']#会话
        if 方法=='resources/list':#列出
            参数={'cursor':请求['cursor']} if 'cursor' in 请求 else None#游标
            return 会话.list_resources(参数) if 参数 is not None else 会话.list_resources()#列出
        if 方法=='resources/templates/list':#模板
            参数={'cursor':请求['cursor']} if 'cursor' in 请求 else None#游标
            return 会话.list_resource_templates(参数) if 参数 is not None else 会话.list_resource_templates()#模板
        if 方法=='resources/read':#读取
            return 会话.read_resource({'uri':请求['uri']})#读取
        raise MCP错误(标签+': unknown resource method '+str(方法))#穷尽失败

    return {'ready':就绪,'dispose':拆除,'instructions':读指令,'resources':{'request':资源请求}}#句柄
