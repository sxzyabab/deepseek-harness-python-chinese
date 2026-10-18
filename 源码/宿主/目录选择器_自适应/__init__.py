'启动时采样一次宿主事实，把 native 或 browse 的后端和界面挂进加载器'
import os,sys#平台与进程环境
from ...工具.启动环境 import 取启动环境,经ssh拉起#进程层的 SSH 事实
from . import 异常,探测,解析#同目录模块，导入即执行顶层
from .探测 import 能否执行,有Linux选择器二进制#Linux 选择器探测
from .解析 import (
    目录选择后端种类,#native 或 browse
    目录选择环境,#显示环境
    目录选择宿主事实,#一次采样的宿主事实
    解析目录选择后端,#决议
)

__all__=[#包根公开名。框架槽 name、inject、apply 不在这里
    '名称','依赖','应用',
    '后端包','界面包',
    '能否执行','有Linux选择器二进制',
    '目录选择后端种类','目录选择环境','目录选择宿主事实','解析目录选择后端',
    '异常','探测','解析',
]

名称='directory-picker-auto'#插件名
依赖=['webServer','connection','加载器']#网页服务、信任围栏、加载器。上游槽名 loader，中文服务名是加载器

后端包={#kind 到宿主后端包名。字面量，不是可调参数
    'native':'@deepseek-ai/dsh-host-directory-picker-native',#系统选择器后端
    'browse':'@deepseek-ai/dsh-host-directory-picker-browse',#应用内浏览后端
}

界面包={#kind 到客户端界面包名。只挂说明符，这里不导入它们
    'native':'@deepseek-ai/dsh-client-ui-directory-picker-native',#系统选择器界面
    'browse':'@deepseek-ai/dsh-client-ui-directory-picker-browse',#应用内浏览界面
}


def 应用(上下文,配置值=None):
    '按启动时一次采样把后端和界面挂进加载器。失败或卸载时倒序摘掉这两条。加载器传入的配置本插件不读'
    后端=解析目录选择后端({#这一次启动的宿主事实
        'bindHost':上下文.webServer.host,#有效绑定主机
        'allowsRemoteAuthorities':上下文.connection.allowsRemoteAuthorities,#允许远程权威则只能 browse
        'platform':sys.platform,#宿主平台，不另做映射
        'ssh':经ssh拉起(取启动环境(上下文)),#SSH 拉起则只能 browse
        'env':os.environ,#显示会话环境
        'linuxChooser':有Linux选择器二进制(os.environ.get('PATH'),能否执行),#Linux 是否有选择器
    })

    def 挂载():
        '先后端后界面挂进加载器。中途失败则倒序卸掉已经挂上的条目'
        加载器=上下文.加载器#已注入的加载器
        标识列表=[]#本趟创建的条目 id

        def 卸载():
            '倒序卸掉。树已经拆掉的跳过'
            for 标识 in reversed(list(标识列表)):#后挂的先卸
                try:#可能已被树拆掉
                    条目=加载器.解析(标识)#还在树上才卸
                except LookupError:#对应 store 里已经没有
                    continue#跳过
                纤程=条目.纤程#这一面的纤程
                if 纤程 is not None:#没有纤程就只摘条目
                    纤程.拆除()#先拆纤程
                加载器.移除(标识)#再从树上摘掉

        try:#先后端，再界面
            for 包名 in (后端包[后端],界面包[后端]):#同一选择的两面
                标识=加载器.创建({'name':包名})#挂进内存根树
                标识列表.append(标识)#记下，失败时才能卸
                条目=加载器.解析(标识)#取出刚挂上的条目
                纤程=条目.纤程#这一面的纤程
                if 纤程 is None:#没有纤程
                    raise RuntimeError('directory-picker-auto: failed to load '+包名)#这一面没加载起来
                纤程.等待()#等这一面启动完成。失败则抛出
        except BaseException:#启动失败先卸残留，再把原错误抛回去
            卸载()#已创建的条目不能留在树上
            raise#原错误
        return 卸载#卸载本插件时再跑一遍

    上下文.副作用(挂载,'directory-picker-auto: interaction entries')#登记可拆除副作用


name=名称#框架槽
inject=依赖#框架槽
apply=应用#框架槽
