'面向模型的工具：经工作树服务创建并进入新的 Git 工作树'
from ...基础设施.通用工具.序列化编码 import 紧凑json编码#结果文本
from ...内核.工具 import 定义工具#工具定义

class 工作树工具错误(Exception):
    'create_worktree 拒绝没有调用方智能体的调用'
    def __init__(自身,消息):
        '用给人看的说明构造'
        super().__init__(消息)#异常文本
        自身.message=消息#工具错误读取的说明

名称='tool-worktree'#Cordis 插件名
依赖=['tools','worktrees']#工具注册表与工作树服务

def 应用(上下文):
    '登记 create_worktree。执行只调用工作树服务'
    def 执行(参数,执行元数据):
        '交给 worktrees 服务创建并进入'
        智能体=执行元数据['agent'] if 'agent' in 执行元数据 else None#发起调用的智能体
        if 智能体 is None:#没有会话就不能改目录
            raise 工作树工具错误('create_worktree 需要调用方智能体')#拒绝
        return 上下文.worktrees.创建(智能体,参数,执行元数据['signal'] if 'signal' in 执行元数据 else None)#服务创建
    def 渲染(_参数,值):
        '把线协议结果交给模型'
        return [{'type':'text','text':紧凑json编码(值)}]#单块文本
    def 呈现调用(参数):
        '通用调用卡片'
        return {'card':'generic','title':'create_worktree','rawInput':参数}#标题保持工具名
    上下文.tools.登记(定义工具({#登记工具
        'name':'create_worktree',#工具名
        'description':'Create a new Git branch and worktree from a local commit, branch, or tag, then change this session\'s working directory to it. Defaults to HEAD and a generated name. Uncommitted files stay in the source checkout. Existing names fail. Use working_directory with cd to leave; the checkout and branch remain.',#面向模型的说明保持原文
        'parameters':{#参数
            'name':{'type':'string','description':'New branch name, also used as the checkout directory. Omit to generate a unique name.'},#分支名
            'from':{'type':'string','description':'Local commit, branch, or tag to start from. Defaults to HEAD; no fetch is performed.'},#修订
        },#parameters结束
        'output':{#输出
            'schema':{#模式
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#线协议字段
                    'path':{'type':'string','required':True},#检出路径
                    'branch':{'type':'string','required':True},#新分支
                    'baseCommit':{'type':'string','required':True},#解析出的提交
                    'repositoryRoot':{'type':'string','required':True},#源仓库根
                },#properties结束
            },#schema结束
            'render':渲染,#渲染结果
        },#output结束
        'execute':执行,#执行
        'presentCall':呈现调用,#调用卡片
    }))#create_worktree结束

__all__=['工作树工具错误']#公开面；框架槽不入表
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
应用.name=名称#函数插件显示名
应用.inject=依赖#函数插件依赖
