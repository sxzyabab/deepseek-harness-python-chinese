"""页面与 worker 宿主之间的隧道帧协议。帧经 `postMessage` 穿越，
故入站帧在使用前须校验。

对齐上游 `webworker-runtime/src/transport/frames.ts`。公开面仅中文名。
"""
__all__=['解析入站帧']#仅中文公开名

def 解析入站帧(数据):#校验入站帧
    """将 `postMessage` 载荷校验为隧道帧。

    参数:
        数据: worker 收到的消息数据。
    返回:
        该帧。
    """
    if not isinstance(数据,dict):#非对象
        raise Exception(f'webworker tunnel: message is not a frame: {数据}')#拒绝
    帧=数据#当作字典
    if 帧.get('t')=='init':#初始化
        if not isinstance(帧.get('image'),str):#缺镜像
            raise Exception('webworker tunnel: init frame needs a string image url')#拒绝
        覆盖层=帧.get('overlays')#覆盖层
        if not isinstance(覆盖层,list) or any(not isinstance(层,str) for 层 in 覆盖层):#覆盖层非法
            raise Exception('webworker tunnel: init frame needs an array of string overlay urls')#拒绝
        return {'t':'init','image':帧['image'],'overlays':覆盖层}#返回init
    标识=帧.get('id')#取id
    if not isinstance(标识,(str,int)):#id不可用
        raise Exception(f'webworker tunnel: frame has no usable id: {帧.get("id")!r}')#拒绝
    if 帧.get('t')=='abort':#中止帧
        return {'t':'abort','id':标识}#返回中止
    if 帧.get('t')=='stream-open':#流打开
        端点=帧.get('endpoint')#端点
        if not isinstance(端点,str) or len(端点)==0:#端点非法
            raise Exception(f'webworker tunnel: stream {标识} needs a non-empty endpoint')#拒绝
        return {'t':'stream-open','id':标识,'endpoint':端点,'payload':帧.get('payload')}#返回流打开
    if 帧.get('t')!='req':#未知类型
        raise Exception(f'webworker tunnel: unknown frame type {帧.get("t")!r}')#拒绝
    if not isinstance(帧.get('method'),str) or not isinstance(帧.get('url'),str):#方法或URL非法
        raise Exception(f'webworker tunnel: request {标识} needs string method and url')#拒绝
    原始头=帧.get('headers')#头
    if not isinstance(原始头,dict):#头非法
        raise Exception(f'webworker tunnel: request {标识} needs a headers object')#拒绝
    头={}#规范化头
    for 键,值 in 原始头.items():#逐头
        if isinstance(值,str):#只收字符串
            头[键.lower()]=值#小写键
    正文=帧.get('body')#取正文
    if 正文 is not None and not isinstance(正文,(bytes,bytearray,memoryview)):#正文类型错
        raise Exception(f'webworker tunnel: request {标识} body must be an ArrayBuffer')#拒绝
    return {'t':'req','id':标识,'method':帧['method'],'url':帧['url'],'headers':头,'body':正文}#返回请求帧
