import json,threading,uuid#帧编码、读线程与请求 id
from ...内核.作用域 import 操作任务#未决请求
from ...工具.超时 import 中止控制器,若已中止则抛出,已中止#中止
from .模式 import ssh错误#本包基类

__all__=['ssh协议版本','ssh进程句柄上限','ssh文本流上限','远程操作错误','ssh请求对等']#仅中文公开名

ssh协议版本=1#线协议版本
ssh进程句柄上限=128#每辅助进程句柄
ssh文本流上限=128#打开的文本迭代器

管理限额={#管理类请求限额
    'heartbeat':1,#心跳
    'close':1,#关闭
    'process.terminate':ssh进程句柄上限,#终止
    'fs.streamClose':ssh文本流上限,#关流
}#限额结束

class 远程操作错误(ssh错误):#带码远端错误
    """保留类型化文件系统或沙箱码。"""
    def __init__(自身,消息,码=None):#记下英文消息与码
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息
        自身.name='RemoteOperationError'#固定名
        自身.code=码#可选码

def 请求分类(方法):#普通或管理
    """管理方法用自己的限额。"""
    if 方法 in 管理限额:#管理
        return 方法#该类
    return 'ordinary'#普通

def 操作错误(错误):#收成 Error
    """非异常则包一层。"""
    if isinstance(错误,BaseException):#已是
        return 错误#原样
    return ssh错误(str(错误))#包装

class ssh请求对等:#有界 JSON 帧对等
    """拥有未决调用；断连拒绝含糊操作，从不重放。"""
    def __init__(自身,输入流,输出流,最大帧字节,最大未决,处理=None):#绑流
        """登记读写错误并开读线程。"""
        自身.输入=输入流#可读
        自身.输出=输出流#可写
        自身.最大帧字节=最大帧字节#帧上限
        自身.最大未决=最大未决#普通未决上限
        自身.处理=处理#入站处理
        自身.未决={}#id → 任务与分类
        自身.活动={}#id → 控制器与分类
        自身.写锁=threading.Lock()#写串行
        自身.排队字节=0#写队列
        自身.失败=None#传输失败
        自身.关闭回调=[]#closed 监听
        def 流出错(错误=None):#流错误
            """关闭对等。"""
            if 错误 is None:#无因
                自身.关闭()#默认文案
            else:#有因
                自身.关闭(操作错误(错误))#关闭
        自身.输入.on('error',流出错)#输入错
        自身.输出.on('error',流出错)#输出错
        自身.输出.on('close',流出错)#输出关
        线程=threading.Thread(target=自身.读帧)#读循环
        线程.start()#启动

    def 请求(自身,方法,参数,模式,信号=None):#发请求并校验
        """取消不回滚已完成远端副作用。"""
        若已中止则抛出(信号)#已中止
        if 自身.失败 is not None:#已失败
            raise 自身.失败#传输失败
        种类=请求分类(方法)#分类
        if 自身.已满(种类,自身.未决.values()):#限额
            raise ssh错误('SSH helper pending request limit reached')#满
        标识=str(uuid.uuid4())#请求 id
        任务=操作任务()#未决
        自身.未决[标识]={'任务':任务,'requestClass':种类}#登记
        def 中止时():#信号中止
            """取消帧；远端清理未完成仍占额度。"""
            任务.拒绝(ssh错误('SSH operation cancelled; a completed remote mutation is not rolled back'))#拒绝
            自身.发送({'type':'cancel','id':标识})#取消帧
        if 信号 is not None and hasattr(信号,'addEventListener'):#DOM 信号
            信号.addEventListener('abort',中止时,{'once':True})#一次
        elif 信号 is not None:# Event
            def 监视():#等中止
                """置位后取消。"""
                信号.wait()#等待
                if 标识 in 自身.未决:#仍未决
                    中止时()#取消
            threading.Thread(target=监视).start()#监视
        try:#发送并等
            自身.发送({'type':'request','id':标识,'method':方法,'params':参数})#请求帧
            值=任务.等待()#结果
            return 模式(值)#校验
        finally:#摘监听
            pass#Event 监视自行结束

    def 关闭(自身,错误=None):#失败未决
        """不声称回滚。"""
        if 错误 is None:#默认文案
            错误=ssh错误('SSH connection lost; remote operation outcome and cleanup are unknown')#默认
        if 自身.失败 is not None:#已关
            return#忽略
        自身.失败=错误#记下
        for 项 in list(自身.未决.values()):#未决
            项['任务'].拒绝(错误)#拒绝
        自身.未决.clear()#清空
        for 项 in list(自身.活动.values()):#活动
            项['controller'].中止(错误)#中止处理
        自身.活动.clear()#清空
        if hasattr(自身.输入,'destroy'):#毁输入
            自身.输入.destroy()#毁
        if hasattr(自身.输出,'destroy'):#毁输出
            自身.输出.destroy()#毁
        for 回调 in 自身.关闭回调:#通知
            回调(错误)#回调

    def 发送(自身,帧):#写一帧
        """4 字节大端长度加 JSON。"""
        if 自身.失败 is not None:#已失败
            raise 自身.失败#拒绝
        体=json.dumps(帧,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode('utf-8')#JSON
        if len(体)>自身.最大帧字节 or 自身.排队字节+len(体)+4>自身.最大帧字节*2:#超限
            raise ssh错误('SSH helper frame or write queue limit exceeded')#超限
        头=len(体).to_bytes(4,'big')#长度
        字节=头+体#帧
        with 自身.写锁:#串行写
            自身.排队字节+=len(字节)#记账
            自身.输出.write(字节)#写出
            自身.排队字节-=len(字节)#还账

    def 读帧(自身):#读循环
        """按长度帧切分。"""
        try:#读
            缓冲=b''#未消费
            while True:#直到断
                块=自身.输入.read(65536) if hasattr(自身.输入,'read') else None#读
                if not 块:#结束
                    break#停
                缓冲+=块#追加
                while True:#切帧
                    if len(缓冲)<4:#不够头
                        break#等
                    大小=int.from_bytes(缓冲[:4],'big')#长度
                    if 大小==0 or 大小>自身.最大帧字节:#非法
                        raise ssh错误('SSH helper sent an invalid frame length')#非法
                    if len(缓冲)<4+大小:#不够体
                        break#等
                    载荷=缓冲[4:4+大小]#体
                    缓冲=缓冲[4+大小:]#剩余
                    帧=json.loads(载荷.decode('utf-8'))#JSON
                    自身.收取(帧)#分发
            if len(缓冲)>0:#半帧
                raise ssh错误('SSH helper disconnected during a frame; outcome is unknown')#半帧
            raise ssh错误('SSH helper disconnected; outcome is unknown')#干净断
        except Exception as 错误:#读失败
            自身.关闭(操作错误(错误))#关闭

    def 收取(自身,帧):#分发一帧
        """结果、错误、取消或入站请求。"""
        类型=帧['type'] if 'type' in 帧 else None#类型
        if 类型=='result' or 类型=='error':#应答
            项=自身.未决.get(帧['id']) if 'id' in 帧 else None#未决
            if 项 is None:#已取消仍可完成
                return#忽略
            del 自身.未决[帧['id']]#摘
            if 类型=='result':#成功
                项['任务'].兑现(帧['value'] if 'value' in 帧 else None)#兑现
            else:#远端错误
                错=帧['error'] if 'error' in 帧 else {}#错误
                项['任务'].拒绝(远程操作错误(错['message'] if 'message' in 错 else '',错['code'] if 'code' in 错 else None))#拒绝
            return#结束
        if 类型=='cancel':#取消入站
            活动=自身.活动.get(帧['id']) if 'id' in 帧 else None#活动
            if 活动 is not None:#有
                活动['controller'].中止(ssh错误('SSH caller cancelled the operation'))#中止
            return#结束
        方法=帧['method'] if 'method' in 帧 else ''#方法
        种类=请求分类(方法)#分类
        if 自身.处理 is None or 帧['id'] in 自身.活动 or 自身.已满(种类,自身.活动.values()):#意外
            raise ssh错误('SSH helper received an unexpected or excessive request')#意外
        控制器=中止控制器()#本请求中止
        自身.活动[帧['id']]={'controller':控制器,'requestClass':种类}#登记
        def 处理体():#线程
            """调用处理并回帧。"""
            try:#处理
                值=自身.处理(方法,帧['params'] if 'params' in 帧 else None,控制器.信号)#处理
                自身.发送({'type':'result','id':帧['id'],'value':值 if 值 is not None else None})#结果
            except Exception as 错误:#失败
                细节=操作错误(错误)#异常
                码=细节.code if hasattr(细节,'code') and isinstance(细节.code,str) else None#码
                体={'name':type(细节).__name__,'message':str(细节)}#错误体
                if 码 is not None:#有码
                    体['code']=码#码
                自身.发送({'type':'error','id':帧['id'],'error':体})#错误帧
            finally:#摘活动
                if 帧['id'] in 自身.活动:#仍在
                    del 自身.活动[帧['id']]#摘
        threading.Thread(target=处理体).start()#处理

    def 已满(自身,种类,请求们):#限额
        """该类是否已达上限。"""
        限额=自身.最大未决 if 种类=='ordinary' else 管理限额[种类]#上限
        计数=0#计数
        for 请求 in 请求们:#逐个
            if 请求['requestClass']==种类:#同类
                计数+=1#加
        return 计数>=限额#满
