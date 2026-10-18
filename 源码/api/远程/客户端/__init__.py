'平台无关的已生成宿主 Remote 贡献组装'
from ....交互.命令.远程 import 远程贡献表 as 命令远程#commands
from ....api.设置控制器.远程 import 远程贡献表 as 设置控制器远程#settings 与 credentials
from ....目标.目标.远程 import 远程贡献表 as 目标远程#goals
from ....模型后端.llm.远程 import 远程贡献表 as 大模型远程#llm
from ....拓展.cordis服务端.远程 import 远程贡献表 as 动态远程#dynamicCordisRunner
from ....反馈.消息反馈.远程 import 远程贡献表 as 消息反馈远程#messageFeedback
from ....反馈.命令_反馈.远程 import 远程贡献表 as 会话反馈远程#sessionFeedback
from ....上下文.会话引用.远程 import 远程贡献表 as 会话引用远程#sessionReferenceResolver
from ....子智能体.子智能体.远程 import 远程贡献表 as 子智能体远程#subagents
from ....api.会话控制器.远程 import 远程贡献表 as 会话远程#session、skills、fileReferences

__all__=['依赖','应用']#只导出本目录入口。贡献对象留在模块里供挂载

依赖=['remote']#硬依赖客户端 Remote 服务

def 应用(上下文,配置=None):
    '按上游顺序挂载已有的宿主 Remote 贡献。中途失败则按相反顺序拆除已挂上的'
    拆除列表=[]#已挂载贡献的拆除函数
    try:#某一份失败时拆掉已经挂上的
        for 贡献 in (#与上游 client 挂载序一致，缺贡献的包不在这里
            命令远程,设置控制器远程,目标远程,大模型远程,动态远程,
            消息反馈远程,会话反馈远程,会话引用远程,
            子智能体远程,会话远程,
        ):#本组装目前拿得到的贡献
            拆除列表.append(getattr(上下文.remote,'$mount')(贡献))#挂载并记下拆除函数
    except BaseException:#挂载失败
        for 拆除 in reversed(拆除列表):#后挂的先拆
            拆除()#拆除
        raise#原样继续抛
    def 整拆():
        '按挂载的相反顺序拆除，后挂的命名空间不比先挂的活得更久'
        for 拆除 in reversed(拆除列表):#后挂的先拆
            拆除()#拆除
    return 整拆#交给调用方在卸载时调用

inject=依赖#框架槽
apply=应用#框架槽
