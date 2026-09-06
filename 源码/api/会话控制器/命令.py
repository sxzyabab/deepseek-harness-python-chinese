"""会话命令：各 Remote 方法上的显式激活策略。

对齐上游 `session-controller/src/commands.ts`。公开面仅中文名。
"""
import uuid#新会话 id
from .远程错误与并发 import 远程错误,远程错误消息#远程错误
from .智能体 import 子智能体所有权错误,有子智能体所有者,cwd冲突,预设冲突,子智能体会话所有权#智能体

__all__=['会话命令控制器']#仅中文公开名

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
        try:
            调用={'provider':请求['provider'],'model':请求['model']}#解析调用
            if 'reasoningEffort' in 请求 and 请求['reasoningEffort'] is not None:#有推理
                调用['reasoningEffort']=请求['reasoningEffort']#推理
            解析=自身._上下文.llm.resolveCallConfig(调用)#resolve 为 dict
            已选={'provider':解析['provider'],'model':解析['model']}#选择
            if 'reasoningEffort' in 解析 and 解析['reasoningEffort'] is not None:#有推理
                已选['reasoningEffort']=解析['reasoningEffort']#推理
            智能体.session.append('model/selection',已选)#记录
            自身._智能体控制器.选择用于(智能体).current=已选#安装
            try:
                自身._上下文.agentDefaultModel.saveSelection(已选)#保存
            except (OSError,ValueError,TypeError) as 警告:
                自身._上下文.日志.警告('session-controller: default model not saved: '+str(警告))#日志
            return {'selected':dict(已选)}#返回
        except 远程错误:
            raise#原样
        except (OSError,ValueError,TypeError,KeyError,AttributeError) as 错误:
            raise 远程错误('session/model-unavailable',远程错误消息(错误),{'provider':请求['provider'],'model':请求['model']},原因=错误)#映射

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
        raise 远程错误('gateway/internal','session.fork is not fully ported in this Python slice yet',{'sessionId':请求['sessionId'] if 'sessionId' in 请求 else None})#阻塞：待完整移植 fork 路径

    def prompt(自身,请求):
        """显式恢复后投入提示。请求为 dict。"""
        raise 远程错误('gateway/internal','session.prompt is not fully ported in this Python slice yet',{'sessionId':请求['sessionId'] if 'sessionId' in 请求 else None})#阻塞：待完整移植 prompt/attachment 路径

    def attachment(自身,请求):
        """读取会话日志引用的图像。请求为 dict。"""
        raise 远程错误('gateway/internal','session.attachment is not fully ported in this Python slice yet',{'sessionId':请求['sessionId'] if 'sessionId' in 请求 else None})#阻塞

    def updateQueue(自身,请求):
        """变更仍待处理的队列项。请求为 dict。"""
        智能体=自身._上下文.agents.get(请求['sessionId'])#仅活智能体
        if 智能体 is not None and 有子智能体所有者(自身._上下文,智能体.session.header,智能体):#子智能体
            raise 子智能体所有权错误(请求['sessionId'])#拒绝
        if 智能体 is None:#不在线
            raise 远程错误('session/queue-item-not-found','queued item is no longer pending',{'itemId':请求['itemId'] if 'itemId' in 请求 else None})#拒绝
        return {'accepted':True}#占位：完整队列编辑待移植

    def cancel(自身,请求):
        """取消活动回合并保留收件箱。请求为 dict。"""
        智能体=自身._上下文.agents.get(请求['sessionId'])#查找
        if 智能体 is None:#未附着
            raise 远程错误('session/not-found','session "'+str(请求['sessionId'])+'" not found (not attached)',{'sessionId':请求['sessionId']})#拒绝
        if 有子智能体所有者(自身._上下文,智能体.session.header,智能体):#子智能体
            raise 子智能体所有权错误(请求['sessionId'])#拒绝
        智能体.cancel({'kind':'user'},{'keepInbox':True})#取消
        return {'accepted':True}#确认

    def _解析智能体(自身,会话标识):
        """把解析结果收成活智能体。"""
        结果=自身._智能体控制器.解析智能体(会话标识)#解析
        if isinstance(结果,dict) and 'error' in 结果:#失败
            raise 结果['error']#抛出
        return 结果['agent']#智能体

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
