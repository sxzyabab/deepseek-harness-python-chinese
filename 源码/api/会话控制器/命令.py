"""会话命令：各 Remote 方法上的显式激活策略。

对齐上游 `session-controller/src/commands.ts`。公开面仅中文名。
"""
import uuid#新会话 id
from .工具 import 取字段,解开,远程错误,远程错误消息#辅助
from .智能体 import 会话未找到,子智能体所有权错误,有子智能体所有者,检视会话,cwd冲突,预设冲突,子智能体会话所有权#智能体

__all__=['会话命令控制器']#仅中文公开名

class 会话命令控制器:#命令实现
    """实现会话控制器委托的业务命令。"""

    def __init__(自身,上下文,智能体们,默认cwd):#构造
        """保存依赖。"""
        自身._上下文=上下文#Cordis
        自身._智能体们=智能体们#智能体控制器
        自身._默认cwd=默认cwd#默认 cwd

    def create(自身,请求):#创建
        """创建或幂等采用普通会话。"""
        if 取字段(请求,'workspaceId') is not None and 取字段(请求,'cwd') is not None:#互斥
            raise 远程错误('gateway/bad-request','session.create accepts workspaceId or cwd, not both',{})#拒绝
        会话标识=取字段(请求,'sessionId') or ('session-'+str(uuid.uuid4()))#id
        工作区=None#工作区
        if 取字段(请求,'workspaceId') is not None:#按工作区
            工作区=自身._上下文.workspaceRegistry.get(取字段(请求,'workspaceId'))#查找
            if 工作区 is None:#未找到
                raise 远程错误('workspace/not-found','workspace "'+str(取字段(请求,'workspaceId'))+'" not found',{'workspaceId':取字段(请求,'workspaceId')})#拒绝
        工作目录=取字段(工作区,'path') if 工作区 is not None else (取字段(请求,'cwd') or 自身._默认cwd)#cwd
        try:#确保
            采用=解开(自身._智能体们.确保会话(会话标识,工作目录,取字段(请求,'sessionId') is not None,取字段(请求,'agentPreset')))#采用
        except Exception as 错误:#映射
            自身._拒绝创建(会话标识,错误)#抛出
        if 工作区 is not None:#附着工作区
            try:#附着
                解开(工作区.attachSession(会话标识))#attach
            except Exception as 错误:#失败
                raise 远程错误('session/workspace-attach-failed','session "'+str(会话标识)+'" was created but could not attach to workspace "'+str(取字段(工作区,'id'))+'": '+远程错误消息(错误),{'sessionId':会话标识,'workspaceId':取字段(工作区,'id')},cause=错误)#失败
        预设=自身._智能体们.会话预设(采用.session)#预设
        return {'sessionId':会话标识,**({} if 预设 is None else {'agentPreset':预设})}#结果

    def selectModel(自身,请求):#选模型
        """校验并安装会话本地模型选择。"""
        智能体=解开(自身._解析智能体(取字段(请求,'sessionId')))#解析
        def 操作():#选模型体
            """解析路由并记录选择。"""
            try:#解析
                解析=解开(自身._上下文.llm.resolveCallConfig({#解析调用
                    'provider':取字段(请求,'provider'),'model':取字段(请求,'model'),
                    **({} if 取字段(请求,'reasoningEffort') is None else {'reasoningEffort':取字段(请求,'reasoningEffort')}),
                }))#resolve
                已选={'provider':取字段(解析,'provider'),'model':取字段(解析,'model'),**({} if 取字段(解析,'reasoningEffort') is None else {'reasoningEffort':取字段(解析,'reasoningEffort')})}#选择
                智能体.session.append('model/selection',已选)#记录
                自身._智能体们.选择用于(智能体).current=已选#安装
                try:#保存默认
                    解开(自身._上下文.agentDefaultModel.saveSelection(已选))#保存
                except Exception as 警告:#非致命
                    自身._上下文.logger.warn('session-controller: default model not saved: '+str(警告))#日志
                return {'selected':dict(已选)}#返回
            except 远程错误:#已是 Remote
                raise#原样
            except Exception as 错误:#不可用
                raise 远程错误('session/model-unavailable',远程错误消息(错误),{'provider':取字段(请求,'provider'),'model':取字段(请求,'model')},cause=错误)#映射
        return 操作()#执行

    def rename(自身,请求):#重命名
        """追加用户拥有的会话标题。"""
        智能体=解开(自身._解析智能体(取字段(请求,'sessionId')))#解析
        标题们=自身._上下文.get('sessionTitle')#标题服务
        if 标题们 is None:#缺席
            raise 远程错误('gateway/internal','renaming is unavailable: this deployment mounts no session-title service',{})#拒绝
        try:#重命名
            接受=标题们.rename(智能体.session,取字段(请求,'title'))#改名
            return {'title':取字段(接受,'title'),'seq':取字段(接受,'eventSeq')}#结果
        except Exception as 错误:#失败
            if 错误.__class__.__name__=='SessionTitleInvalidError':#无效标题
                raise 远程错误('session/title-invalid',str(错误),{'sessionId':取字段(请求,'sessionId')})#映射
            raise 远程错误('gateway/internal','failed to rename session "'+str(取字段(请求,'sessionId'))+'": '+远程错误消息(错误),{})#内部

    def fork(自身,请求):#分叉
        """从已完成回合前缀分叉新会话。"""
        raise 远程错误('gateway/internal','session.fork is not fully ported in this Python slice yet',{'sessionId':取字段(请求,'sessionId')})#阻塞：待完整移植 fork 路径

    def prompt(自身,请求):#投入提示
        """显式恢复后投入提示。"""
        raise 远程错误('gateway/internal','session.prompt is not fully ported in this Python slice yet',{'sessionId':取字段(请求,'sessionId')})#阻塞：待完整移植 prompt/attachment 路径

    def attachment(自身,请求):#读附件
        """读取会话日志引用的图像。"""
        raise 远程错误('gateway/internal','session.attachment is not fully ported in this Python slice yet',{'sessionId':取字段(请求,'sessionId')})#阻塞

    def updateQueue(自身,请求):#改队列
        """变更仍待处理的队列项。"""
        智能体=自身._上下文.agents.get(取字段(请求,'sessionId'))#仅活智能体
        if 智能体 is not None and 有子智能体所有者(自身._上下文,智能体.session,智能体):#子智能体
            raise 子智能体所有权错误(取字段(请求,'sessionId'))#拒绝
        if 智能体 is None:#不在线
            raise 远程错误('session/queue-item-not-found','queued item is no longer pending',{'itemId':取字段(请求,'itemId')})#拒绝
        return {'accepted':True}#占位：完整队列编辑待移植

    def cancel(自身,请求):#取消
        """取消活动回合并保留收件箱。"""
        智能体=自身._上下文.agents.get(取字段(请求,'sessionId'))#查找
        if 智能体 is None:#未附着
            raise 远程错误('session/not-found','session "'+str(取字段(请求,'sessionId'))+'" not found (not attached)',{'sessionId':取字段(请求,'sessionId')})#拒绝
        if 有子智能体所有者(自身._上下文,智能体.session,智能体):#子智能体
            raise 子智能体所有权错误(取字段(请求,'sessionId'))#拒绝
        智能体.cancel({'kind':'user'},{'keepInbox':True})#取消
        return {'accepted':True}#确认

    def _解析智能体(自身,会话标识):#解析智能体或抛错
        """把解析结果收成活智能体。"""
        结果=解开(自身._智能体们.解析智能体(会话标识))#解析
        if isinstance(结果,dict) and 'error' in 结果:#失败
            raise 结果['error']#抛出
        return 结果['agent']#智能体

    def _拒绝创建(自身,会话标识,错误):#创建失败映射
        """把创建错误映射为 Remote 失败。"""
        if isinstance(错误,远程错误):#已是
            raise 错误#原样
        if isinstance(错误,预设冲突):#预设
            raise 远程错误('agent-preset/conflict',str(错误),{'sessionId':错误.sessionId,'requestedPreset':错误.requestedPreset,**({} if 错误.existingPreset is None else {'existingPreset':错误.existingPreset})})#映射
        if isinstance(错误,cwd冲突):#cwd
            raise 远程错误('session/conflict',str(错误),{'sessionId':错误.sessionId,'requestedCwd':错误.requestedCwd,**({} if 错误.existingCwd is None else {'existingCwd':错误.existingCwd})})#映射
        if isinstance(错误,子智能体会话所有权):#子智能体
            raise 子智能体所有权错误(错误.sessionId)#映射
        raise 远程错误('gateway/internal','failed to create session "'+str(会话标识)+'": '+远程错误消息(错误),{})#内部
