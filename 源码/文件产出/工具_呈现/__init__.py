"""作用域工具：在所属会话中声明文件系统交付。

公开业务面仅中文名。工具名 present、事件 deliverables/presented 与配置键 maxFiles 保持英文线协议。
"""
import weakref#待定交付弱映射
from ...依赖.schemastery import 数字字段#配置字段
from ...内核.工具 import 定义工具#定义面向模型的工具
from ...工具.超时 import 若已中止则抛出#取消信号
from ...文件系统.文件系统 import 文件系统错误#文件系统带类型错误
from .类型 import 已呈现文件字段#再导出类型面

__all__=['名称','注入','配置','应用','默认','已呈现文件字段','呈现错误']#仅中文公开名

名称='tool-present'#Cordis插件名（字面量）
注入=['tools','fs','sessionProjections']#依赖工具、文件系统与投影
配置={#部署配置
    'maxFiles':数字字段(默认值=8),#每次调用最大文件数
}#配置模式结束

class 呈现错误(Exception):#本包异常基类
    """呈现工具入参或执行失败。"""
    def __init__(自身,消息):#记下英文消息
        """用原样英文消息构造。"""
        super().__init__(消息)#英文消息

def 应用(上下文,配置值):#登记 present 并在成功结果上追加交付事件
    """登记 present 工具；成功的 tools/result 追加 deliverables/presented。"""
    最大文件=配置值['maxFiles']#部署上限
    if isinstance(最大文件,bool) or not isinstance(最大文件,int) or 最大文件<1:#须为正整数
        raise 呈现错误('present requires a positive integer maxFiles')#加载失败
    待定=weakref.WeakKeyDictionary()#执行 → 待发表交付
    def 渲染(参数,值):#模型看到路径摘要
        """把结构化结果渲染成 Presented 路径行。"""
        行表=[]#摘要行
        for 文件 in 值['files']:#逐文件
            行表.append('Presented '+文件['path'])#英文摘要字面量
        return [{'type':'text','text':'\n'.join(行表)}]#单个文本块
    def 执行(参数,执行上下文):#校验并暂存交付
        """校验普通文件后暂存，等 tools/result 成功再发表。"""
        智能体=执行上下文['agent'] if 'agent' in 执行上下文 else None#调用方智能体
        if 智能体 is None:#非智能体
            raise 呈现错误('present requires an agent Session')#拒绝
        边界=上下文.sessionProjections.状态(智能体.session,'turnBoundary')#轮次边界
        if 边界 is None or 边界['openTurnStartSeq'] is None:#无打开轮次
            raise 呈现错误('present requires an open turn')#拒绝
        文件参数=参数['files']#模型给出的列表
        if len(文件参数)==0 or len(文件参数)>最大文件:#数量越界
            raise 呈现错误('present accepts 1 to '+str(最大文件)+' files')#拒绝
        头=智能体.session.header#会话头
        工作目录=头['cwd'] if 'cwd' in 头 else None#工作区
        if 工作目录 is None:#无工作区
            raise 呈现错误('present requires a workspace')#拒绝
        信号=执行上下文['signal'] if 'signal' in 执行上下文 else None#取消信号
        选项={'cwd':工作目录,'signal':信号}#解析选项
        文件表=[]#已校验声明
        for 文件 in 文件参数:#逐文件
            路径=文件['path']#原始路径
            if len(路径.strip())==0:#空路径
                raise 呈现错误('present requires a non-empty file path')#拒绝
            条目=上下文.fs.链接状态(路径,{'cwd':工作目录},信号)#不跟随末段链接
            if 条目 is not None and 条目['type']!='file':#路径级非普通文件
                raise 呈现错误('Cannot present '+路径+': not a regular file')#拒绝
            目标=上下文.fs.解析(路径,选项)#解析稳定目标
            信息=上下文.fs.状态(目标,信号)#跟随后元数据
            if 信息 is None:#缺失
                raise 文件系统错误('Cannot present '+路径+': file not found. Check the path, create the file if needed, and retry.','FS_NOT_FOUND')#未找到
            if 信息['type']!='file':#目标非普通文件
                raise 呈现错误('Cannot present '+路径+': not a regular file')#拒绝
            声明={'path':路径}#必填路径
            if 'description' in 文件:#可选描述
                声明['description']=文件['description']#原样
            文件表.append(声明)#收下
        若已中止则抛出(信号)#发表前再查中止
        待定[执行上下文]={'session':智能体.session,'turn':边界['lastTurn'],'files':文件表}#记下待定
        return {'turn':边界['lastTurn'],'files':文件表}#结构化结果
    def 工具结果(执行上下文,结果):#成功才追加事件
        """成功的最终结果才追加 deliverables/presented。"""
        交付=待定.pop(执行上下文,None)#取出并清除
        if 交付 is None or 结果['isError']:#无交付或失败
            return#不发表
        交付['session'].追加('deliverables/presented',{#耐久事件
            'turn':交付['turn'],#轮次
            'callId':执行上下文['callId'],#调用 id
            'files':交付['files'],#文件声明
        })#追加结束
    呈现工具=定义工具({#面向模型的 present
        'name':'present',#工具名
        'description':(#面向模型描述，字面量不译
            'Declare selected existing files accessible through the Session filesystem as final deliverables. '
            +'Use present when the user needs a separate file deliverable, especially Office documents, spreadsheets, and slide decks. '
            +'Prefer showing results in your final response when that is sufficient; creating or editing a file does not by itself require present. '
            +'Usually select the 1-2 most important deliverables; include more when needed, but at most 4 files in a single present call. '
            +'The files must already exist. The user opens the current source files; their contents are not copied or preserved.'
        ),#描述结束
        'parameters':{#参数模式
            'files':{#文件列表
                'type':'array',#数组
                'required':True,#必填
                'items':{#条目
                    'type':'object',#对象
                    'additionalProperties':False,#禁止额外字段
                    'properties':{#字段
                        'path':{'type':'string','required':True,'description':'Path of an existing regular file. Relative paths use the Session working directory.'},#路径
                        'description':{'type':'string','description':'Brief description for the user.'},#可选描述
                    },#字段结束
                },#条目结束
            },#files结束
        },#参数结束
        'output':{#结构化输出
            'schema':{#输出模式
                'type':'object',#对象
                'additionalProperties':False,#禁止额外字段
                'properties':{#字段
                    'turn':{'type':'integer','required':True},#轮次
                    'files':{#文件列表
                        'type':'array',#数组
                        'required':True,#必填
                        'items':{#条目
                            'type':'object',#对象
                            'additionalProperties':False,#禁止额外字段
                            'properties':{#字段
                                'path':{'type':'string','required':True},#路径
                                'description':{'type':'string'},#可选描述
                            },#字段结束
                        },#条目结束
                    },#files结束
                },#字段结束
            },#schema结束
            'render':渲染,#路径摘要
        },#output结束
        'execute':执行,#校验并暂存
    })#定义结束
    上下文.tools.登记(呈现工具)#挂到工具注册表
    上下文.监听('tools/result',工具结果)#成功结果发表交付

name=名称#Cordis插件名
inject=注入#Cordis依赖声明
Config=配置#Cordis配置模式
apply=应用#Cordis插件入口
默认=应用
default=应用#框架槽
