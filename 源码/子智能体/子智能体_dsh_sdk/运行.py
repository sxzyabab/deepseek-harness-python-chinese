"""DSH SDK 子进程客户端（对齐 upstream subagent-dsh-sdk/run.ts）。"""
import uuid#子 id
from ...内核.会话 import 会话标识#品牌
from ...sdk.客户端.高层 import 深求装备#Harness 高层 API
默认关闭超时毫秒=10000#shutdown 上限
默认处置eof宽限毫秒=6000#EOF 宽限
默认处置宽限毫秒=3000#处置宽限

def 取字段(对象,键,缺省=None):#读字段
    if 对象 is None:return 缺省#空
    if isinstance(对象,dict):return 对象.get(键,缺省)#映射
    return getattr(对象,键,缺省)#属性

def 解开(值):#可等待则等待
    等待=getattr(值,'wait',None) or getattr(值,'等待',None)#方法
    if callable(等待):return 等待()#等待
    return 值#同步

def 启动sdk跑(请求,规格):#startSdkRun
    """用深求装备驱动一个独立子运行时。"""
    父=取字段(请求,'parent')#父
    工作目录=取字段(规格,'cwd') or 取字段(取字段(父,'session').header,'cwd')#cwd
    if 工作目录 is None:#无 cwd
        raise Exception('subagent-dsh-sdk: parent session has no cwd')#拒绝
    子标识=会话标识(str(uuid.uuid4()))#子 id
    装备=深求装备({
        'launch':{'dshHome':规格['dshHome'],'env':规格.get('env',{})},
        'cwd':工作目录,'provider':规格.get('provider','deepseek-official'),
        'model':规格.get('model','deepseek-v4-flash'),
        **({} if 规格.get('maxTokens') is None else {'maxTokens':规格['maxTokens']}),
    })#构造装备
    提示=取字段(请求,'prompt')#提示
    信号=取字段(请求,'signal')#取消
    if getattr(信号,'aborted',False) or getattr(信号,'已中止',False):#已取消
        raise Exception('aborted')#取消
    import concurrent.futures#Future
    未来=concurrent.futures.Future()#结果
    def 工作者():#后台
        try:#跑
            解开(装备.启动运行时())#握手
            会话=装备.会话(str(子标识))#开会话
            输出=解开(会话.run(提示))#跑一轮
            未来.set_result({'output':[{'type':'text','text':str(输出)}],'stopReason':'completed'})#成功
        except BaseException as 错误:#失败
            未来.set_exception(错误)#拒绝
        finally:#关
            解开(装备.关闭())#关闭装备
    import threading#线程
    threading.Thread(target=工作者,daemon=True).start()#启动
    class 结果代理:#thenable
        def wait(自身,超时=None):return 未来.result(超时)#等待
        def 等待(自身,超时=None):return 自身.wait(超时)#中文
    async def 处置():#dispose
        未来.result()#等结果
        解开(装备.关闭())#关
    return {'id':子标识,'localAgent':None,'result':结果代理(),'dispose':处置}#句柄

__all__=['默认关闭超时毫秒','默认处置eof宽限毫秒','默认处置宽限毫秒','启动sdk跑']#公开面
