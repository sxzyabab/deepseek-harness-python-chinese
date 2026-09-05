"""Host 文件上传服务：流式接收与按 Agent 作用域的暂存凭证。

对齐上游 `@deepseek-ai/dsh-client-file-upload` 的 `src/index.ts`。
公开面仅中文名。Cordis 服务键与依赖槽保持上游英文字面量。
"""
import weakref#会话 → 暂存表
from ...内核.作用域 import 获取作用域#作用域标签
from ...工具.加密 import 随机uuid#铸造凭证
from ...typert.协议 import 远程,远程服务#Remote 装饰与服务基类
from ...附件.附件 import 若已中止则抛出,解开#取消与可等待解开
from .http路由 import 处理文件上传http#HTTP 路由处理
from .协议 import 文件上传路径,FILE_UPLOAD_PATH#上传路径
from .类型 import (#类型再导出
    文件上传凭证标识,#凭证品牌
    远程错误,#Remote 错误
    取远程错误,#结构识别
    编码文件上传请求字段,#请求字段
    文件上传结果字段,#结果字段
    文件附件引用字段,#文件引用字段
)#类型导入结束

__all__=[#仅中文公开名
    '提示文件绑定',
    '提示文件绑定守卫',
    '文件上传服务',
    '文件上传路径',
    'FILE_UPLOAD_PATH',
    '文件上传凭证标识',
    '远程错误',
    '取远程错误',
    '编码文件上传请求字段',
    '文件上传结果字段',
    '文件附件引用字段',
    '处理文件上传http',
    '默认',
    '名称',
    '注入',
    '应用',
    'apply',
    'FileUploads',
]#公开面结束

名称='file-upload'#Cordis 插件名
注入=['agents','attachments','commands','connection']#硬依赖

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#值
        return 缺省#缺席
    return getattr(对象,键,缺省)#属性

class 提示文件绑定守卫:#绑定守卫
    """Prompt 凭证绑定：除非投递提交，否则释放时恢复先前拥有者。"""
    def __init__(自身,回滚):#记下回滚
        """登记回滚闭包。"""
        自身._回滚=回滚#回滚
        自身._已结算=False#是否已结算

    def 提交(自身):#提交绑定
        """保持凭证绑定，直至队列或历史观察退休它们。"""
        自身._已结算=True#标记已结算

    def commit(自身):#上游名
        """提交绑定。"""
        自身.提交()#转发

    def 释放(自身):#释放
        """未提交则回滚先前绑定。"""
        if 自身._已结算:#已提交则不回滚
            return#停
        自身._已结算=True#标记已结算
        自身._回滚()#恢复先前绑定

    def __enter__(自身):#进入 with
        """返回自身。"""
        return 自身#守卫

    def __exit__(自身,类型,值,回溯):#离开 with
        """对齐 Symbol.dispose。"""
        自身.释放()#释放
        return False#不吞异常

提示文件绑定=提示文件绑定守卫#协议别名

class 文件上传服务(远程服务):#Host 文件上传服务
    """拥有上传存储与按 Agent 作用域暂存凭证的 Host 服务。"""
    inject=注入#硬依赖
    def __init__(自身,上下文):#构造服务
        """携带 Agent、附件、命令与 Connection 服务的 Host 上下文。"""
        super().__init__(上下文,'fileUploads')#登记 Remote 服务名
        自身._暂存=weakref.WeakKeyDictionary()#会话 → 暂存表
        自身._智能体解析器=None#冷会话解析器
        def 解析凭证(智能体,凭证标识):#命令凭证解析
            """转交 resolve。"""
            return 自身.解析(智能体,凭证标识)#解析
        上下文.effect(#登记命令解析器
            lambda:上下文.commands.registerFileReceiptResolver(解析凭证),#登记
            'file-upload: command file receipt resolver',#effect 名
        )#结束 commands effect
        def 登记流式路由():#登记流式路由
            """挂到 connection.fetch。"""
            return 上下文.connection.fetch.register({#登记
                'path':文件上传路径,#路径
                'methods':['POST'],#方法
                'requestBody':'streaming',#流式正文
                'fetch':lambda 请求:处理文件上传http(自身,请求),#处理函数
            })#结束 register
        上下文.effect(登记流式路由,'file-upload: streaming route')#connection effect
        上下文.on('session/event',lambda 会话,事件:自身._观察会话事件(会话,事件))#观察会话事件
        上下文.on('session/disposed',lambda 会话:自身._暂存.pop(会话,None))#会话拆除清表

    def 登记智能体解析器(自身,解析器):#登记 Agent 解析器
        """登记原始上传寻址冷 Session 时用的普通 Session 解析器。"""
        if 自身._智能体解析器 is not None:#只许一个
            raise Exception('file-upload: Agent resolver is already registered')#拒绝
        自身._智能体解析器=解析器#记下
        def 拆除():#卸本实例
            """仅卸本解析器。"""
            if 自身._智能体解析器 is 解析器:#仍是本实例
                自身._智能体解析器=None#清空
        return 拆除#disposer

    registerAgentResolver=登记智能体解析器#上游名

    @远程('upload')
    def 上传(自身,智能体,请求,信号=None):#编码上传
        """持久化一次编码上传，并按 Typert 选定的 Agent 接收方暂存。"""
        若已中止则抛出(信号)#已取消则抛
        参数={'data':取字段(请求,'data')}#base64 数据
        名=取字段(请求,'name')#可选名
        if 名 is not None:#有名
            参数['name']=名#写入
        return 自身._提交(智能体,lambda:解开(自身.ctx.attachments.admitEncodedFile(参数)))#准入编码文件

    upload=上传#上游名

    def 流式上传(自身,请求):#流式上传
        """为一个 Session 持久化原始分片，不聚合整次上传。"""
        智能体=自身._解析智能体(取字段(请求,'sessionId'))#解析接收 Agent
        参数={'data':取字段(请求,'data')}#字节流
        信号=取字段(请求,'signal')#可选取消
        if 信号 is not None:#有信号
            参数['signal']=信号#写入
        名=取字段(请求,'name')#可选名
        if 名 is not None:#有名
            参数['name']=名#写入
        return 自身._提交(智能体,lambda:解开(自身.ctx.attachments.saveFileStream(参数)))#流式存盘

    uploadStream=流式上传#上游名

    def 解析(自身,智能体,凭证标识):#解析凭证
        """在其接收 Agent 作用域内解析一条暂存凭证。"""
        自身._断言智能体作用域(智能体)#必须在 Agent 自身作用域
        表=自身._暂存.get(智能体.session)#本会话暂存表
        if 表 is None:#无表
            return None#未知
        项=表.get(凭证标识)#暂存项
        if 项 is None:#无
            return None#未知
        return 取字段(项,'file')#持久文件引用

    resolve=解析#上游名

    def 绑定提示(自身,智能体,凭证标识们,请求标识):#绑定 prompt 凭证
        """在一条 prompt 进入 Agent 收件箱时绑定凭证。"""
        自身._断言智能体作用域(智能体)#必须在 Agent 自身作用域
        表=自身._暂存.get(智能体.session)#本会话暂存表
        已绑=[]#先前绑定记录
        for 凭证标识 in 凭证标识们:#逐凭证
            上传项=None if 表 is None else 表.get(凭证标识)#取暂存项
            if 上传项 is None:#未暂存
                raise 文件未暂存()#抛错
            已绑.append({'upload':上传项,'previous':上传项.get('requestId') if isinstance(上传项,dict) else getattr(上传项,'requestId',None)})#记下先前
        for 项 in 已绑:#写入新绑定
            上传项=项['upload']#暂存项
            if isinstance(上传项,dict):#映射
                上传项['requestId']=请求标识#写入
            else:#对象
                上传项.requestId=请求标识#写入
        def 回滚():#回滚守卫
            """恢复先前绑定。"""
            for 项 in 已绑:#逐项恢复
                上传项=项['upload']#暂存项
                先前=项['previous']#先前 requestId
                if isinstance(上传项,dict):#映射
                    if 先前 is None:#先前无绑定
                        上传项.pop('requestId',None)#删除
                    else:#有
                        上传项['requestId']=先前#恢复
                else:#对象
                    if 先前 is None:#先前无绑定
                        if hasattr(上传项,'requestId'):#有属性
                            delattr(上传项,'requestId')#删除
                    else:#有
                        上传项.requestId=先前#恢复
        return 提示文件绑定守卫(回滚)#回滚守卫

    bindPrompt=绑定提示#上游名

    def 退休提示(自身,智能体,请求标识):#退休 prompt 凭证
        """退休被一条已移除队列出现接受的全部凭证。"""
        自身._断言智能体作用域(智能体)#必须在 Agent 自身作用域
        自身._退休(智能体.session,请求标识)#按请求 id 退休

    retirePrompt=退休提示#上游名

    def _提交(自身,智能体,存盘):#存盘并暂存
        """执行存盘并铸造凭证。"""
        自身._断言普通智能体(智能体)#普通 Agent 才接受上传
        try:#存盘
            文件=存盘()#执行存盘
        except BaseException as 错误:#存盘失败
            是否附件=getattr(自身.ctx.attachments,'isAttachmentError',None)#附件域判定
            if callable(是否附件) and 是否附件(错误):#附件域错误
                raise 远程错误('session/attachment-invalid',str(错误),{'reason':getattr(错误,'code',None)})#映射 Remote
            raise 远程错误(#内部错误
                'gateway/internal',#内部错误
                'failed to store file upload: '+str(错误),#消息
                {},#空细节
                {'cause':错误},#因果
            )#结束 RemoteError
        if 自身.ctx.agents.get(智能体.id) is not 智能体:#存盘期间 Agent 已拆除
            raise 远程错误(#会话不存在
                'session/not-found',#码
                'session "'+str(智能体.id)+'" was disposed before its file upload completed',#消息
                {'sessionId':智能体.id},#细节
            )#结束 RemoteError
        表=自身._暂存.get(智能体.session)#取或建暂存表
        if 表 is None:#尚无表
            表={}#新建
            自身._暂存[智能体.session]=表#挂上会话
        凭证标识=文件上传凭证标识(随机uuid())#铸造凭证
        表[凭证标识]={'file':文件}#写入暂存
        return {'receiptId':凭证标识,'file':文件}#返回结果

    def _解析智能体(自身,会话标识):#解析接收 Agent
        """存活或冷解析。"""
        存活=自身.ctx.agents.get(会话标识)#存活 Agent
        if 存活 is not None:#直接返回
            return 存活#存活
        解析器=自身._智能体解析器#冷解析器
        if 解析器 is None:#未登记
            raise 远程错误('session/not-found','session "'+str(会话标识)+'" is not attached',{'sessionId':会话标识})#未附着
        return 解析器(会话标识)#恢复或解析

    def _断言智能体作用域(自身,智能体):#断言 Agent 自身作用域
        """必须在 Agent 自身作用域。"""
        if 获取作用域(智能体.ctx) is not 智能体:#作用域不对
            raise Exception("file-upload: operation requires the Agent's own scope")#拒绝

    def _断言普通智能体(自身,智能体):#断言普通 Agent
        """子智能体不接受文件上传。"""
        自身._断言智能体作用域(智能体)#先查作用域
        头=取字段(取字段(智能体.session,'header'),'origin')#来源
        if 头=='subagent':#子智能体
            raise 远程错误(#子智能体附件非法
                'subagent/attachment-invalid',#码
                'subagent conversations do not accept file uploads',#消息
                {'reason':'SUBAGENT_FILE_UNSUPPORTED'},#原因
            )#结束 RemoteError

    def _观察会话事件(自身,会话,事件):#观察会话事件
        """用户消息带 rpcId 则退休凭证。"""
        if 取字段(事件,'type')!='user/message':#非用户消息
            return#忽略
        源=取字段(取字段(事件,'data'),'source')#来源
        if 取字段(源,'kind')!='user':#非用户
            return#忽略
        if isinstance(源,dict):#映射形
            if 'rpcId' not in 源:#无 rpcId
                return#忽略
            rpc标识=源['rpcId']#取出
        elif 源 is not None and hasattr(源,'rpcId'):#对象形
            rpc标识=源.rpcId#取出
        else:#无
            return#忽略
        if isinstance(rpc标识,str):#有字符串 rpcId
            自身._退休(会话,rpc标识)#按 rpcId 退休

    def _退休(自身,会话,请求标识):#按请求 id 退休凭证
        """匹配 requestId 的凭证删除。"""
        表=自身._暂存.get(会话)#暂存表
        if 表 is None:#无表
            return#停
        待删=[]#待删键
        for 凭证标识,上传项 in list(表.items()):#逐项
            绑定=上传项.get('requestId') if isinstance(上传项,dict) else getattr(上传项,'requestId',None)#绑定 id
            if 绑定==请求标识:#匹配
                待删.append(凭证标识)#记下
        for 凭证标识 in 待删:#删除
            表.pop(凭证标识,None)#删
        if len(表)==0:#空表
            自身._暂存.pop(会话,None)#卸下

def 文件未暂存():#未暂存错误
    """File was not uploaded for this session."""
    return 远程错误(#未暂存
        'session/attachment-invalid',#附件非法
        'File was not uploaded for this session.',#消息
        {'reason':'FILE_NOT_STAGED'},#原因
    )#结束 RemoteError

def 应用(上下文,配置=None):#安装 Host 插件
    """挂载文件上传 Host 服务。"""
    文件上传服务(上下文)#构造并登记
    return None#无额外拆除

apply=应用#Cordis 插件入口
默认=文件上传服务#默认导出
FileUploads=文件上传服务#上游名
