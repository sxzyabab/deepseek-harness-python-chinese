"""四象限 RPC 消息层模式。对齐上游 `host/apiproxy/src/api/rpc.schema.ts`。公开面仅中文名。"""

__all__=['Rpc标识','服务端响应模式','服务端请求模式','传输错误','rpc结果模式']#公开面

def Rpc标识(标识):#品牌化 rpc id
    """把字符串打成 Rpc 标识（纯品牌，不校验格式）。"""
    return 标识#编译期品牌，运行时原样

def 传输错误(错误):#载体抛错折成业务错误支
    """对齐上游 transportError：internal + 空 details。"""
    消息=错误.args[0] if isinstance(错误,BaseException) and 错误.args else str(错误)#取消息
    return {'ok':False,'error':{'code':'internal','message':str(消息),'details':{}}}#错误支

class rpc结果模式:#RpcResult 形状校验
    """业务成功/失败结果槽。"""
    @staticmethod
    def parse(值):#解析 result 槽
        """ok 判别联合；失败时 error 须为映射。"""
        if not isinstance(值,dict):#非映射
            raise Exception('invalid rpc result')#拒绝
        if 值.get('ok') is True:#成功支
            return {'ok':True,'value':值.get('value')}#value 可缺席
        if 值.get('ok') is False:#失败支
            错误=值.get('error')#错误体
            if not isinstance(错误,dict):#非映射
                raise Exception('invalid rpc error')#拒绝
            if not isinstance(错误.get('code'),str):#缺 code
                raise Exception('invalid rpc error code')#拒绝
            if not isinstance(错误.get('message'),str):#缺 message
                raise Exception('invalid rpc error message')#拒绝
            细节=错误.get('details')#details
            if 细节 is None:#缺 details
                细节={}#internal 等码用空对象
            if not isinstance(细节,dict):#非映射
                raise Exception('invalid rpc error details')#拒绝
            return {'ok':False,'error':{'code':错误['code'],'message':错误['message'],'details':细节}}#失败支
        raise Exception('invalid rpc result ok field')#缺 ok

class 服务端响应模式:#ServerResponse 完整形
    """S→C 一元响应信封。"""
    @staticmethod
    def parse(值):#解析 server-response
        """校验 type/rpcId/result。"""
        if not isinstance(值,dict):#非映射
            raise Exception('invalid server-response')#拒绝
        if 值.get('type')!='server-response':#判别标签
            raise Exception('invalid server-response type')#拒绝
        rpc标识=值.get('rpcId')#关联 id
        if not isinstance(rpc标识,str):#非字符串
            raise Exception('invalid server-response rpcId')#拒绝
        结果=rpc结果模式.parse(值.get('result'))#result 槽
        return {'type':'server-response','rpcId':Rpc标识(rpc标识),'result':结果}#完整形

class 服务端请求模式:#ServerRequest 完整形
    """S→C 推送/提问信封。"""
    @staticmethod
    def parse(值):#解析 server-request
        """校验 type/rpcId/method/payload。"""
        if not isinstance(值,dict):#非映射
            raise Exception('invalid server-request')#拒绝
        if 值.get('type')!='server-request':#判别标签
            raise Exception('invalid server-request type')#拒绝
        rpc标识=值.get('rpcId')#关联 id
        if not isinstance(rpc标识,str):#非字符串
            raise Exception('invalid server-request rpcId')#拒绝
        方法=值.get('method')#帧方法
        if not isinstance(方法,str):#非字符串
            raise Exception('invalid server-request method')#拒绝
        if 'payload' not in 值:#缺 payload 键
            raise Exception('invalid server-request payload')#拒绝
        return {'type':'server-request','rpcId':Rpc标识(rpc标识),'method':方法,'payload':值['payload']}#完整形
