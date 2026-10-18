'所有语音界面共用的一份宿主就绪镜像'
import threading#就绪流在后台读，登记不卡住
from ....api.网关.异常 import 远程流载体错误#流正常结束也算载体失败
from ....客户端.存储 import 创建快照存储#就绪快照

__all__=['观察就绪度']#挂载时订阅一次


def 观察就绪度(上下文):
    '每个客户端插件订阅一次，与页面和会话无关。返回状态和拆除函数'
    状态=创建快照存储({'catalog':None,'connected':False,'error':None})#目录、连接、传输错误分开
    已拆除={'值':False}#拆除后不再改写错误

    def 失败(错误):
        '传输失败只记下错误，不改写宿主目录'
        快照=状态.getSnapshot()#当前快照
        if isinstance(快照,dict) is False:#还不是字典
            快照={'catalog':None,'connected':False,'error':None}#补一份
        if isinstance(错误,BaseException):#取消息
            消息=str(错误)#异常消息
        else:#其它值
            消息=str(错误)#转成文字
        下一=dict(快照)#拷贝
        下一['connected']=False#断开
        下一['error']=消息#留下错误
        状态.set(下一)#通知界面

    def 打开(信号):
        '跟随宿主 speech 就绪'
        return 上下文.remote.speech.follow(信号)#这一代的快照

    def 流结束(已接受=None):
        '就绪流自己结束，交给载体失败'
        return 远程流载体错误('Speech readiness stream ended')#可重试

    流=getattr(上下文.remote,'$stream')({#一条可重连的逻辑流
        'name':'Speech readiness',#流名保持英文
        'open':打开,#打开一代
        'ended':流结束,#正常结束的分类
        'carrierFailed':失败,#载体失败只记错误
    })

    def 观察():
        '逐项写入目录，并接受这一代的开口'
        try:#读到拆除或终端失败为止
            for 项 in 流:#一项目录
                状态.set({'catalog':项.value,'connected':True,'error':None})#连上并清掉错误
                项.accept()#接受开口
        except Exception as 错误:#终端失败
            if 已拆除['值'] is False:#还没拆除才记
                失败(错误)#写入错误

    观察线程=threading.Thread(target=观察)#不挡住登记
    观察线程.start()#开始读

    def 拆除():
        '停流并等观察线程结束'
        已拆除['值']=True#先挡住失败回调
        流.dispose()#永久停止
        观察线程.join()#等这一轮结束

    return {'state':状态,'dispose':拆除}#共享快照和清理
