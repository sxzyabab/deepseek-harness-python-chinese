import ssl,socket,threading#TLS-PSK、Unix 套接字与握手超时
from ...工具.超时 import 若已中止则抛出,等待中止#中止
from .模式 import ssh错误#本包基类

__all__=['ssh流tls选项','套接字流','认证流']#仅中文公开名

ssh流tls选项={#无证书 PSK 与 AEAD 记录；无未认证密码回落
    'ciphers':'PSK-AES256-GCM-SHA384',#密码套件
    'minVersion':'TLSv1.2',#下限
    'maxVersion':'TLSv1.2',#上限
}#选项结束

class 套接字流:#给请求对等用的阻塞套接字面
    """把操作系统套接字收成 协议.py 所用的读/写/关闭面。"""
    def __init__(自身,套接字对象):#包一层
        """记下已连接套接字。"""
        自身._套接字=套接字对象#底层
        自身._监听={'error':[],'close':[],'connect':[],'data':[],'drain':[],'secureConnect':[]}#事件表
        自身.closed=False#是否已关
        自身._暂停=False#pause 旗
        自身._暂停事件=threading.Event()#恢复通知
        自身._暂停事件.set()#默认可读

    def on(自身,事件,回调):#登记监听
        """追加监听。"""
        自身._监听[事件].append(回调)#追加
        return 自身#链式

    def once(自身,事件,回调):#只触发一次
        """触发一次后摘掉。"""
        def 一次(*参数):#包装
            """摘掉后再调。"""
            自身.off(事件,一次)#摘
            回调(*参数)#调
        自身.on(事件,一次)#登记
        return 自身#链式

    def off(自身,事件,回调):#摘监听
        """移除一个监听。"""
        表=自身._监听[事件]#表
        if 回调 in 表:#有
            表.remove(回调)#摘
        return 自身#链式

    def write(自身,字节):#写出
        """阻塞写出全部字节。"""
        自身._套接字.sendall(字节)#写出
        return True#已接受

    def read(自身,大小):#读入
        """阻塞读；暂停时等待恢复。"""
        自身._暂停事件.wait()#等恢复
        return 自身._套接字.recv(大小)#读

    def pause(自身):#暂停读
        """暂停后续 read。"""
        自身._暂停=True#旗
        自身._暂停事件.clear()#堵

    def resume(自身):#恢复读
        """恢复 read。"""
        自身._暂停=False#旗
        自身._暂停事件.set()#放行

    def destroy(自身,错误=None):#关闭
        """关掉套接字并通知。"""
        if 自身.closed:#已关
            return#忽略
        自身.closed=True#记下
        自身._暂停事件.set()#放行阻塞读
        try:#关
            自身._套接字.close()#关
        except OSError:#已关
            pass#忽略
        if 错误 is not None:#有因
            for 回调 in list(自身._监听['error']):#错误
                回调(错误 if isinstance(错误,BaseException) else ssh错误(str(错误)))#通知
        for 回调 in list(自身._监听['close']):#关闭
            回调()#通知

    def pipe(自身,目标):#转发到可写
        """后台把读到的字节写到目标。"""
        def 转发():#线程
            """直到 EOF。"""
            try:#读
                while True:#循环
                    块=自身.read(65536)#读
                    if not 块:#结束
                        break#停
                    目标.write(块)#写
                if hasattr(目标,'end'):#半关
                    目标.end()#结束写
            except OSError as 错误:#失败
                自身.destroy(错误)#关
        线程=threading.Thread(target=转发)#后台
        线程.daemon=True#守护
        线程.start()#启动
        return 目标#链式

    def end(自身):#半关闭写
        """关掉写方向。"""
        try:#半关
            自身._套接字.shutdown(socket.SHUT_WR)#只关写
        except OSError:#已关
            pass#忽略

    def 触发(自身,事件,*参数):#内部派发
        """派发已登记监听。"""
        for 回调 in list(自身._监听[事件]):#逐个
            回调(*参数)#调

def 客户psk回调(能力十六进制):#PSK 客户端
    """身份 dsh-stream，密钥为十六进制能力。"""
    def 回调(提示):#ssl 回调
        """忽略提示，交身份与密钥。"""
        return 'dsh-stream',bytes.fromhex(能力十六进制)#身份与密钥
    return 回调#工厂

def 认证流(套接字对象,能力,超时毫秒,信号=None):#TLS-PSK 认证转发流
    """用管理通道私钥认证已连接套接字；密钥从不作为数据发送。返回已暂停的认证流。"""
    流=套接字对象 if isinstance(套接字对象,套接字流) else 套接字流(套接字对象)#统一面
    if 信号 is not None and 信号.is_set():#已中止
        流.destroy()#毁
        若已中止则抛出(信号)#抛原因或已中止错误
    上下文=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)#客户 TLS
    上下文.minimum_version=ssl.TLSVersion.TLSv1_2#下限
    上下文.maximum_version=ssl.TLSVersion.TLSv1_2#上限
    上下文.set_ciphers(ssh流tls选项['ciphers'])#PSK-AEAD
    上下文.check_hostname=False#PSK 无主机名
    上下文.verify_mode=ssl.CERT_NONE#无证书
    上下文.set_psk_client_callback(客户psk回调(能力))#PSK
    完成=threading.Event()#握手结束
    箱={'流':None,'错误':None}#结算
    def 握手():#线程
        """阻塞握手。"""
        try:#包装
            包装=上下文.wrap_socket(流._套接字,server_side=False)#握手
            箱['流']=套接字流(包装)#认证流
        except BaseException as 错误:#失败
            箱['错误']=错误#记下
        finally:#广播
            完成.set()#结束
    def 中止时():#信号中止
        """毁掉握手中的套接字。"""
        原因=ssh错误('SSH stream closed during authentication')#默认
        流.destroy(原因)#毁
    if 信号 is not None:#有信号
        def 监视():#等中止
            """置位后毁掉。"""
            等待中止(信号)#等置位
            if not 完成.is_set():#仍在握手
                中止时()#毁
        监视线程=threading.Thread(target=监视)#监视
        监视线程.daemon=True#守护
        监视线程.start()#启动
    工作=threading.Thread(target=握手)#握手线程
    工作.daemon=True#守护
    工作.start()#启动
    if not 完成.wait(超时毫秒/1000.0):#超时
        流.destroy(ssh错误('SSH stream authentication timed out'))#毁
        raise ssh错误('SSH stream authentication timed out')#超时
    if 箱['错误'] is not None:#失败
        流.destroy(箱['错误'] if isinstance(箱['错误'],BaseException) else ssh错误(str(箱['错误'])))#毁
        raise 箱['错误']#原样
    认证=箱['流']#已包装
    认证.pause()#暂停待消费方挂上
    return 认证#已认证流
