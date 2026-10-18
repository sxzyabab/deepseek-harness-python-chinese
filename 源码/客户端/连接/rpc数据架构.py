'连接 RPC 信封的运行时校验。没有 zod，按上游字段在本包判断'
from .rpc import Rpc标识#关联 id


class 问题集:
    '校验失败时交给调用方的 issues'
    def __init__(自身,问题):
        '记下问题列表'
        自身.issues=问题#问题


class 校验结果:
    'safeParse 的结果。成功有 data，失败有 error.issues'
    def __init__(自身,成功,数据=None,问题=None):
        '记下是否成功'
        自身.success=成功#是否通过
        自身.data=数据#通过后的值
        自身.error=None if 成功 else 问题集(问题 or [])#失败问题


def 问题(路径,消息):
    '一条字段问题'
    return {'code':'invalid','message':消息,'path':路径}#问题


def 是否记录(值):
    '普通对象。数组和空值都不是'
    return isinstance(值,dict)#字典


class 标识模式:
    'rpcId 必须是字符串'
    def safeParse(自身,值):
        '通过则原样返回字符串'
        if isinstance(值,str):#字符串
            return 校验结果(True,值)#通过
        return 校验结果(False,问题=[问题([],'rpcId must be a string')])#拒绝

    def __call__(自身,值):
        '不通过就抛'
        结果=自身.safeParse(值)#校验
        if not 结果.success:#失败
            raise TypeError('rpcId must be a string')#抛出
        return 结果.data#字符串


class 错误模式:
    '端点失败：code、message、details'
    def safeParse(自身,值):
        '三项都要在，details 必须是对象'
        if not 是否记录(值):#不是对象
            return 校验结果(False,问题=[问题([],'error must be an object')])#拒绝
        收集=[]#问题
        if not isinstance(值.get('code'),str):#code
            收集.append(问题(['code'],'code must be a string'))#问题
        if not isinstance(值.get('message'),str):#message
            收集.append(问题(['message'],'message must be a string'))#问题
        if not 是否记录(值.get('details')):#details
            收集.append(问题(['details'],'details must be an object'))#问题
        if 收集:#有问题
            return 校验结果(False,问题=收集)#拒绝
        return 校验结果(True,{'code':值['code'],'message':值['message'],'details':值['details']})#通过


class 结果模式:
    '成功值或通用失败。值模式由端点自己给出'
    def __init__(自身,值模式):
        '记下成功值的模式'
        自身.值模式=值模式#值模式

    def safeParse(自身,值):
        'ok 为真走值模式，ok 为假走错误模式'
        if not 是否记录(值) or 'ok' not in 值:#不是结果对象
            return 校验结果(False,问题=[问题(['ok'],'result.ok is required')])#拒绝
        if 值['ok'] is True:#成功
            if 自身.值模式 is None:#任意值，键可以不写
                业务=值['value'] if 'value' in 值 else None#缺席当 undefined
                return 校验结果(True,{'ok':True,'value':业务})#通过
            内层=自身.值模式.safeParse(值.get('value'))#校验值
            if not 内层.success:#值不合法
                return 校验结果(False,问题=内层.error.issues)#拒绝
            return 校验结果(True,{'ok':True,'value':内层.data})#通过
        if 值['ok'] is False:#失败
            错误=rpc错误模式.safeParse(值.get('error'))#错误对象
            if not 错误.success:#不合法
                return 校验结果(False,问题=错误.error.issues)#拒绝
            return 校验结果(True,{'ok':False,'error':错误.data})#通过
        return 校验结果(False,问题=[问题(['ok'],'result.ok must be boolean')])#拒绝


class 任意模式:
    '任意值都通过'
    def safeParse(自身,值):
        '原样通过'
        return 校验结果(True,值)#通过


class 可选任意模式:
    '键可以不写。写出的值任意'
    def safeParse(自身,值):
        '原样通过，包含 None'
        return 校验结果(True,值)#通过


def rpc结果模式(值模式):
    '按端点自己的值模式组装结果模式'
    return 结果模式(值模式)#结果模式


class 客户端请求模式类:
    'client-request 信封。端点载荷留给端点自己校验'
    def safeParse(自身,值):
        'type、rpcId、method 必须符合，payload 必须写出'
        if not 是否记录(值):#不是对象
            return 校验结果(False,问题=[问题([],'client-request must be an object')])#拒绝
        收集=[]#问题
        if 值.get('type')!='client-request':#类型
            收集.append(问题(['type'],'type must be client-request'))#问题
        标识=rpc标识模式.safeParse(值.get('rpcId'))#关联
        if not 标识.success:#不是字符串
            收集.extend(标识.error.issues)#带上
        if not isinstance(值.get('method'),str):#方法
            收集.append(问题(['method'],'method must be a string'))#问题
        if 'payload' not in 值:#载荷键必须在
            收集.append(问题(['payload'],'payload is required'))#问题
        if 收集:#有问题
            return 校验结果(False,问题=收集)#拒绝
        return 校验结果(True,{#信封
            'type':'client-request',#类型
            'rpcId':Rpc标识(值['rpcId']),#关联
            'method':值['method'],#方法
            'payload':值['payload'],#载荷
        })#通过

    def __call__(自身,值):
        '不通过就抛'
        结果=自身.safeParse(值)#校验
        if not 结果.success:#失败
            raise TypeError('invalid client-request message')#抛出
        return 结果.data#信封


class 服务端响应模式类:
    'server-response 信封。值留给调用方'
    def safeParse(自身,值):
        'type、rpcId、result 都要合法'
        if not 是否记录(值):#不是对象
            return 校验结果(False,问题=[问题([],'server-response must be an object')])#拒绝
        收集=[]#问题
        if 值.get('type')!='server-response':#类型
            收集.append(问题(['type'],'type must be server-response'))#问题
        标识=rpc标识模式.safeParse(值.get('rpcId'))#关联
        if not 标识.success:#不是字符串
            收集.extend(标识.error.issues)#带上
        结果=服务端结果.safeParse(值.get('result'))#结果
        if not 结果.success:#结果不合法
            收集.extend(结果.error.issues)#带上
        if 收集:#有问题
            return 校验结果(False,问题=收集)#拒绝
        return 校验结果(True,{#信封
            'type':'server-response',#类型
            'rpcId':Rpc标识(值['rpcId']),#关联
            'result':结果.data,#结果
        })#通过


class 消息模式:
    '两条方向里的任意一条'
    def safeParse(自身,值):
        '先看 type，再走对应信封'
        if not 是否记录(值):#不是对象
            return 校验结果(False,问题=[问题(['type'],'type is required')])#拒绝
        if 值.get('type')=='client-request':#请求
            return 客户端请求模式.safeParse(值)#请求
        if 值.get('type')=='server-response':#响应
            return 服务端响应模式.safeParse(值)#响应
        return 校验结果(False,问题=[问题(['type'],'type must be client-request or server-response')])#拒绝


rpc标识模式=标识模式()#关联 id
rpc错误模式=错误模式()#失败对象
客户端请求模式=客户端请求模式类()#请求信封
服务端结果=rpc结果模式(可选任意模式())#响应里的 result，值可选
服务端响应模式=服务端响应模式类()#响应信封
rpc消息模式=消息模式()#任一方向
