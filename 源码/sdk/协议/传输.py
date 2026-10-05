import json,threading,uuid#JSON、互斥与请求 id
from ...基础设施.通用工具.并发原语 import 操作任务,中止信号,中止控制器,已中止#任务与中止
from ...基础设施.通用工具.帧协议 import 换行帧解码器,编码ndjson行#换行帧
from ...基础设施.通用工具.jsonrpc协议 import (#JSON-RPC 构造与分类
    构造jsonrpc请求,构造jsonrpc通知,构造jsonrpc成功响应,构造jsonrpc错误响应,分类jsonrpc消息,
)#构造与分类
from ...基础设施.通用工具.线程工具 import 启动守护线程#守护线程

__all__=['JSONRPC响应错误','JSONRPC传输对等端','换行JSONRPC传输','操作任务','已中止','中止信号','中止控制器']#仅中文公开名

from .异常 import JSONRPC传输错误,JSONRPC响应错误#本包异常

def 对象参数(参数):
    '把 JSON-RPC params 归一成普通对象。空 dict 在 JS 为真，这里只认 dict'
    if isinstance(参数,dict):#普通对象
        return 参数#原样
    return {}#非普通对象则空对象

def 中止错误(原因):
    '把中止原因归一成拒绝用的异常'
    if isinstance(原因,BaseException):#已是异常
        return 原因#原样
    return JSONRPC传输错误('JSON-RPC 请求已中止：'+str(原因))#包一层消息

def 错误消息(错误):
    '取出错误消息'
    return str(错误)#字符串化

class JSONRPC传输对等端:
    '运行时服务端与 SDK 客户端共用的出站请求与通知面'
    def 请求(自身,方法,参数):
        '发送请求并等待响应'
        raise NotImplementedError#子类实现

    def 通知(自身,方法,参数=None):
        '发送通知；省略 params 则不写 params 成员'
        raise NotImplementedError#子类实现

class 换行JSONRPC传输(JSONRPC传输对等端):
    '基于调用方拥有的流的按行端点。启动挂上监听；关闭卸掉监听并拒绝未完成请求，不销毁流'
    def __init__(自身,输入流,输出流):
        '记下入站与出站流'
        自身.输入=输入流#入站字节/文本流
        自身.输出=输出流#出站字节/文本流
        自身._行解码=换行帧解码器()#换行切分
        自身.已启动=False#是否已挂上输入监听
        自身.请求处理=None#当前入站请求处理函数
        自身.通知处理=None#当前入站通知处理函数
        自身.未决={}#按字符串 id 登记的未完成请求
        自身.锁=threading.Lock()#未决互斥
        自身._读线程=None#后台读线程
        自身._写锁=threading.Lock()#写出互斥

    def 启动(自身):
        '幂等'
        if 自身.已启动:#已启动
            return#不再挂监听
        自身.已启动=True#标记已启动
        def 读循环():
            '读到 EOF 或出错为止'
            try:
                while True:#直到 EOF
                    if hasattr(自身.输入,'readline'):#按行可读
                        行=自身.输入.readline()#读一行
                        if 行=='' or 行 is None:#EOF
                            break
                        自身._处理数据(行)#喂入
                        continue#下一行
                    块=自身.输入.read(65536)#一块
                    if not 块:#EOF
                        break
                    自身._处理数据(块)#喂入
            except BaseException as 错误:
                包装=错误 if isinstance(错误,BaseException) else JSONRPC传输错误(str(错误))#归一
                自身._失败未决(包装)#拒绝未决
                return
            自身._失败未决(JSONRPC传输错误('JSON-RPC 输入已关闭'))#输入关闭
        自身._读线程=启动守护线程(读循环)#后台线程

    def 关闭(自身):
        '在启动之前调用也安全。不销毁流'
        自身._失败未决(JSONRPC传输错误('JSON-RPC 传输已关闭'))#拒绝所有未完成请求

    def 当请求(自身,处理函数):
        '安装请求处理函数，替换先前的处理函数'
        自身.请求处理=处理函数#替换

    def 当通知(自身,处理函数):
        '安装通知处理函数，替换先前的处理函数'
        自身.通知处理=处理函数#替换

    def 请求(自身,方法,参数,信号=None):
        '发送请求并等待响应；可选中止信号。同步返回结果'
        标识='req_'+uuid.uuid4().hex#无连字符请求 id
        消息=构造jsonrpc请求(标识,方法,参数)#组装请求帧
        等待=操作任务()#为本 id 挂起
        if 已中止(信号):#已经中止
            等待.拒绝(中止错误(信号.原因 if 信号 is not None else None))#立刻拒绝
            return 等待.等待()#抛出
        def 监视中止():
            '中止时清 pending 并拒绝'
            if 信号 is None:#无信号
                return#无需
            信号.等待()#等到中止
            with 自身.锁:#互斥
                自身.未决.pop(标识,None)#丢掉该 id
            等待.拒绝(中止错误(信号.原因))#拒绝
        if 信号 is not None:#调用方给了放弃信号
            启动守护线程(监视中止)#监视中止
        def 兑现(值):
            '成功回调'
            等待.兑现(值)#把结果交给调用方
        def 拒绝(错误):
            '失败回调'
            等待.拒绝(错误)#把错误交给调用方
        with 自身.锁:#互斥
            自身.未决[标识]={'兑现':兑现,'拒绝':拒绝}#登记未完成请求
        try:
            自身._写出(消息)#写到输出流
        except BaseException as 错误:
            with 自身.锁:#互斥
                自身.未决.pop(标识,None)#清掉 pending
            等待.拒绝(错误 if isinstance(错误,BaseException) else JSONRPC传输错误(str(错误)))#拒绝
        return 等待.等待()#同步交出结果

    def 通知(自身,方法,参数=None):
        '省略 params 则不写该成员'
        自身._写出(构造jsonrpc通知(方法,参数))#通知帧

    def 刷出(自身):
        '等待此前帧写出落定。空屏障不发出字节。同步返回'
        if hasattr(自身.输出,'flush'):#可刷新
            自身.输出.flush()#刷新

    def _处理数据(自身,块):
        '切出完整行并异步处理'
        for 行 in 自身._行解码.推入(块):#已完整的非空行
            启动守护线程(自身._处理行,行)#异步处理该行

    def _处理行(自身,行):
        '畸形 JSON 忽略'
        try:
            消息=json.loads(行)#解析帧
        except json.JSONDecodeError:
            return#忽略本行
        种类=分类jsonrpc消息(消息)#请求、通知、响应或无效
        if 种类=='请求':#入站请求
            参数=消息['params'] if 'params' in 消息 else None#params
            自身._处理入站请求(消息['id'],消息['method'],对象参数(参数))#派发请求
            return#本行处理完
        if 种类=='响应':#入站响应
            自身._处理入站响应(消息['id'],消息)#交给 pending 认领
            return#本行处理完
        if 种类=='通知':#入站通知
            处理=自身.通知处理#有处理函数才调用
            if 处理 is not None:#有处理函数
                参数=消息['params'] if 'params' in 消息 else None#params
                处理(消息['method'],对象参数(参数))#调用

    def _处理入站请求(自身,标识,方法,参数):
        '未安装处理函数返回 -32601；处理失败返回 -32603'
        处理=自身.请求处理#当前请求处理函数
        if 处理 is None:#未安装处理函数
            自身._写出错误(标识,-32601,'找不到方法：'+str(方法))#方法未找到
            return#不再往下
        try:
            结果=处理(方法,参数)#同步业务结果
            自身._写出(构造jsonrpc成功响应(标识,结果))#写出成功响应
            return
        except BaseException as 错误:
            自身._写出错误(标识,-32603,错误消息(错误))#内部错误

    def _处理入站响应(自身,标识,帧):
        '未知 id 忽略。帧为 dict'
        with 自身.锁:#互斥
            未决=自身.未决.pop(标识,None)#按 id 查找并认领
        if 未决 is None:#未知 id
            return#忽略
        if 'error' in 帧 and isinstance(帧['error'],dict):#对端给了 error 对象
            错误体=帧['error']#error
            原始码=错误体['code'] if 'code' in 错误体 else None#可能的错误码
            码=原始码 if isinstance(原始码,(int,float)) and not isinstance(原始码,bool) else None#非数字视为未给
            原始消息=错误体['message'] if 'message' in 错误体 else None#可能的消息
            消息=原始消息 if isinstance(原始消息,str) else 'JSON-RPC 错误'#默认消息
            数据=错误体['data'] if 'data' in 错误体 else None#可选 data
            未决['拒绝'](JSONRPC响应错误(码,消息,数据))#拒绝为 JSONRPC响应错误
            return#错误响应处理完
        结果=帧['result'] if 'result' in 帧 else None#成功 result
        未决['兑现'](结果)#成功则兑现 result

    def _写出错误(自身,标识,码,消息):
        '标准 JSON-RPC 错误对象'
        自身._写出(构造jsonrpc错误响应(标识,码,消息))#写出

    def _写出(自身,消息):
        '序列化后加换行写出'
        行=编码ndjson行(消息)#紧凑 JSON 行
        with 自身._写锁:#写出互斥
            编码=getattr(自身.输出,'encoding',None)#文本流编码
            if 编码 is not None:#文本模式
                自身.输出.write(行)#写文本
            else:#二进制
                自身.输出.write(行.encode('utf-8'))#写字节
            if hasattr(自身.输出,'flush'):#可刷新
                自身.输出.flush()#刷新

    def _失败未决(自身,错误):
        '快照后清空，避免重复拒绝'
        with 自身.锁:#互斥
            等待者=list(自身.未决.values())#先快照
            自身.未决.clear()#立刻清空
        for 一项 in 等待者:#逐个拒绝
            一项['拒绝'](错误)#拒绝
