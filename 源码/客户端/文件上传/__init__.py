'宿主文件上传服务：流式接入，以及会话持有的暂存回执'
import weakref#会话到暂存表，会话消失后表一起消失
from ...类型化远程调用.协议 import 远程,远程服务,远程错误#远程方法与远程失败
from uuid import uuid4#铸造凭证
from . import (
    http路由,#原始字节路由
    协议,#上传路径
    类型,#请求与回执类型
    异常,#本包没有异常类
    客户端,#浏览器上传，不在这里启动
)#同目录模块

__all__=['文件上传服务','http路由','协议','类型','异常','客户端']#包根只导出客户端这个模块，不转发里面的类

class 提示文件绑定守卫:
    '一条提示的凭证绑定。提交之后拆除不再恢复先前拥有者'
    def __init__(自身,回滚):
        '记下回滚'
        自身._回滚=回滚#未提交时恢复
        自身._已结算=False#提交或拆除之后为真

    def 提交(自身):
        '保持绑定，直到队列或历史观察退休这些凭证'
        自身._已结算=True#拆除时不再回滚

    def 拆除(自身):
        '未提交则恢复先前绑定。重复拆除无事'
        if 自身._已结算:#已经提交或拆除
            return#停
        自身._已结算=True#只回滚一次
        自身._回滚()#恢复

    def __enter__(自身):
        '进入 with，对应 using'
        return 自身#守卫

    def __exit__(自身,类型,值,回溯):
        '离开时拆除。异常继续向外抛'
        自身.拆除()#未提交则回滚
        return False#不吞异常

class 文件上传服务(远程服务):
    '按接收智能体的会话持有上传存储和暂存回执'
    inject=['agents','attachments','commands','connection']#智能体、附件、命令、连接
    def __init__(自身,上下文,配置=None):
        '登记 fileUploads，并挂上命令解析、流式路由和会话观察'
        super().__init__(上下文,'fileUploads')#远程服务名
        自身._暂存=weakref.WeakKeyDictionary()#会话到凭证表
        自身._智能体解析器=None#冷会话解析器
        def 解析凭证(智能体,凭证标识):
            '命令提交时解析暂存凭证'
            return 自身.解析(智能体,凭证标识)#本服务解析
        def 登记命令解析器():
            '挂到命令服务，返回拆除器'
            return 上下文.commands.登记文件回执解析器(解析凭证)#唯一解析器
        上下文.副作用(登记命令解析器,'file-upload: command file receipt resolver')#随纤程拆除
        def 登记流式路由():
            '挂到连接的流式上传路由'
            def 处理请求(请求):
                '把这一次请求交给路由'
                return http路由.处理文件上传http(自身,请求)#校验并暂存
            return 上下文.connection.fetch.register({#登记
                'path':协议.文件上传路径,#路径
                'methods':['POST'],#方法
                'requestBody':'streaming',#不在路由里聚合成一段
                'fetch':处理请求,#处理函数
            })#登记结束
        上下文.副作用(登记流式路由,'file-upload: streaming route')#随纤程拆除
        def 观察事件(会话,事件):
            '用户消息带字符串 rpcId 时退休对应凭证'
            if 事件['type']!='user/message':#不是用户消息
                return#忽略
            源=事件['data']['source']#来源
            if 源['kind']!='user' or 'rpcId' not in 源:#不是带 rpc 的用户来源
                return#忽略
            if isinstance(源['rpcId'],str):#字符串 rpc
                自身._退休(会话,源['rpcId'])#按这次提示退休
        def 会话拆除(会话):
            '会话拆除时丢掉它的暂存表'
            自身._暂存.pop(会话,None)#没有表也不报错
        上下文.监听('session/event',观察事件)#观察用户消息
        上下文.监听('session/disposed',会话拆除)#会话拆除

    def 登记智能体解析器(自身,解析器):
        '登记冷会话用的普通智能体解析器。返回只卸这一次的拆除器'
        if 自身._智能体解析器 is not None:#已经有一个
            raise RuntimeError('file-upload: Agent resolver is already registered')#拒绝第二个
        自身._智能体解析器=解析器#记下
        def 拆除():
            '只卸这一次登记的解析器'
            if 自身._智能体解析器 is 解析器:#仍是这一次
                自身._智能体解析器=None#清空
        return 拆除#拆除器

    @远程('upload')
    def 上传(自身,智能体,请求,信号=None):
        '持久化一次编码上传，并暂存在远程选定的智能体下'
        if 信号 is not None:#有取消信号
            抛出=getattr(信号,'throwIfAborted',None)#浏览器取消
            if callable(抛出):#有抛出方法
                抛出()#已取消则抛
            elif getattr(信号,'aborted',None) is True:#已置位但没有抛出方法
                中止=RuntimeError('The operation was aborted.')#与 DOMException 同一句
                中止.name='AbortError'#调用方按这个名字识别
                raise 中止#中止
        参数={'data':请求['data']}#规范 base64
        if 'name' in 请求 and 请求['name'] is not None:#有显示名
            参数['name']=请求['name']#写入
        def 存盘():
            '准入这一份编码文件'
            结果=自身.ctx.attachments.准入编码文件(参数)#解码并耐久提交
            if hasattr(结果,'等待'):#期约
                结果=结果.等待()#落到引用
            return 结果#文件引用
        return 自身._提交(智能体,存盘)#暂存

    def 流式上传(自身,请求):
        '为一个会话持久化原始分片，不把上传拼成一整段'
        会话标识=请求['sessionId']#会话
        存活=自身.ctx.agents.获取(会话标识)#在线智能体
        if 存活 is not None:#已经在线
            智能体=存活#直接用
        else:#冷会话
            解析器=自身._智能体解析器#登记过的解析器
            if 解析器 is None:#没有解析器
                raise 远程错误('session/not-found','session "'+str(会话标识)+'" is not attached',{'sessionId':会话标识})#未附着
            智能体=解析器(会话标识)#恢复
            if hasattr(智能体,'等待'):#期约
                智能体=智能体.等待()#落到智能体
        参数={'data':请求['data']}#分片，不在这里拼接
        if 'signal' in 请求 and 请求['signal'] is not None:#有取消
            参数['signal']=请求['signal']#交给存储
        if 'name' in 请求 and 请求['name'] is not None:#有显示名
            参数['name']=请求['name']#写入
        def 存盘():
            '把原始分片交给附件存储'
            结果=自身.ctx.attachments.保存文件流(参数)#流式存盘
            if hasattr(结果,'等待'):#期约
                结果=结果.等待()#落到引用
            return 结果#文件引用
        return 自身._提交(智能体,存盘)#暂存

    def 解析(自身,智能体,凭证标识):
        '在接收智能体的会话里解析一条暂存凭证。未知或别的会话返回 None'
        表=自身._暂存.get(智能体.session)#本会话的表
        if 表 is None:#没有表
            return None#未知
        项=表.get(凭证标识)#这一条
        if 项 is None:#没有
            return None#未知
        return 项['file']#持久引用

    def 绑定提示(自身,智能体,凭证标识列表,请求标识):
        '一条提示进入收件箱时绑定凭证。未提交就拆除时恢复先前拥有者'
        表=自身._暂存.get(智能体.session)#本会话的表
        已绑=[]#先前绑定
        for 凭证标识 in 凭证标识列表:#逐条
            上传项=None if 表 is None else 表.get(凭证标识)#暂存项
            if 上传项 is None:#没有暂存
                raise 远程错误('session/attachment-invalid','File was not uploaded for this session.',{'reason':'FILE_NOT_STAGED'})#未上传
            先前=上传项['requestId'] if 'requestId' in 上传项 else None#先前拥有者
            已绑.append({'upload':上传项,'previous':先前})#记下
        for 项 in 已绑:#全部都在才写入
            项['upload']['requestId']=请求标识#绑到这次提示
        def 回滚():
            '恢复写入之前的拥有者'
            for 项 in 已绑:#逐条
                上传项=项['upload']#暂存项
                先前=项['previous']#先前标识
                if 先前 is None:#先前没有绑定
                    上传项.pop('requestId',None)#去掉
                else:#有先前拥有者
                    上传项['requestId']=先前#恢复
        return 提示文件绑定守卫(回滚)#交给调用方提交或拆除

    def 退休提示(自身,智能体,请求标识):
        '退休被一条已移除队列接受的全部凭证'
        自身._退休(智能体.session,请求标识)#按提示标识

    def _提交(自身,智能体,存盘):
        '存盘成功后铸造凭证。子会话拒绝。存盘期间会话拆掉则拒绝'
        头=智能体.session.header#会话头
        if ('origin' in 头 and 头['origin']=='subagent'):#子会话
            raise 远程错误('subagent/attachment-invalid','subagent conversations do not accept file uploads',{'reason':'SUBAGENT_FILE_UNSUPPORTED'})#不接受上传
        try:#存盘失败映射成远程错误
            文件=存盘()#执行存盘
        except Exception as 错误:#附件或内部失败
            if 自身.ctx.attachments.是否附件错误(错误):#附件失败
                说明=错误.message if isinstance(getattr(错误,'message',None),str) else str(错误)#说明
                raise 远程错误('session/attachment-invalid',说明,{'reason':错误.code})#带原因码
            raise 远程错误('gateway/internal','failed to store file upload: '+str(错误),{},错误)#内部失败
        if 自身.ctx.agents.获取(智能体.id) is not 智能体:#存盘期间已经拆掉
            raise 远程错误('session/not-found','session "'+str(智能体.id)+'" was disposed before its file upload completed',{'sessionId':智能体.id})#会话不在了
        表=自身._暂存.get(智能体.session)#本会话的表
        if 表 is None:#还没有
            表={}#新建
            自身._暂存[智能体.session]=表#挂上会话
        凭证标识=str(uuid4())#这一次上传的凭证
        表[凭证标识]={'file':文件}#先不绑定提示
        return {'receiptId':凭证标识,'file':文件}#回执

    def _退休(自身,会话,请求标识):
        '删掉绑在这个提示上的凭证。表空了就卸下会话'
        表=自身._暂存.get(会话)#本会话的表
        if 表 is None:#没有表
            return#停
        待删=[]#先收集，避免边遍历边删
        for 凭证标识,上传项 in 表.items():#逐条
            if 上传项.get('requestId')==请求标识:#这一次提示
                待删.append(凭证标识)#记下
        for 凭证标识 in 待删:#再删
            表.pop(凭证标识,None)#去掉
        if len(表)==0:#没有剩余
            自身._暂存.pop(会话,None)#卸下会话

default=文件上传服务#类插件
