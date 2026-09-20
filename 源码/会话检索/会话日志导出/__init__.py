"""登记 export 命令：把本会话日志下载为 ZIP。"""
from ...交互.命令.标识构造 import 命令定义标识

包名='@deepseek-ai/dsh-session-log-export'
名称='session-log-download'
依赖=['commands','connection']

已请求={'kind':'success','text':'已请求下载会话日志。'}
路径拒绝={'kind':'error','text':'Web /export 命令不接受路径。'}

__all__=['包名','名称','依赖','应用','默认']

def 处理导出(调用):
    """无参数才请求下载。"""
    原始输入=调用['rawInput'] if 'rawInput' in 调用 else ''
    原始=原始输入.strip() if isinstance(原始输入,str) else ''
    if 原始=='':
        return 已请求
    return 路径拒绝

def 应用(上下文):
    """登记仅 Web 的 `/export` 命令，由浏览器下载插件观察。"""
    def 挂上():
        """登记 export 命令并在拆除时注销。"""
        return 上下文.commands.register({'definitionId':命令定义标识('@deepseek-ai/dsh-session-log-export'),'name':'export','description':'把本会话日志下载为 ZIP 归档','handler':处理导出})
    上下文.副作用(挂上,'session-log-download: command')

默认=应用
name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
default=默认#框架槽
