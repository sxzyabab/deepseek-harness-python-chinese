"""目录选择缝的自适应选择器：启动时按宿主处境采样一次并把匹配的交互挂进 Loader 根树。

对齐上游 `@deepseek-ai/dsh-host-directory-picker-auto`。公开面仅中文名。本包不提供默认导出（Loader 的 unwrapExports 会折叠掉 inject）。
"""
import os,sys#环境与平台
from cordis.工具 import 是否thenable#可等待判定
from .解析 import (
    目录选择后端种类,#后端 kind
    解析目录选择后端,#纯决策
    可执行,#可执行谓词
    有Linux选择器二进制,#PATH 探测
)#解析与探测

__all__=[#仅中文公开名
    '名称','注入','应用',
    '后端包们','界面包们',
    '目录选择后端种类','解析目录选择后端','可执行','有Linux选择器二进制',
]#公开面结束

名称='directory-picker-auto'#Cordis 插件名
注入=['webServer','loader']#依赖 webServer 与 loader
后端包们={#kind → 宿主后端包名
    'native':'@deepseek-ai/dsh-host-directory-picker-native',#原生后端
    'browse':'@deepseek-ai/dsh-host-directory-picker-browse',#浏览后端
}#后端表结束
界面包们={#kind → 客户端界面包名
    'native':'@deepseek-ai/dsh-client-ui-directory-picker-native',#原生界面
    'browse':'@deepseek-ai/dsh-client-ui-directory-picker-browse',#浏览界面
}#界面表结束

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

def 应用(上下文):#解析交互并挂上对应后端与界面条目
    """按启动时一次采样解析交互，并把其后端与界面挂为 Loader 条目。"""
    后端=解析目录选择后端({#按当前宿主事实解析
        'bindHost':上下文.webServer.host,#有效绑定主机
        'platform':sys.platform,#当前平台
        'env':os.environ,#进程环境
        'linuxChooser':有Linux选择器二进制(os.environ.get('PATH'),可执行),#Linux 选择器
    })#解析结束
    def 装条目():#把解析出的交互两面挂进 Loader 根树
        """先后创建后端与界面条目；拆除时倒序卸载。"""
        标识们=[]#已创建条目 id
        def 卸载():#卸掉本插件挂上的全部条目
            """后挂的先卸。"""
            for 标识 in reversed(list(标识们)):#倒序
                存储=getattr(上下文.loader,'store',None)#条目树
                if 存储 is not None and 标识 not in 存储:#已不在树
                    continue#跳过
                解开(上下文.loader.remove(标识))#卸掉并等静止
        try:#先后创建
            for 包名 in (后端包们[后端],界面包们[后端]):#先后端后界面
                标识们.append(解开(上下文.loader.create({'name':包名})))#创建并记下
        except BaseException:#中途失败
            卸载()#卸掉已挂
            raise#原样抛出
        return 卸载#交给 effect
    上下文.effect(装条目,'directory-picker-auto: interaction entries')#挂载 effect
