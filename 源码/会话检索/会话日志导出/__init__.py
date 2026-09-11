"""盖在 ApiProxy 拥有的宿主端点上的 Web 会话日志下载命令。对齐上游 `@deepseek-ai/dsh-session-log-export`。"""
from ...交互.命令.标识构造 import 命令定义标识#命令定义身份
名称='session-log-download'#Cordis插件名（字面量）
注入=['commands','connection']#依赖命令注册表与连接

已请求={'kind':'success','text':'Session log download requested.'}#浏览器插件观察的成功结算
路径拒绝={'kind':'error','text':'The Web /export command does not accept a path.'}#拒绝路径

__all__=['名称','注入','应用']#仅中文公开名

def 处理导出(调用):
    """无参数才请求下载。"""
    原始输入=调用['rawInput'] if 'rawInput' in 调用 else ''#原始输入
    原始=原始输入.strip() if isinstance(原始输入,str) else ''#修剪
    if 原始=='':#无参数
        return 已请求#请求下载
    return 路径拒绝#拒绝路径

def 应用(上下文):
    """登记仅 Web 的 `/export` 命令，由浏览器下载插件观察。"""
    def 挂上():
        """登记 export 命令并在拆除时注销。"""
        return 上下文.commands.register({'definitionId':命令定义标识('@deepseek-ai/dsh-session-log-export'),'name':'export','description':'Download this Session log as a ZIP archive','handler':处理导出})#登记命令
    上下文.副作用(挂上,'session-log-download: command')#effect标签

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
apply=应用#Cordis插件入口
default=应用#Cordis 默认导出槽
