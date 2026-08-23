"""/api 传输的 node:http ↔ fetch 桥（web 载体的宿主侧）。

对齐上游 `connection/src/http-bridge.ts`。公开面仅中文名。fetch 形态的处理函数本身与传输无关。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

__all__=['默认最大请求正文字节','桥接']#仅中文公开名

默认最大请求正文字节=160*1024*1024#默认 160MiB 正文上限

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

def 桥接(请求,响应,接口处理,最大请求正文字节=None):#Node HTTP → fetch
    """把一条 HTTP 请求桥到 fetch 形态的处理函数。"""
    if 最大请求正文字节 is None:#未传
        最大请求正文字节=默认最大请求正文字节#默认上限
    中止器={'aborted':False}#客户端断开时 abort
    def 响应关闭(_事件=None):#响应关闭
        """尚未正常结束则视为客户端走开。"""
        已结束=取字段(响应,'writableEnded',False)#是否已 end
        if not 已结束:#未正常结束
            中止器['aborted']=True#标中止
    if hasattr(响应,'on'):#有事件面
        响应.on('close',响应关闭)#挂 close
    头们=取字段(请求,'headers',{}) or {}#请求头
    声明长度=头们.get('content-length') if isinstance(头们,dict) else None#声明的正文长度
    if 声明长度 is not None:#有 Content-Length
        try:#转数字
            if int(声明长度)>最大请求正文字节:#声明就已超上限
                响应.writeHead(413,{'connection':'close'})#Payload Too Large
                响应.end()#结束响应
                if hasattr(请求,'destroy'):#可拆
                    请求.destroy()#拆掉请求
                return#不再派发
        except (TypeError,ValueError):#畸形长度
            pass#继续读
    块们=[]#正文块
    已收=0#已收字节
    读体=取字段(请求,'readBody',None)#可选整读
    if callable(读体):#有整读面
        正文=读体()#读
        if 正文:#有正文
            if isinstance(正文,str):#文本
                正文=正文.encode('utf-8')#编码
            已收=len(正文)#长度
            if 已收>最大请求正文字节:#超上限
                响应.writeHead(413,{'connection':'close'})#Payload Too Large
                响应.end()#结束
                return#不派发
            块们.append(正文)#收下
    elif hasattr(请求,'rfile'):#BaseHTTP 形
        长度=int(声明长度) if 声明长度 is not None else 0#长度
        if 长度>0:#有正文
            if 长度>最大请求正文字节:#超上限
                响应.writeHead(413,{'connection':'close'})#Payload Too Large
                响应.end()#结束
                return#不派发
            块们.append(请求.rfile.read(长度))#读
            已收=长度#记下
    方法=取字段(请求,'method') or 'GET'#方法
    网址=取字段(请求,'url') or '/'#url
    过滤头={}#只保留字符串头
    if isinstance(头们,dict):#映射
        for 键,值 in 头们.items():#逐个
            if isinstance(值,str):#字符串头
                过滤头[键]=值#收下
    体=b''.join(块们) if 块们 else None#合并正文
    标准请求={#拼 fetch 形请求
        'url':'http://dsh.internal'+网址,#绝对 URL
        'method':方法,#方法
        'headers':过滤头,#头
        'body':体,#正文
        'signal':中止器,#取消信号
    }#请求结束
    标准响应=解开(接口处理.fetch(标准请求))#交给 fetch 处理
    状态=取字段(标准响应,'status',200)#状态
    响应头=取字段(标准响应,'headers',{}) or {}#头
    if hasattr(响应头,'items'):#映射
        响应.writeHead(状态,dict(响应头.items()) if not isinstance(响应头,dict) else 响应头)#抄状态与头
    else:#已是 dict
        响应.writeHead(状态,响应头)#抄
    响应体=取字段(标准响应,'body',None)#正文
    if 响应体 is None:#无正文
        响应.end()#直接结束
        return#完
    if hasattr(响应体,'__iter__') and not isinstance(响应体,(bytes,str,bytearray)):#流式
        for 块 in 响应体:#逐块
            if 中止器['aborted']:#已中止
                break#停
            写出=取字段(响应,'write',None)#写
            if callable(写出):#有 write
                写出(块)#写出
            else:#只有 end
                响应.end(块)#一次写出
                return#完
        响应.end()#全部写完
        return#完
    响应.end(响应体)#一次性正文
