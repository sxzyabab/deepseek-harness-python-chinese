import threading#客户端断开中止

__all__=['默认最大请求正文字节','桥接']#仅中文公开名

默认最大请求正文字节=160*1024*1024#默认 160MiB 正文上限

def 桥接(请求,响应,接口处理,最大请求正文字节=None):#Node HTTP → fetch
    """把一条 HTTP 请求桥到 fetch 形态的处理函数。"""
    if 最大请求正文字节 is None:#未传
        最大请求正文字节=默认最大请求正文字节#默认上限
    中止器=threading.Event()#客户端断开时 abort
    def 响应关闭(_事件=None):#响应关闭
        """尚未正常结束则视为客户端走开。"""
        已结束=响应.writableEnded#是否已 end
        if not 已结束:#未正常结束
            中止器.set()#标中止
    响应.on('close',响应关闭)#挂 close
    请求头表=请求.headers if 请求.headers is not None else {}#请求头
    声明长度=请求头表['content-length'] if isinstance(请求头表,dict) and 'content-length' in 请求头表 else None#声明的正文长度
    if 声明长度 is not None:#有 Content-Length
        try:#转数字
            if int(声明长度)>最大请求正文字节:#声明就已超上限
                响应.writeHead(413,{'connection':'close'})#Payload Too Large
                响应.end()#结束响应
                请求.destroy()#拆掉请求
                return#不再派发
        except (TypeError,ValueError):#畸形长度
            pass#继续读
    块列表=[]#正文块
    已收=0#已收字节
    读体=请求.readBody if hasattr(请求,'readBody') else None#可选整读
    if callable(读体):#有整读面
        正文=读体()#读
        if 正文 is not None and len(正文)>0:#有正文
            if isinstance(正文,str):#文本
                正文=正文.encode('utf-8')#编码
            已收=len(正文)#长度
            if 已收>最大请求正文字节:#超上限
                响应.writeHead(413,{'connection':'close'})#Payload Too Large
                响应.end()#结束
                return#不派发
            块列表.append(正文)#收下
    elif hasattr(请求,'rfile'):#BaseHTTP 形
        长度=int(声明长度) if 声明长度 is not None else 0#长度
        if 长度>0:#有正文
            if 长度>最大请求正文字节:#超上限
                响应.writeHead(413,{'connection':'close'})#Payload Too Large
                响应.end()#结束
                return#不派发
            块列表.append(请求.rfile.read(长度))#读
            已收=长度#记下
    方法=请求.method if 请求.method is not None else 'GET'#方法
    网址=请求.url if 请求.url is not None else '/'#url
    过滤头={}#只保留字符串头
    if isinstance(请求头表,dict):#映射
        for 键,值 in 请求头表.items():#逐个
            if isinstance(值,str):#字符串头
                过滤头[键]=值#收下
    体=b''.join(块列表) if len(块列表)>0 else None#合并正文
    标准请求={#拼 fetch 形请求
        'url':'http://dsh.internal'+网址,#绝对 URL
        'method':方法,#方法
        'headers':过滤头,#头
        'body':体,#正文
        'signal':中止器,#取消信号
    }#请求结束
    标准响应=接口处理['fetch'](标准请求)#交给 fetch 处理
    状态=标准响应['status'] if 'status' in 标准响应 else 200#状态
    响应头=标准响应['headers'] if 'headers' in 标准响应 and 标准响应['headers'] is not None else {}#头
    响应.writeHead(状态,响应头)#抄状态与头
    响应体=标准响应['body'] if 'body' in 标准响应 else None#正文
    if 响应体 is None:#无正文
        响应.end()#直接结束
        return#完
    if hasattr(响应体,'__iter__') and not isinstance(响应体,(bytes,str,bytearray)):#流式
        for 块 in 响应体:#逐块
            if 中止器.is_set():#已中止
                break#停
            响应.write(块)#写出
        响应.end()#全部写完
        return#完
    响应.end(响应体)#一次性正文
