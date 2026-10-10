from ...依赖.schemastery import 字典字段,字符串字段#配置

__all__=['名称','依赖','配置','应用']#公开面

名称='subagent-fork-in-process'#Cordis 插件名
依赖=['subagents']#依赖
配置=字典字段(字典结构={'providerName':字符串字段(默认值='fork')})#配置

def 已完成回合前缀(父):
    '父已完成回合前的事件前缀。活序号等于数组下标，切片含最后一条 turn/end'
    事件列表=父.session.snapshotEvents()#日志快照
    最后结束=None#最后 turn/end
    for 索引 in range(len(事件列表)-1,-1,-1):#倒扫
        事件=事件列表[索引]#当前
        类型=事件['type'] if isinstance(事件,dict) else getattr(事件,'type',None)#类型
        if 类型=='turn/end':#命中
            最后结束=事件#记下
            break#停
    if 最后结束 is None:#无完成回合
        return []#空前缀
    序号=最后结束['seq'] if isinstance(最后结束,dict) else 最后结束.seq#序号
    return 事件列表[:序号+1]#前缀

class 进程内分叉提供方:
    '用父已完成回合前缀种子化子体'
    def __init__(自身,名):
        '记下提供方名与能力'
        自身.名称=名#中文名
        自身.能力={'agentOptions':True,'outputSchema':True,'depthLimit':True,'toolFilter':True,'persona':True}#能力
        自身.继承父上下文=True#契约

    def 准备可续跑(自身,请求):
        '准备可续跑分叉规格。请求为 dict'
        种子=已完成回合前缀(请求['parent'])#种子
        return {} if len(种子)==0 else {'seed':种子}#规格

def 应用(上下文,配置值):
    '加载 fork 提供方。配置为 dict'
    名=配置值['providerName'] if 'providerName' in 配置值 else 'fork'#提供方名
    上下文.subagents.登记提供方(进程内分叉提供方(名))#登记

name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
Config=配置#框架槽
default=应用#框架槽
