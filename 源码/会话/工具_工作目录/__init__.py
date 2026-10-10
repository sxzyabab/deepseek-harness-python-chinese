'读取或更改当前会话的工作目录；已有进程各自保留自己的目录'
from ...内核.工具 import 定义工具#导入工具定义

class 工作目录工具错误(Exception):
    '工作目录工具拒绝缺少会话的调用'

名称='tool-working-directory'#Cordis插件名
依赖=['tools','workingDirectory']#工具注册表与工作目录服务

def 应用(上下文):
    '登记 working_directory，读当前目录或按 cd 进入已有目录'
    def 执行(参数,执行元数据):
        '缺 cd 时确保当前目录，有 cd 时切换；返回绝对路径'
        智能体=执行元数据.agent#发起调用的智能体
        if 智能体 is None:#没有会话就不能改目录
            raise 工作目录工具错误('working_directory 需要智能体会话')
        信号=执行元数据.signal#取消信号
        if 'cd' not in 参数 or 参数['cd'] is None:#省略 cd 表示只读
            目录=上下文.workingDirectory.ensure(智能体,信号)#校验并在目录消失时回到原项目
        else:#进入已有目录
            目录=上下文.workingDirectory.set(智能体,参数['cd'],信号)#相对路径按当前目录解析
        return {'cwd':目录}#线协议字段保持 cwd
    def 渲染(_参数,值):
        '把绝对路径交给模型'
        return [{'type':'text','text':值['cwd']}]
    上下文.tools.register(定义工具({
        'name':'working_directory',#工具名
        'description':'Read the current working directory, or change it with cd. Relative paths use the current directory. Existing shells and running processes keep their own directories.',#面向模型的说明保持原文
        'parameters':{
            'cd':{'type':'string','description':'Existing directory to enter. Omit to read the current directory.'},
        },
        'output':{
            'schema':{
                'type':'object',
                'additionalProperties':False,
                'properties':{'cwd':{'type':'string','required':True,'description':'Current absolute working directory.'}},
            },
            'render':渲染,
        },
        'execute':执行,
    }))

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=应用#框架槽
默认=应用

__all__=['名称','依赖','应用','默认','工作目录工具错误']
