"""记录会话反馈事件，并注册 `/feedback` 命令与 sessionFeedback 远程服务。"""
from ...依赖 import cordis#外部依赖胶水
from ...身份.匿名用户id import 获取或创建匿名用户id#匿名用户 id
from ...交互.命令.标识构造 import 命令定义标识#命令定义身份
from .类型 import 反馈类别表#类别表

名称='command-feedback'#Cordis插件名
依赖=['commands']#依赖命令注册表
用法='Usage: /feedback <text>'#用法提示

__all__=['名称','依赖','用法','反馈类别表','记录反馈','会话反馈服务','应用']#仅中文公开名

def 记录反馈(会话,条目):#追加反馈记录事件
    """与任何 UI 触发器无关地记录。条目为 dict；空白正文记为缺席。"""
    正文=条目['text'].strip() if 'text' in 条目 and 条目['text'] is not None else ''#规范化
    载荷={}#事件载荷
    if len(正文)>0:#有正文
        载荷['text']=正文#正文
    if 'category' in 条目 and 条目['category'] is not None:#有类别
        载荷['category']=条目['category']#类别
    会话.追加('feedback/record',载荷)#追加事件

def 执行反馈命令(调用):#执行 /feedback
    """无正文则返回用法错误，否则记录并返回确认。调用是 dict。"""
    原文=调用['rawInput'] if 'rawInput' in 调用 else ''#正文
    if len(str(原文).strip())==0:#无正文
        return {'kind':'error','text':'Feedback text is required. '+用法}#用法错误
    智能体=调用['agent']#调用方智能体
    会话=智能体.session#会话
    记录反馈(会话,{'text':原文})#记录
    匿名用户=获取或创建匿名用户id()#真实匿名 id
    return {#成功确认
        'kind':'success',#成功
        'text':'Feedback recorded for session '+str(会话.id)+'\nAnonymous user: '+str(匿名用户)+'.',#确认文案
    }#成功返回结束

class 会话反馈服务(cordis.服务):#sessionFeedback Remote
    """产品面经其记录会话级评语。"""
    inject=['sessions']#依赖会话存储

    def __init__(自身,ctx):
        """用宿主上下文安装。"""
        super().__init__(ctx,'sessionFeedback')#登记服务名

    def record(自身,请求):#记录一条评语
        """请求为 dict；返回结果 dict。"""
        会话标识=请求['sessionId'] if 'sessionId' in 请求 else None#会话 id
        if 会话标识 not in 自身.ctx.sessions:#缺席
            return {'ok':False,'error':{'code':'session-not-found','sessionId':会话标识}}#未找到
        会话=自身.ctx.sessions[会话标识]#取会话
        记录反馈(会话,请求)#记录
        return {'ok':True,'value':{'recorded':True}}#已记录

def 应用(上下文):
    """注册 /feedback 并挂载 sessionFeedback Remote。"""
    上下文.plugin(会话反馈服务)#挂载服务
    def 处理(调用):
        """处理一条 /feedback。"""
        return 执行反馈命令(调用)#处理函数
    上下文.commands.register({#注册命令
        'definitionId':命令定义标识('@deepseek-ai/dsh-command-feedback'),#稳定定义身份
        'name':'feedback',#命令名
        'description':'Record feedback about this session',#描述
        'input':{'hint':'<text>'},#输入提示
        'recordInput':False,#不记录原始输入
        'handler':处理,#处理函数
    })#register结束

name=名称#Cordis插件名
inject=依赖#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
