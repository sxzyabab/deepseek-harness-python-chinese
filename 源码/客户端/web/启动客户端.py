from ...依赖.loader import 加载器 as 加载器类#cordis 加载器插件
from .加载器状态 import 状态标签#协议标签
from .异常 import 网页错误#本包失败


def 启动客户端(选项):
    '组装客户端。个别插件失败或超时只记下来，其余继续挂'
    上下文=选项['ctx']#根上下文
    清单=选项['manifest']#启动清单
    汇报=选项['onEntryState'] if 'onEntryState' in 选项 else None#条目状态回调
    纤程=上下文.启动插件(加载器类)#挂加载器插件
    纤程.等待()#启动失败就抛出来
    加载器=上下文.加载器#取加载器服务
    if 加载器 is None:
        raise 网页错误('网页启动：加载器没有挂上')#没有服务就不能写内部加载器
    加载器.内部加载器=选项['modules']#导入走客户端模块系统

    def 纤程状态(纤程,旧状态=None):
        '把条目的纤程状态投影出去。旧状态是广播带上的前一个状态'
        条目=纤程.插件配置#这条纤程所属的插件配置
        if 条目 is None or 条目.纤程 is None:#没有条目或还没有纤程
            return#不投影
        if 汇报 is None:#无人渲染进度
            return#不投影
        汇报(条目.选项['name'],状态标签[条目.纤程.状态])#投影协议标签

    上下文.监听('internal/status',纤程状态)#纤程状态变化
    for 行 in 清单['plugins']:#先标成加载中
        if 汇报 is not None:#有人要进度
            汇报(行['id'],'loading')#标加载中
    选项['modules'].entries.start(加载器,清单)#按清单创建条目并等初建落定
    for 条目 in 加载器.列出插件配置():#导入失败的条目没有纤程
        if 条目.纤程 is None and 汇报 is not None:#导入失败
            汇报(条目.选项['name'],'failed')#标失败
    for 失败 in 选项['modules'].entries.快照['failures']:#超时或创建失败
        if 汇报 is not None:#有人要进度
            汇报(失败['id'],'failed',失败.get('message'))#标失败，带上原因
    try:#有插件没起来也不挡住其余
        加载器.等待()#把启动错误收集出来
    except Exception as 启动错误:#记下来，继续挂已起来的部分
        上下文.日志.错误(启动错误)#留在日志
