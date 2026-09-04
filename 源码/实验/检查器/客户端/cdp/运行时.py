"""类型化 Runtime 命令协议的 Client realm 执行器。

对齐上游 `client/cdp/runtime.ts`。公开面仅中文名。
"""
from ...共享.json import 是否json值,json字节长度#JSON
from ...共享.桥接.版本 import 检查器协议版本#协议版本
from .错误 import 客户端运行时执行错误#执行错误
from .对象 import 客户端对象存储#对象存储
from .属性 import 获取客户端属性#属性
from .栈 import 客户端错误栈#错误栈

__all__=['运行时桥能力','客户端运行时上限','客户端运行时执行器']#仅中文公开名

最大运行时错误消息长度=2048#错误消息上限

def 运行时桥能力(来源):#Runtime桥能力
    """描述浏览器侧 Runtime 执行。"""
    return {'type':'client-runtime','origin':来源}#能力

class 客户端运行时上限:#Client运行时上限
    """Host 部署注入的 Client 侧上限。"""
    def __init__(自身,maxObjectsPerSession,maxPropertiesPerResult,maxResponseBytes):#构造
        """保存上限。"""
        自身.maxObjectsPerSession=maxObjectsPerSession#每会话对象上限
        自身.maxPropertiesPerResult=maxPropertiesPerResult#每结果属性上限
        自身.maxResponseBytes=maxResponseBytes#响应字节上限

def 响应帧(帧,结果封装):#构响应帧
    """构响应帧。"""
    return {'v':检查器协议版本,'t':'client-runtime/response','sourceId':帧['sourceId'],'generation':帧['generation'],'sessionId':帧['sessionId'],'requestId':帧['requestId'],'outcome':结果封装}#响应

def 运行时错误(错误):#规范化错误
    """规范化错误。"""
    if isinstance(错误,客户端运行时执行错误):#类型化
        return {'code':错误.code,'message':错误.message[:最大运行时错误消息长度]}#错误
    消息=str(错误)#转串
    return {'code':'internal-error','message':消息[:最大运行时错误消息长度]}#内部错误

class 客户端运行时会话:#Client Runtime会话
    """按 DevTools 会话隔离对象句柄。"""
    def __init__(自身,最大对象,最大属性,解析脚本):#构造
        """创建对象存储。"""
        自身.对象=客户端对象存储(最大对象)#对象存储
        自身.最大属性=最大属性#属性上限
        自身.解析脚本=解析脚本#脚本键

    def 开始分配(自身):#开始分配
        """开始分配。"""
        return 自身.对象.开始分配()#委托

    def 提交分配(自身,分配):#提交分配
        """提交分配。"""
        自身.对象.提交分配(分配)#委托

    def 回滚(自身,分配):#回滚分配
        """回滚分配。"""
        自身.对象.回滚(分配)#委托

    def 执行(自身,命令,分配,信号=None):#执行命令
        """执行命令。"""
        操作=命令.get('op')#操作
        if 操作=='evaluate':#求值
            return {'op':操作,'completion':自身.求值(命令,分配,信号)}#完成
        if 操作=='get-properties':#取属性
            结果=获取客户端属性(自身.对象,命令,自身.最大属性,分配)#属性
            return {'op':操作,**结果}#合并
        if 操作=='call-function':#调函数
            return {'op':操作,'completion':自身.调函数(命令,分配,信号)}#完成
        if 操作=='await-promise':#等待Promise
            return {'op':操作,'completion':自身.等待承诺(命令,分配,信号)}#完成
        if 操作=='release-object':#释放对象
            自身.对象.释放(命令['handle'])#释放
            return {'op':操作}#确认
        if 操作=='release-object-group':#释放对象组
            自身.释放对象组(命令['objectGroup'])#释放
            return {'op':操作}#确认
        if 操作=='global-lexical-scope-names':#全局词法名
            return {'op':操作,'names':[]}#空列表
        raise Exception(f'Unexpected Client Runtime command: {操作!r}')#未知

    def 关闭(自身):#关闭
        """关闭。"""
        自身.对象.清空()#清空对象

    def 释放对象组(自身,组):#释放对象组
        """释放对象组。"""
        自身.对象.释放组(组)#委托

    def 全部序列化(自身,值们,组,分配):#全部序列化
        """全部序列化。"""
        return [自身.对象.序列化(值,{'group':组},分配) for 值 in 值们]#参数

    def 描述异常(自身,错误,组,栈,分配):#描述异常
        """描述异常。"""
        return {'text':str(错误),'lineNumber':0,'columnNumber':0,'stackTrace':栈 or 客户端错误栈(错误,自身.解析脚本),'exception':自身.对象.序列化(错误,{'group':组},分配)}#详情

    def 求值(自身,命令,分配,信号=None):#求值
        """求值。"""
        raise 客户端运行时执行错误('unsupported','Client evaluate requires a browser JS realm binding')#需浏览器绑定

    def 调函数(自身,命令,分配,信号=None):#调函数
        """调函数。"""
        raise 客户端运行时执行错误('unsupported','Client call-function requires a browser JS realm binding')#需浏览器绑定

    def 等待承诺(自身,命令,分配,信号=None):#等待Promise
        """等待 Promise。"""
        raise 客户端运行时执行错误('unsupported','Client await-promise requires a browser JS realm binding')#需浏览器绑定

class 客户端运行时执行器:#Client Runtime执行器
    """执行 Runtime 请求，同时按 DevTools 会话隔离对象句柄。"""
    def __init__(自身,上限,解析脚本=None):#构造
        """保存上限与脚本解析。"""
        自身.上限=上限 if hasattr(上限,'maxObjectsPerSession') else 客户端运行时上限(**上限)#上限
        自身.解析脚本=解析脚本 or (lambda _网址:None)#脚本键
        自身.会话们={}#会话表
        自身.响应分配={}#响应表

    def 执行(自身,帧,信号=None,延迟对象提交=False):#执行
        """执行一次请求并保留其源、代数、会话与请求身份。"""
        会话=自身.取会话(帧['sessionId'])#会话
        分配=会话.开始分配()#分配
        try:#执行体
            结果=会话.执行(帧['command'],分配,信号)#命令结果
            响应=响应帧(帧,{'ok':True,'result':结果})#成功响应
            if not 是否json值(响应) or json字节长度(响应)>自身.上限.maxResponseBytes:#超字节
                会话.回滚(分配)#回滚
                return 响应帧(帧,{'ok':False,'error':{'code':'result-too-large','message':'Client Runtime result exceeds the source-frame byte limit'}})#过大
            if 延迟对象提交:#延迟提交
                if 帧['requestId'] in 自身.响应分配:#重复id
                    会话.回滚(分配)#回滚
                    return 响应帧(帧,{'ok':False,'error':{'code':'invalid-request','message':'Client Runtime request id is already pending'}})#非法
                自身.响应分配[帧['requestId']]={'sessionId':帧['sessionId'],'session':会话,'allocation':分配}#挂起
            else:#立即提交
                会话.提交分配(分配)#提交
            return 响应#返回
        except Exception as 错误:#失败
            会话.回滚(分配)#回滚
            return 响应帧(帧,{'ok':False,'error':运行时错误(错误)})#错误响应

    def 确认(自身,会话标识,请求标识):#确认
        """Worker 接受一次 Runtime 响应后提交句柄。"""
        挂起=自身.响应分配.get(请求标识)#挂起
        if 挂起 is None or 挂起['sessionId']!=会话标识:#不匹配
            return#返回
        自身.响应分配.pop(请求标识,None)#移除
        挂起['session'].提交分配(挂起['allocation'])#提交

    def 取消(自身,会话标识,请求标识):#取消
        """回滚来自已取消或以其他方式未接受的 Runtime 响应的句柄。"""
        挂起=自身.响应分配.get(请求标识)#挂起
        if 挂起 is None or 挂起['sessionId']!=会话标识:#不匹配
            return#返回
        自身.响应分配.pop(请求标识,None)#移除
        挂起['session'].回滚(挂起['allocation'])#回滚

    def 关闭会话(自身,会话标识):#关闭会话
        """释放为一个已关闭 DevTools 连接保留的全部值。"""
        for 请求标识,挂起 in list(自身.响应分配.items()):#清挂起
            if 挂起['sessionId']==会话标识:#匹配
                自身.响应分配.pop(请求标识,None)#删除
        会话=自身.会话们.get(会话标识)#会话
        if 会话 is not None:#关闭
            会话.关闭()#关闭会话
        自身.会话们.pop(会话标识,None)#删表

    def 释放对象组(自身,会话标识,组):#释放对象组
        """在不关闭外围 Runtime 会话的前提下释放一个对象组。"""
        会话=自身.会话们.get(会话标识)#会话
        if 会话 is not None:#委托
            会话.释放对象组(组)#委托

    def 控制台事件(自身,会话标识,类型,值们,时间戳,栈=None):#Console事件
        """为特定 DevTools Runtime 会话序列化一次 Console 调用。"""
        会话=自身.取会话(会话标识)#会话
        分配=会话.开始分配()#分配
        try:#序列化
            事件={'type':'console-api','event':{'type':类型,'arguments':会话.全部序列化(值们,'console',分配),'timestamp':时间戳}}#事件
            if 栈 is not None:#栈
                事件['event']['stackTrace']=栈#栈
            if not 是否json值(事件) or json字节长度(事件)+4096>自身.上限.maxResponseBytes:#超限
                会话.回滚(分配)#回滚
                return None#丢弃
            会话.提交分配(分配)#提交
            return 事件#返回
        except Exception:#失败
            会话.回滚(分配)#回滚
            raise#继续抛

    def 异常事件(自身,会话标识,错误,时间戳,栈=None):#异常事件
        """为 DevTools Runtime 会话序列化一次未捕获 Client 异常。"""
        会话=自身.取会话(会话标识)#会话
        分配=会话.开始分配()#分配
        try:#序列化
            事件={'type':'exception','event':{'timestamp':时间戳,'details':会话.描述异常(错误,'console',栈,分配)}}#事件
            if not 是否json值(事件) or json字节长度(事件)+4096>自身.上限.maxResponseBytes:#超限
                会话.回滚(分配)#回滚
                return None#丢弃
            会话.提交分配(分配)#提交
            return 事件#返回
        except Exception:#失败
            会话.回滚(分配)#回滚
            raise#继续抛

    def 重置(自身):#重置
        """源代数结束或重连时释放全部会话。"""
        自身.响应分配.clear()#清挂起
        for 会话 in 自身.会话们.values():#关会话
            会话.关闭()#关
        自身.会话们.clear()#清表

    def 取会话(自身,会话标识):#取或建会话
        """取或建会话。"""
        会话=自身.会话们.get(会话标识)#已有
        if 会话 is None:#新建
            会话=客户端运行时会话(自身.上限.maxObjectsPerSession,自身.上限.maxPropertiesPerResult,自身.解析脚本)#会话
            自身.会话们[会话标识]=会话#登记
        return 会话#返回
