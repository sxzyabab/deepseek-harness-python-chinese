"""Workspace-backed Session creation for one settled webhook rule result。对齐上游 `webhook/src/session.ts`。"""
import os,uuid#绝对路径与会话 id
from ...内核.会话 import 会话标识#会话 id 品牌
from ...模型后端.llm import 创建用户消息,错误链#用户消息与错误链

class 会话错误(Exception):
    """webhook 会话创建路径上的失败。"""

class 会话查询错误中止(会话错误):
    """webhook 创建路径上的取消。"""

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号.is_set()#Event 置位即中止

def 若已中止则抛出(信号):
    """已中止则抛出取消。"""
    if 已中止(信号):#已中止
        raise 会话查询错误中止()#取消

def 必填字符串(记录,字段):
    """从规则结果读取一个非空字符串字段。记录为 dict。"""
    if 字段 not in 记录:#键不存在
        raise TypeError(f'webhook Session request {字段} must be a non-empty string')#拒绝
    值=记录[字段]#字段值
    if (not isinstance(值,str)) or 值.strip()=='':#非法
        raise TypeError(f'webhook Session request {字段} must be a non-empty string')#拒绝
    return 值#合法值

def 解析请求(上下文,输入):
    """快照并校验同进程规则结果，再跨调用边界使用。输入为 dict。"""
    if 输入 is None or not isinstance(输入,dict):#必须是对象
        raise TypeError('webhook rule result must be null or a Session request object')#拒绝
    工作区路径=必填字符串(输入,'workspacePath')#工作区路径
    if not os.path.isabs(工作区路径):#必须绝对路径
        raise TypeError(f'webhook Session request workspacePath must be absolute, got {repr(工作区路径)}')#拒绝
    标题=必填字符串(输入,'title')#标题
    提示=必填字符串(输入,'prompt')#提示
    智能体预设=必填字符串(输入,'agentPreset')#智能体预设
    权限预设=必填字符串(输入,'permissionPreset')#权限预设
    模型=输入['model'] if 'model' in 输入 else None#可选模型
    if 模型 is not None and (not isinstance(模型,dict)):#模型必须是对象
        raise TypeError('webhook Session request model must be an object')#拒绝
    if 模型 is None:#省略模型
        已选=上下文.agentDefaultModel.currentSelection()#当前默认
        智能体选项={'provider':已选['provider'],'model':已选['model']}#路由
        模型选择=dict(已选)#完整选择
    else:#显式模型
        提供方=必填字符串(模型,'provider')#提供方
        模型号=必填字符串(模型,'model')#模型
        最大token=模型['maxTokens'] if 'maxTokens' in 模型 else None#可选上限
        if 最大token is not None and (isinstance(最大token,bool) or (not isinstance(最大token,int)) or 最大token<=0):#非法上限
            raise TypeError('webhook Session request model.maxTokens must be a positive safe integer')#拒绝
        智能体选项={'provider':提供方,'model':模型号}#路由
        if 最大token is not None:#带上上限
            智能体选项['maxTokens']=最大token#写入
        模型选择={'provider':提供方,'model':模型号}#显式选择
    return {
        'workspacePath':工作区路径,'title':标题,'prompt':提示,
        'agentPreset':智能体预设,'permissionPreset':权限预设,
        'modelSelection':模型选择,'agentOptions':智能体选项,
    }#解析结果

def 报告回滚失败(上下文,主题,错误):
    """记录回滚失败，不替换原始失败。"""
    上下文.日志.警告(f'webhook: {主题} rollback failed: {错误链(错误)}')#记警告

def 安装初始模型选择(智能体上下文,选择):
    """在首次耐久请求头出现前应用创建时选择。选择为 dict。"""
    def 请求钩子(载荷,下一步):
        """首条请求前覆盖 provider/model。"""
        已解析=下一步(载荷)#先走链
        智能体=智能体上下文.agent#作用域智能体
        if 智能体 is None:#没有智能体
            raise 会话错误('webhook Session setup has no scoped Agent')#拒绝
        if 智能体.session.requestHeader() is not None:#已有请求头
            return 已解析#不再覆盖
        if 'provider' not in 已解析 or 'model' not in 已解析 or 已解析['provider']!=选择['provider'] or 已解析['model']!=选择['model']:#路由已变
            return 已解析#不覆盖
        下一=dict(已解析)#拷贝
        下一.pop('reasoningEffort',None)#去掉继承力度
        if 'reasoningEffort' in 选择 and 选择['reasoningEffort'] is not None:#有力度
            下一['reasoningEffort']=选择['reasoningEffort']#写入
        return 下一#返回覆盖
    智能体上下文.监听('agent/request',请求钩子)#挂上钩子

def 创建Webhook会话(上下文,投递,规则号,请求,信号):
    """创建、附着、命名、配置并提示一条普通根 Session。投递为 dict。"""
    已解析=解析请求(上下文,请求)#解析请求
    上下文.permissionPresets.resolve(已解析['permissionPreset'])#校验权限预设
    预设=上下文.agentPresets.resolve(已解析['agentPreset'])#解析智能体预设
    上下文.agentPresets.standingKeyFor(预设['id'])#校验站立键
    若已中止则抛出(信号)#已取消
    工作区=上下文.workspaceRegistry.create(已解析['workspacePath'])#创建工作区
    若已中止则抛出(信号)#已取消
    会话号=会话标识(f'webhook-{uuid.uuid4()}')#铸造 webhook 会话
    def 安装预设(智能体上下文):
        """setup 回调：挂载预设并安装模型选择。"""
        安装预设与模型(上下文,智能体上下文,预设['id'],已解析['modelSelection'])#挂载
    句柄=上下文.agents.创建({
        'sessionId':会话号,'signal':信号,
        'meta':{'cwd':工作区.path,'agentPreset':预设['id']},
        'agentOptions':已解析['agentOptions'],
        'setup':安装预设,
    })#创建智能体
    已附着=False#附着标记
    try:#附着、权限、标题、提示
        若已中止则抛出(信号)#已取消
        工作区.attachSession(会话号)#附着工作区
        已附着=True#已附着
        若已中止则抛出(信号)#已取消
        上下文.permissionPresets.set(句柄.智能体.session,已解析['permissionPreset'])#应用权限
        上下文.sessionTitle.rename(句柄.智能体.session,已解析['title'])#写标题
        句柄.智能体.后续(创建用户消息({
            'content':[{'type':'text','text':已解析['prompt']}],
            'source':{
                'kind':'webhook',
                'provider':投递['kind'],
                'source':投递['source'],
                'deliveryId':投递['deliveryId'],
                'ruleId':规则号,
                'form':'notice',
                'summary':f"{投递['kind']} webhook handled by {规则号}",
            },
        }))#投递首条提示
    except (会话错误,TypeError,OSError) as 错误:#失败回滚
        if 已附着:#曾附着
            try:#拆离工作区
                工作区.detachSession(会话号)#拆离
            except (会话错误,TypeError,OSError) as 回滚错误:#回滚失败
                报告回滚失败(上下文,f'Workspace detach for Session "{会话号}"',回滚错误)#记警告
        try:#销毁智能体
            句柄.拆除()#销毁
        except (会话错误,TypeError,OSError) as 回滚错误:#回滚失败
            报告回滚失败(上下文,f'Agent disposal for Session "{会话号}"',回滚错误)#记警告
        raise 错误#原样抛出

def 安装预设与模型(上下文,智能体上下文,预设号,模型选择):
    """挂载智能体预设并安装初始模型选择。"""
    上下文.agentPresets.mount(智能体上下文,预设号)#挂载预设
    安装初始模型选择(智能体上下文,模型选择)#安装模型选择
