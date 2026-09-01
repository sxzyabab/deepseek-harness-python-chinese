"""@deepseek-ai/dsh-subagent-codex 的本包拥有不变量配套。"""
包名='@deepseek-ai/dsh-subagent-codex'#包名
名称='subagent-codex-invariant'#插件名
注入=['invariants']#依赖
name=名称;inject=注入#Cordis 槽
__all__=['包名','名称','注入','安装','应用']#公开面

def 安装(*位置参数):return#空
def 应用(上下文对象):return 已兑现(上下文对象.invariants.register(包名,安装))#登记
apply=应用#Cordis 插件入口
