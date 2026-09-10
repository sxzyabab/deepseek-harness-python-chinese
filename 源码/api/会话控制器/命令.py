"""会话命令：各 Remote 方法上的显式激活策略。

对齐上游 `session-controller/src/commands.ts`。公开面仅中文名。
"""
import base64#附件字节
import uuid#新会话 id
from ...工具.时间 import 规范化客户端时区#客户端时区
from ...模型后端.llm import 创建用户消息,冻结消息,助手流块列表#消息与流
from ...附件.附件 import 附件错误#附件失败
from ...附件.附件.准入 import 准入编码图像批次#图像准入
from .远程错误与并发 import 远程错误,远程错误消息#远程错误
from .智能体 import (#智能体面
    会话未找到,子智能体所有权错误,有子智能体所有者,cwd冲突,预设冲突,子智能体会话所有权,检视会话,
)#智能体导入结束

__all__=['会话命令控制器']#仅中文公开名

def _活智能体(上下文,会话标识):
    """取在线智能体：兼容英文 get 与中文 获取。"""
    取=getattr(上下文.agents,'get',None)#英文
    if 取 is not None:#有英文
        return 取(会话标识)#取
    return 上下文.agents.获取(会话标识)#中文

def _有提示内容(内容):
    """是否含非空白文本或附件块。内容为 list。"""
    if not isinstance(内容,list):#非列表
        return False#空
    for 块 in 内容:#逐块
        if not isinstance(块,dict):#非对象
            continue#跳过
        种类=块['type'] if 'type' in 块 else None#块类型
        if 种类!='text':#非文本即附件等
            return True#有内容
        文本=块['text'] if 'text' in 块 else ''#文本
        if isinstance(文本,str) and len(文本.strip())>0:#非空白
            return True#有内容
    return False#全空

def _提供方已服务(上下文,提供方):
    """提供方是否有适配器。"""
    for 条目 in 上下文.llm.列出提供方():#逐提供方
        if 条目['id']==提供方:#命中
            return True#有
    return False#无

def _解析提示文件回执(内容,解析暂存):
    """把 file 块上的 receiptId 换成持久文件引用。返回 content 与 receiptIds。"""
    回执集合=set()#回执
    已解析=[]#块
    for 块 in 内容:#逐块
        if not isinstance(块,dict) or 块.get('type')!='file':#非文件
            已解析.append(块)#原样
            continue#下一块
        回执=块['receiptId'] if 'receiptId' in 块 else None#凭证
        附件=解析暂存(回执)#解析
        if 附件 is None:#未暂存
            raise 远程错误(
                'session/attachment-invalid',
                'File was not uploaded for this session.',
                {'reason':'FILE_NOT_STAGED'},
            )#拒绝
        回执集合.add(回执)#记下
        已解析.append({'type':'file','attachment':附件})#替换
    return {'content':已解析,'receiptIds':list(回执集合)}#结果

def _准入提示内容(附件服务,内容):
    """对齐 attachments.admitPromptContent：无图直通，有图则批次准入。"""
    if all((not isinstance(块,dict)) or 块.get('type')!='image' for 块 in 内容):#无图
        结果=[]#块
        for 块 in 内容:#逐块
            if isinstance(块,dict) and 块.get('type')=='text':#文本
                结果.append({'type':'text','text':块['text']})#文本
            elif isinstance(块,dict) and 块.get('type')=='file':#文件
                结果.append({'type':'file','attachment':块['attachment']})#文件
            else:#其它
                结果.append(块)#原样
        return 结果#直通
    图像列表=[块 for 块 in 内容 if isinstance(块,dict) and 块.get('type')=='image']#图像块
    引用列表=准入编码图像批次(附件服务,图像列表)#准入
    游标=0#引用下标
    结果=[]#重组
    for 块 in 内容:#原序
        if isinstance(块,dict) and 块.get('type')=='text':#文本
            结果.append({'type':'text','text':块['text']})#文本
        elif isinstance(块,dict) and 块.get('type')=='file':#文件
            结果.append({'type':'file','attachment':块['attachment']})#文件
        elif isinstance(块,dict) and 块.get('type')=='image':#图像
            结果.append({'type':'image','attachment':引用列表[游标]})#引用
            游标+=1#前进
        else:#其它
            结果.append(块)#原样
    return 结果#已准入

def _有同请求提示(智能体,请求标识):
    """收件箱或日志是否已有同 rpcId 的用户消息。"""
    def 匹配(消息):
        """是否同请求。"""
        源=消息['source'] if isinstance(消息,dict) and 'source' in 消息 else None#来源
        return isinstance(源,dict) and 源.get('kind')=='user' and 源.get('rpcId')==请求标识#匹配
    if any(匹配(消息) for 消息 in 智能体.inbox.下一轮队列):#下一轮
        return True#有
    if any(匹配(消息) for 消息 in 智能体.inbox.下一步队列):#下一步
        return True#有
    for 事件 in 智能体.session.snapshotEvents():#日志
        if 事件['type']!='user/message':#非用户
            continue#跳过
        源=事件['data']['source'] if 'data' in 事件 and isinstance(事件['data'],dict) and 'source' in 事件['data'] else None#来源
        if isinstance(源,dict) and 源.get('kind')=='user' and 源.get('rpcId')==请求标识:#匹配
            return True#有
    return False#无

def _内容块中的图(内容,谓词):
    """在内容块树中找匹配的图像引用。"""
    if not isinstance(内容,list):#非列表
        return None#无
    for 值 in 内容:#逐块
        if not isinstance(值,dict):#非对象
            continue#跳过
        if 值.get('type')=='image' and isinstance(值.get('attachment'),dict):#图像
            引用=值['attachment']#引用
            if 谓词(引用):#命中
                return 引用#返回
        if 值.get('type')=='tool-result':#工具结果
            嵌套=_内容块中的图(值['content'] if 'content' in 值 else None,谓词)#嵌套
            if 嵌套 is not None:#命中
                return 嵌套#返回
    return None#无

def _事件中的图(事件,谓词):
    """在会话事件载荷中找图像引用。"""
    数据=事件['data'] if 'data' in 事件 and isinstance(事件['data'],dict) else {}#载荷
    直接=_内容块中的图(数据['content'] if 'content' in 数据 else None,谓词)#直接
    if 直接 is not None:#命中
        return 直接#返回
    消息=数据['message'] if 'message' in 数据 and isinstance(数据['message'],dict) else None#消息
    if 消息 is not None:#有消息
        找到=_内容块中的图(消息['content'] if 'content' in 消息 else None,谓词)#消息内容
        if 找到 is not None:#命中
            return 找到#返回
    for 插入 in (数据['inserted'] if 'inserted' in 数据 and isinstance(数据['inserted'],list) else []):#插入
        if not isinstance(插入,dict):#非对象
            continue#跳过
        找到=_内容块中的图(插入['content'] if 'content' in 插入 else None,谓词)#插入内容
        if 找到 is not None:#命中
            return 找到#返回
    if 事件['type'] in ('assistant/message','assistant/attempt'):#助手流
        流=数据['stream'] if 'stream' in 数据 else []#流
        for 块 in 助手流块列表(流,'block-end'):#块结束
            找到=_内容块中的图([块],谓词) if not isinstance(块,dict) or 'block' not in 块 else _内容块中的图([块['block']],谓词)#块
            if 找到 is not None:#命中
                return 找到#返回
    return None#无

def _引用图像(事件列表,附件标识):
    """按附件 id 在事件前缀中找图像引用。"""
    def 谓词(引用):
        """匹配 attachmentId。"""
        return str(引用['attachmentId'] if 'attachmentId' in 引用 else '')==str(附件标识)#比较
    for 事件 in 事件列表:#逐事件
        找到=_事件中的图(事件,谓词)#查找
        if 找到 is not None:#命中
            return 找到#返回
    return None#无

def _自有序号(会话,序号):
    """对齐 Session.isOwnSeq：落在继承切口与下一 seq 之间。"""
    return 序号>=getattr(会话,'inheritedEventCount',0) and 序号<会话.seq#区间

class 会话命令控制器:
    """实现会话控制器委托的业务命令。"""

    def __init__(自身,上下文,智能体控制器,默认cwd):
        """保存依赖。"""
        自身._上下文=上下文#Cordis
        自身._智能体控制器=智能体控制器#智能体控制器
        自身._默认cwd=默认cwd#默认 cwd

    def create(自身,请求):
        """创建或幂等采用普通会话。请求为 dict。"""
        if ('workspaceId' in 请求 and 请求['workspaceId'] is not None) and ('cwd' in 请求 and 请求['cwd'] is not None):#互斥
            raise 远程错误('gateway/bad-request','session.create accepts workspaceId or cwd, not both',{})#拒绝
        会话标识=请求['sessionId'] if 'sessionId' in 请求 and 请求['sessionId'] is not None else ('session-'+str(uuid.uuid4()))#id
        工作区=None#工作区
        if 'workspaceId' in 请求 and 请求['workspaceId'] is not None:#按工作区
            工作区=自身._上下文.workspaceRegistry.get(请求['workspaceId'])#查找
            if 工作区 is None:#未找到
                raise 远程错误('workspace/not-found','workspace "'+str(请求['workspaceId'])+'" not found',{'workspaceId':请求['workspaceId']})#拒绝
        if 工作区 is not None:#工作区路径
            工作目录=工作区.path#cwd
        else:#请求或默认
            工作目录=请求['cwd'] if 'cwd' in 请求 and 请求['cwd'] is not None else 自身._默认cwd#cwd
        try:
            采用=自身._智能体控制器.确保会话(会话标识,工作目录,'sessionId' in 请求 and 请求['sessionId'] is not None,请求['agentPreset'] if 'agentPreset' in 请求 else None)#采用
        except BaseException as 错误:
            自身._拒绝创建(会话标识,错误)#抛出
        if 工作区 is not None:#附着工作区
            try:
                工作区.attachSession(会话标识)#attach
            except (OSError,ValueError,TypeError) as 错误:
                raise 远程错误('session/workspace-attach-failed','session "'+str(会话标识)+'" was created but could not attach to workspace "'+str(工作区.id)+'": '+远程错误消息(错误),{'sessionId':会话标识,'workspaceId':工作区.id},原因=错误)#失败
        预设=自身._智能体控制器.会话预设(采用.session)#预设
        结果={'sessionId':会话标识}#结果
        if 预设 is not None:#有预设
            结果['agentPreset']=预设#写入
        return 结果#结果

    def selectModel(自身,请求):
        """校验并安装会话本地模型选择。请求为 dict。"""
        智能体=自身._解析智能体(请求['sessionId'])#解析
        def 准入():
            """串行区内安装选择。"""
            try:
                调用={'provider':请求['provider'],'model':请求['model']}#解析调用
                if 'reasoningEffort' in 请求 and 请求['reasoningEffort'] is not None:#有推理
                    调用['reasoningEffort']=请求['reasoningEffort']#推理
                解析=自身._上下文.llm.resolveCallConfig(调用)#resolve 为 dict
                已选={'provider':解析['provider'],'model':解析['model']}#选择
                if 'reasoningEffort' in 解析 and 解析['reasoningEffort'] is not None:#有推理
                    已选['reasoningEffort']=解析['reasoningEffort']#推理
                自身._智能体控制器.选择下次请求(智能体,已选)#安装
                try:
                    自身._上下文.agentDefaultModel.saveSelection(已选)#保存
                except (OSError,ValueError,TypeError) as 警告:
                    自身._上下文.日志.警告('session-controller: default model not saved: '+str(警告))#日志
                return {'selected':dict(已选)}#返回
            except 远程错误:
                raise#原样
            except (OSError,ValueError,TypeError,KeyError,AttributeError) as 错误:
                raise 远程错误('session/model-unavailable',远程错误消息(错误),{'provider':请求['provider'],'model':请求['model']},原因=错误)#映射
        return 自身._智能体控制器.串行图像准入(智能体,准入)#串行

    def rename(自身,请求):
        """追加用户拥有的会话标题。请求为 dict。"""
        智能体=自身._解析智能体(请求['sessionId'])#解析
        标题服务=自身._上下文.获取服务('sessionTitle')#标题服务
        if 标题服务 is None:#缺席
            raise 远程错误('gateway/internal','renaming is unavailable: this deployment mounts no session-title service',{})#拒绝
        try:
            接受=标题服务.rename(智能体.session,请求['title'])#改名，接受为 dict
            return {'title':接受['title'],'seq':接受['eventSeq']}#结果
        except 远程错误:
            raise#原样
        except BaseException as 错误:
            if getattr(错误,'name',None)=='SessionTitleInvalidError' or 错误.__class__.__name__=='SessionTitleInvalidError':#无效标题按结构识别
                raise 远程错误('session/title-invalid',str(错误),{'sessionId':请求['sessionId']})#映射
            raise 远程错误('gateway/internal','failed to rename session "'+str(请求['sessionId'])+'": '+远程错误消息(错误),{})#内部

    def fork(自身,请求):
        """从已完成回合前缀分叉新会话。请求为 dict。"""
        锚点=请求['atSeq'] if 'atSeq' in 请求 else None#可选锚点
        if 锚点 is not None:#有锚点
            if isinstance(锚点,bool) or (not isinstance(锚点,int)) or 锚点<0:#非法
                raise 远程错误('gateway/bad-request','atSeq must be a non-negative safe integer',{})#拒绝
        try:
            观测=自身._上下文.sessionQuery.observeSession(请求['sessionId'])#观测源
        except BaseException as 错误:
            if getattr(错误,'code',None)=='SESSION_QUERY_SESSION_NOT_FOUND':#未找到
                raise 远程错误('session/not-found','session "'+str(请求['sessionId'])+'" not found',{'sessionId':请求['sessionId']})#映射
            raise 远程错误('gateway/internal','fork source unavailable for session "'+str(请求['sessionId'])+'": '+远程错误消息(错误),{})#内部
        try:
            事件列表=list(观测.events if 观测.events is not None else [])#事件前缀
            头=观测.header#头
            末序号=事件列表[-1]['seq'] if len(事件列表)>0 else -1#末序号
            边界=None#turn/end
            if 锚点 is not None:#锚定
                for 事件 in 事件列表:#找锚点边界
                    if 事件['type']=='turn/end' and 事件['seq']>=锚点:#命中
                        边界=事件#记下
                        break#停
            if 边界 is None and (锚点 is None or 锚点>末序号):#回退最近完成回合
                for 事件 in reversed(事件列表):#自后向前
                    if 事件['type']=='turn/end':#命中
                        边界=事件#记下
                        break#停
            if 边界 is None:#不可分叉
                if 锚点 is not None and 锚点<=末序号:#锚在日志内但回合未完成
                    文案='session "'+str(请求['sessionId'])+'" has not completed the turn containing event '+str(锚点)#文案
                else:#无完成回合
                    文案='session "'+str(请求['sessionId'])+'" has no completed turn to fork from'#文案
                raise 远程错误('session/fork-unavailable',文案,{'sessionId':请求['sessionId']})#拒绝
            切开=边界['seq']+1#切开点
            while 切开<len(事件列表) and 事件列表[切开]['type']!='turn/start':#推到下一回合开始
                切开+=1#前进
            try:
                工作区=自身._分叉工作区(头)#解析工作区
            except BaseException as 错误:
                raise 远程错误('gateway/internal','failed to resolve fork workspace for session "'+str(请求['sessionId'])+'": '+远程错误消息(错误),{})#内部
            子标识='session-'+str(uuid.uuid4())#子会话 id
            组合=自身._智能体控制器.组合智能体(自身._智能体控制器._观测预设(观测))#组装
            try:
                默认=自身._上下文.agentDefaultModel.currentSelection()#默认模型
                元={}#元
                if 'cwd' in 头 and 头['cwd'] is not None:#继承 cwd
                    元['cwd']=头['cwd']#cwd
                元['parentSession']=头['id']#父
                元['isSeeded']=True#已播种
                if 'agentPreset' in 组合 and 组合['agentPreset'] is not None:#预设
                    元['agentPreset']=组合['agentPreset']#写入
                创建=getattr(自身._上下文.agents,'create',None) or 自身._上下文.agents.创建#创建入口
                创建({
                    'sessionId':子标识,
                    'seed':事件列表[:切开],
                    'inheritedEventCount':切开,
                    'meta':元,
                    'agentOptions':{'provider':默认['provider'],'model':默认['model']},
                    'setup':组合['setup'],
                })#创建子会话
            except BaseException as 错误:
                raise 远程错误('gateway/internal','failed to fork session "'+str(请求['sessionId'])+'": '+远程错误消息(错误),{})#内部
            if 工作区 is not None:#附着
                try:
                    工作区.attachSession(子标识)#附着
                except (OSError,ValueError,TypeError) as 错误:
                    raise 远程错误(
                        'session/workspace-attach-failed',
                        'session "'+str(子标识)+'" was forked but could not attach to workspace "'+str(工作区.id)+'": '+远程错误消息(错误),
                        {'sessionId':子标识,'workspaceId':工作区.id},
                        原因=错误,
                    )#失败
            return {'sessionId':子标识}#结果
        finally:
            if hasattr(观测,'close'):#可关
                观测.close()#关

    def prompt(自身,请求):
        """显式恢复后投入提示。请求为 dict。"""
        内容=请求['content'] if 'content' in 请求 else None#提示内容
        if not _有提示内容(内容):#空或仅空白
            raise 远程错误(
                'gateway/bad-request',
                'prompt content must include non-whitespace text or an attachment',
                {},
            )#拒绝
        客户端时区=None#时区
        if 'clientTimeZone' in 请求 and 请求['clientTimeZone'] is not None:#有时区
            客户端时区=规范化客户端时区(请求['clientTimeZone'])#规范化
            if 客户端时区 is None:#非法
                raise 远程错误(
                    'session/invalid-time-zone',
                    'clientTimeZone must be UTC or a valid IANA Area/Location name',
                    {'value':请求['clientTimeZone']},
                )#拒绝
        智能体=自身._解析智能体(请求['sessionId'])#解析
        if _有同请求提示(智能体,请求['requestId']):#幂等
            return {'accepted':True}#已接受
        选择=自身._智能体控制器.选择用于(智能体).current#当前选择
        if not _提供方已服务(自身._上下文,选择['provider']):#无适配器
            raise 远程错误(
                'session/model-unavailable',
                'no adapter serves provider "'+str(选择['provider'])+'"; select a model for this session',
                {'provider':选择['provider'],'model':选择['model']},
            )#拒绝
        来源={'kind':'user','rpcId':请求['requestId']}#来源
        if 客户端时区 is not None:#带时区
            来源['clientTimeZone']=客户端时区#写入
        有图=any(isinstance(块,dict) and 块.get('type')=='image' for 块 in 内容)#是否含图
        def 准入():
            """执行准入。"""
            try:
                if 有图:#校验模态
                    当前=自身._智能体控制器.选择用于(智能体).current#当前
                    模型=自身._上下文.llm.解析模型信息(当前['provider'],当前['model'])#模型信息
                    模态=模型['inputModalities'] if isinstance(模型,dict) and 'inputModalities' in 模型 else None#模态
                    if 模态 is not None and 'image' not in 模态:#不支持图
                        raise 远程错误(
                            'session/attachment-invalid',
                            'Model "'+str(当前['model'])+'" does not support image input.',
                            {'reason':'MODEL_DOES_NOT_SUPPORT_IMAGES'},
                        )#拒绝
                上传=自身._上下文.fileUploads#上传服务
                解析=_解析提示文件回执(内容,lambda 回执:上传.解析(智能体,回执))#解析回执
                已准入=_准入提示内容(自身._上下文.attachments,解析['content'])#准入内容
                消息=创建用户消息({'content':已准入,'source':来源})#用户消息
                现=_活智能体(自身._上下文,智能体.id)#再取
                if 现 is not 智能体:#准入期间拆除
                    raise 远程错误(
                        'session/not-found',
                        'session "'+str(智能体.id)+'" was disposed during prompt admission',
                        {'sessionId':智能体.id},
                    )#拒绝
                绑定=上传.绑定提示(智能体,解析['receiptIds'],请求['requestId'])#绑定
                try:
                    if 请求.get('mode')=='steer':#引导
                        智能体.转向(消息)#转向
                    else:#排队
                        智能体.后续(消息)#后续
                    绑定.提交()#提交绑定
                finally:
                    绑定.拆除()#未提交则回滚
            except 远程错误:
                raise#原样
            except 附件错误 as 错误:
                raise 远程错误('session/attachment-invalid',str(错误),{'reason':错误.code})#映射
            except BaseException as 错误:
                raise 远程错误('session/agent-busy','prompt rejected',{'reason':str(错误)})#忙碌
            return {'accepted':True}#确认
        if 有图:#有图串行
            return 自身._智能体控制器.串行图像准入(智能体,准入)#串行
        return 准入()#直接

    def attachment(自身,请求):
        """读取会话日志引用的图像。请求为 dict。"""
        try:
            源=自身._读会话状态(请求['sessionId'])#读取
        except 会话未找到 as 错误:
            raise 远程错误('session/not-found',str(错误),{'sessionId':请求['sessionId']})#映射
        except BaseException as 错误:
            raise 远程错误(
                'gateway/internal',
                'attachment authorization unavailable for session "'+str(请求['sessionId'])+'": '+远程错误消息(错误),
                {},
            )#内部
        引用=_引用图像(源['events'],str(请求['attachmentId']))#查找引用
        if 引用 is None:#未引用
            raise 远程错误(
                'session/attachment-invalid',
                'Image is not referenced by this session.',
                {'reason':'ATTACHMENT_NOT_REFERENCED'},
            )#拒绝
        try:
            已存=自身._上下文.attachments.读取图像(引用)#读取
            数据=已存['data'] if isinstance(已存,dict) and 'data' in 已存 else getattr(已存,'data',None)#字节
            引用出=已存['ref'] if isinstance(已存,dict) and 'ref' in 已存 else (已存['attachment'] if isinstance(已存,dict) and 'attachment' in 已存 else 引用)#引用
            if isinstance(数据,str):#已是文本
                编码=数据#原样
            else:#字节
                编码=base64.b64encode(bytes(数据)).decode('ascii')#base64
            return {'attachment':引用出,'data':编码}#结果
        except 附件错误 as 错误:
            raise 远程错误('session/attachment-invalid',str(错误),{'reason':错误.code})#映射
        except BaseException:
            raise 远程错误('gateway/internal','Unable to read image attachment.',{})#内部

    def updateQueue(自身,请求):
        """变更仍待处理的队列项。请求为 dict。"""
        动作=请求['action'] if 'action' in 请求 else None#动作
        if isinstance(动作,dict) and 动作.get('kind')=='edit':#编辑
            内容=动作['content'] if 'content' in 动作 else None#编辑内容
            if isinstance(内容,list) and any(isinstance(块,dict) and 块.get('type')!='text' for 块 in 内容):#含非文本
                raise 远程错误(
                    'session/attachment-invalid',
                    'queue edits accept text content only',
                    {'reason':'QUEUE_EDIT_NON_TEXT'},
                )#拒绝
            if not _有提示内容(内容):#空或仅空白
                raise 远程错误(
                    'gateway/bad-request',
                    'queue edit content must include non-whitespace text',
                    {},
                )#拒绝
        智能体=_活智能体(自身._上下文,请求['sessionId'])#仅活智能体
        if 智能体 is None:#不在线
            raise 远程错误('session/queue-item-not-found','queued item is no longer pending',{'itemId':请求['itemId'] if 'itemId' in 请求 else None})#拒绝
        if 有子智能体所有者(自身._上下文,智能体.session.header,智能体):#子智能体
            快照=自身._上下文.sessionProjections.snapshot(智能体.session,['subagent'])#快照
            身份=快照['values']['subagent'] if isinstance(快照,dict) and 'values' in 快照 and 'subagent' in 快照['values'] else None#身份
            if not isinstance(身份,dict) or 身份.get('mode')!='continuable' or not _自有序号(智能体.session,身份['seq']):#非可继续自有
                raise 子智能体所有权错误(请求['sessionId'])#拒绝
        定位=None#定位
        for 消息 in 智能体.inbox.下一轮队列:#下一轮
            if 消息['id']==请求['itemId']:#命中
                定位={'target':'next-turn','message':消息}#记下
                break#停
        if 定位 is None:#再找下一步
            for 消息 in 智能体.inbox.下一步队列:#下一步
                if 消息['id']==请求['itemId']:#命中
                    定位={'target':'next-step','message':消息}#记下
                    break#停
        if 定位 is None:#未找到
            raise 远程错误('session/queue-item-not-found','queued item is no longer pending',{'itemId':请求['itemId']})#拒绝
        目标=定位['target']#目标面
        消息=定位['message']#消息
        种类=动作['kind'] if isinstance(动作,dict) else None#动作种类
        if 种类=='steer' and (目标!='next-turn' or 智能体.状态!='running'):#不可引导
            raise 远程错误('session/steer-unavailable','current turn no longer accepts steering',{'itemId':请求['itemId']})#拒绝
        if 种类=='edit':#编辑文本
            新消息=冻结消息({**消息,'content':list(动作['content'])})#冻结
            智能体.inbox.替换(请求['itemId'],新消息)#替换
        elif 种类=='remove':#移除
            智能体.inbox.移除(请求['itemId'])#移除
            源=消息['source'] if isinstance(消息,dict) and 'source' in 消息 else None#来源
            if isinstance(源,dict) and 源.get('kind')=='user' and 'rpcId' in 源:#用户 rpc
                自身._上下文.fileUploads.退休提示(智能体,源['rpcId'])#退役上传
        elif 种类=='steer':#改为引导
            智能体.inbox.移除(请求['itemId'])#移除
            智能体.转向(消息)#转向
        else:#未知
            raise 远程错误('gateway/bad-request','unknown queue action',{'kind':种类})#拒绝
        return {'accepted':True}#确认

    def cancel(自身,请求):
        """取消活动回合并保留收件箱。请求为 dict。"""
        智能体=_活智能体(自身._上下文,请求['sessionId'])#查找
        if 智能体 is None:#未附着
            raise 远程错误('session/not-found','session "'+str(请求['sessionId'])+'" not found (not attached)',{'sessionId':请求['sessionId']})#拒绝
        if 有子智能体所有者(自身._上下文,智能体.session.header,智能体):#子智能体
            raise 子智能体所有权错误(请求['sessionId'])#拒绝
        智能体.取消({'kind':'user'},{'keepInbox':True})#取消
        return {'accepted':True}#确认

    def _解析智能体(自身,会话标识):
        """把解析结果收成活智能体。"""
        结果=自身._智能体控制器.解析智能体(会话标识)#解析
        if isinstance(结果,dict) and 'error' in 结果:#失败
            raise 结果['error']#抛出
        return 结果['agent']#智能体

    def _读会话状态(自身,会话标识):
        """读附着或冷检视状态。"""
        附着=自身._上下文.sessions.get(会话标识)#附着
        if 附着 is not None:#附着
            return {'id':附着.id,'header':附着.header,'events':list(附着.snapshotEvents())}#即时
        检视=检视会话(自身._上下文,会话标识)#冷读
        return {'id':检视['meta']['id'],'header':检视['meta'],'events':list(检视['events'])}#冷

    def _分叉工作区(自身,源头):
        """解析 fork 工作区：直接附着或子智能体祖先。"""
        工作区列表=自身._上下文.workspaceRegistry.list()#全部
        直接=None#直接
        for 工作区 in 工作区列表:#查找
            标识列表=工作区.sessionIds if hasattr(工作区,'sessionIds') else []#会话集
            if 源头['id'] in 标识列表:#命中
                直接=工作区#记下
                break#停
        if 直接 is not None or 源头.get('origin')!='subagent':#普通或已找到
            return 直接#返回
        谱系=自身._上下文.sessionQuery.追踪会话谱系(源头['id'])#追溯
        for 祖先 in 谱系['ancestors']:#祖先
            祖头=祖先['header'] if isinstance(祖先,dict) and 'header' in 祖先 else 祖先#头
            for 工作区 in 工作区列表:#查找
                标识列表=工作区.sessionIds if hasattr(工作区,'sessionIds') else []#会话集
                if 祖头['id'] in 标识列表:#命中
                    return 工作区#返回
        return None#无

    def _拒绝创建(自身,会话标识,错误):
        """把创建错误映射为 Remote 失败。"""
        if isinstance(错误,远程错误):#已是
            raise 错误#原样
        if isinstance(错误,预设冲突):#预设
            详情={'sessionId':错误.sessionId,'requestedPreset':错误.requestedPreset}#详情
            if 错误.existingPreset is not None:#已有
                详情['existingPreset']=错误.existingPreset#已有
            raise 远程错误('agent-preset/conflict',str(错误),详情)#映射
        if isinstance(错误,cwd冲突):#cwd
            详情={'sessionId':错误.sessionId,'requestedCwd':错误.requestedCwd}#详情
            if 错误.existingCwd is not None:#已有
                详情['existingCwd']=错误.existingCwd#已有
            raise 远程错误('session/conflict',str(错误),详情)#映射
        if isinstance(错误,子智能体会话所有权):#子智能体
            raise 子智能体所有权错误(错误.sessionId)#映射
        raise 远程错误('gateway/internal','failed to create session "'+str(会话标识)+'": '+远程错误消息(错误),{})#内部
