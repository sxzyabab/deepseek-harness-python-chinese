"""把 ApiProxy 映射成 fetch 形处理函数。对齐上游 `host/apiproxy/src/fetch/handler.ts`。公开面仅中文名。"""
import json,uuid#JSON 与推送帧 id
from urllib.parse import urlparse,parse_qs#路径与查询
from .接口.rpc模式 import Rpc标识,服务端响应模式,服务端请求模式#信封模式

__all__=['转fetch处理']#公开面

无效请求rpc标识=Rpc标识('invalid-request')#读不出 rpcId 时的哨兵

def _取字段(对象,键,缺省=None):#读映射或属性
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def _错误响应(rpc标识,错误):#200 + ok:false
    """包成 server-response 完整形。"""
    return {'status':200,'headers':{'content-type':'application/json'},'body':json.dumps({'type':'server-response','rpcId':rpc标识,'result':{'ok':False,'error':错误}},ensure_ascii=False).encode('utf-8')}#JSON 200

def _成功响应(窄形):#窄形 → server-response
    """把实现面窄形补成完整形。"""
    完整={'type':'server-response','rpcId':窄形['rpcId'],'result':窄形['result']}#完整形
    return {'status':200,'headers':{'content-type':'application/json'},'body':json.dumps(完整,ensure_ascii=False).encode('utf-8')}#JSON 200

def _解析client_request(正文):#校验 client-request
    """第一级信封解析。"""
    if not isinstance(正文,dict):#非映射
        raise ValueError('not a client-request object')#拒绝
    if 正文.get('type')!='client-request':#判别
        raise ValueError('invalid client-request type')#拒绝
    rpc标识=正文.get('rpcId')#关联 id
    if not isinstance(rpc标识,str):#非字符串
        raise ValueError('invalid client-request rpcId')#拒绝
    方法=正文.get('method')#方法键
    if not isinstance(方法,str):#非字符串
        raise ValueError('invalid client-request method')#拒绝
    if 'payload' not in 正文:#缺 payload
        raise ValueError('invalid client-request payload')#拒绝
    return {'type':'client-request','rpcId':Rpc标识(rpc标识),'method':方法,'payload':正文['payload']}#完整形

def _一元路由(api,方法,消息,信号):#按方法键派发
    """把窄形 RpcRequest 交给 api 实现面。"""
    域,名=方法.split('.',1) if '.' in 方法 else (方法,None)#拆域
    if 名 is None:#无点
        raise Exception(f'unknown unary method {方法!r}')#未知
    面=_取字段(api,域)#域面
    if 面 is None:#无此域
        raise Exception(f'unknown unary method {方法!r}')#未知
    调用=_取字段(面,名)#方法
    if not callable(调用):#不可调用
        raise Exception(f'unknown unary method {方法!r}')#未知
    请求={'rpcId':消息['rpcId'],'payload':消息['payload']}#窄形请求
    if 方法 in ('session.search','subagent.list','subagent.history','subagent.prompt','host.pickDirectory','host.listDirectory','host.openPath','agentPreset.openDocument','settings.openDocument','llm.discoverModels'):#带 signal
        return 调用(请求,信号)#转发取消
    return 调用(请求)#一元

def 转fetch处理(api):#toFetchHandler
    """把宿主 ApiProxy 包成 {fetch: ...}。"""
    class _处理器:#fetch 形
        @staticmethod
        def fetch(输入,初始化=None):#唯一 HTTP 入口
            """归一请求后按路径分发。"""
            if isinstance(输入,dict):#桥接形
                网址=输入.get('url','')#URL
                方法=输入.get('method','GET')#方法
                头=输入.get('headers',{}) or {}#头
                正文=输入.get('body')#正文
                信号=输入.get('signal')#取消
            else:#其它形当 dict 用
                网址=_取字段(输入,'url','')#URL
                方法=_取字段(输入,'method','GET')#方法
                头=_取字段(输入,'headers',{}) or {}#头
                正文=_取字段(输入,'body')#正文
                信号=_取字段(输入,'signal')#取消
            路径=urlparse(网址).path#pathname
            if 路径=='/api/respond' and 方法=='POST':#client-response
                try:#解析 JSON
                    体=json.loads(正文.decode('utf-8') if isinstance(正文,(bytes,bytearray)) else 正文)#正文
                except Exception:#非 JSON
                    return {'status':400,'headers':{},'body':b'body is not JSON'}#400
                if not isinstance(体,dict) or 体.get('type')!='client-response':#坏应答
                    return {'status':200,'headers':{'content-type':'application/json'},'body':json.dumps({'accepted':False,'reason':'bad-response'}).encode('utf-8')}#回执
                回执=api.respond(体)#实现面
                return {'status':200,'headers':{'content-type':'application/json'},'body':json.dumps(回执,ensure_ascii=False).encode('utf-8')}#JSON
            if 方法!='POST' or not 路径.startswith('/api/'):#其余只接受 /api POST
                return {'status':404,'headers':{},'body':b'not found'}#404
            媒体=(_取字段(头,'content-type','') or '').split(';',1)[0].strip().lower()#媒体类型
            if 媒体!='application/json':#非 JSON
                return {'status':415,'headers':{},'body':b'content type must be application/json'}#415
            try:#解析 JSON
                体=json.loads(正文.decode('utf-8') if isinstance(正文,(bytes,bytearray)) else 正文)#正文
            except Exception:#非 JSON
                return {'status':400,'headers':{},'body':b'body is not JSON'}#400
            方法键=路径[len('/api/'):]#路径段
            try:#校验信封
                消息=_解析client_request(体)#client-request
            except ValueError as 原因:#信封坏
                原始id=体.get('rpcId') if isinstance(体,dict) else None#尽力取 id
                rpc标识=Rpc标识(原始id) if isinstance(原始id,str) else 无效请求rpc标识#哨兵
                return _错误响应(rpc标识,{'code':'bad-request','message':'invalid client-request message','details':{'issues':[str(原因)]}})#200 业务错
            if 消息['method']!=方法键:#路径与 method 不一致
                return _错误响应(消息['rpcId'],{'code':'bad-request','message':f'method "{消息["method"]}" does not match path "{方法键}"','details':{'issues':[]}})#200 业务错
            try:#调用实现
                窄形=_一元路由(api,方法键,消息,信号)#派发
            except Exception as 错误:#实现崩溃
                return {'status':500,'headers':{},'body':f'handler failure: {错误}'.encode('utf-8')}#500
            return _成功响应(窄形)#200 业务结果
    return _处理器()#处理器实例
