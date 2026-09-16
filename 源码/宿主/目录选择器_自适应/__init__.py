"""自适应目录选择器：启动时按宿主处境采样一次，挂上 native 或 browse 交互两面。

对齐上游 `@deepseek-ai/dsh-host-directory-picker-auto`。公开面仅中文名。
"""
import os,sys#环境与平台
from ...工具.启动环境 import 取启动环境,经ssh拉起#SSH 拉起事实
from .探测 import 能否执行,有Linux选择器二进制#PATH 探测
from .解析 import 解析目录选择后端#按宿主事实解析后端

名称='directory-picker-auto'#Cordis 插件名
注入=['webServer','loader']#依赖 webServer 与 loader

后端包={#kind → 宿主后端包名
    'native':'@deepseek-ai/dsh-host-directory-picker-native',#原生选择器后端
    'browse':'@deepseek-ai/dsh-host-directory-picker-browse',#应用内浏览后端
}#后端包结束

界面包={#kind → 客户端界面包名
    'native':'@deepseek-ai/dsh-client-ui-directory-picker-native',#原生选择器界面
    'browse':'@deepseek-ai/dsh-client-ui-directory-picker-browse',#应用内浏览界面
}#界面包结束

__all__=['名称','注入','后端包','界面包','应用','能否执行','有Linux选择器二进制','解析目录选择后端']#公开面

def _节点平台():#对齐 process.platform
    """粗映射到 Node 平台名。"""
    名=sys.platform#本机
    if 名=='win32':#Windows
        return 'win32'
    if 名=='darwin':#macOS
        return 'darwin'
    if 名.startswith('linux'):#Linux
        return 'linux'
    return 名#原样

def 应用(上下文):#解析交互并挂条目
    """按启动时一次采样解析交互，并把其后端与界面挂为 Loader 条目。"""
    后端=解析目录选择后端({#按当前宿主事实
        'bindHost':上下文.webServer.host,#有效绑定主机
        'platform':_节点平台(),#当前平台
        'ssh':经ssh拉起(取启动环境(上下文)),#SSH 拉起
        'env':{#显示会话
            'DISPLAY':os.environ.get('DISPLAY'),
            'WAYLAND_DISPLAY':os.environ.get('WAYLAND_DISPLAY'),
        },
        'linuxChooser':有Linux选择器二进制(os.environ.get('PATH'),能否执行),#Linux 选择器
    })
    async def 挂载():#挂两面
        """把解析出的交互两面挂进 Loader 根树。"""
        标识列表=[]#已创建 id
        async def 卸载():#倒序卸
            """卸掉本插件挂上的全部条目。"""
            for 标识 in reversed(list(标识列表)):#后挂先卸
                条目=getattr(上下文.loader,'store',{}).get(标识)#树上的条目
                if 条目 is None:#已不在
                    continue#跳过
                纤程=getattr(条目,'fiber',None)#条目纤程
                拆除=纤程.dispose() if 纤程 is not None else None#先拿到拆除
                上下文.loader.remove(标识)#从树上摘掉
                if 拆除 is not None:#有拆除承诺
                    await 拆除#等这一面静止
        try:#先后端后界面
            for 包名 in (后端包[后端],界面包[后端]):#两面
                标识=await 上下文.loader.create({'name':包名})#创建
                标识列表.append(标识)#记下
                条目=上下文.loader.resolve(标识)#解析刚挂上的条目
                if getattr(条目,'fiber',None) is None:#没有纤程
                    raise Exception('directory-picker-auto: failed to load '+包名)#失败
                await 条目.fiber.await()#等这一面启动完成
        except Exception:#中途失败
            await 卸载()#卸残留
            raise#原样抛出
        return 卸载#disposers
    return 上下文.effect(挂载,'directory-picker-auto: interaction entries')#登记 effect
