"""浏览器半边：模块系统类和线约定，外加登记插件面。

对齐上游 `modules/src/client/index.ts`。公开面仅中文名。
"""
from .系统 import 客户端模块系统#再导出模块系统
from .清单 import (#再导出线约定
    客户端模块错误,#本包异常
    解析启动清单,#解析
    启动清单,#清单
    启动模块行,#模块行
    启动插件行,#插件行
    网页启动入口,#入口
    网页启动图,#图
    客户端插件交接,#交接
    客户端窗口,#窗口
    客户端模块记录,#记录
    客户端模块加载器,#加载器
    客户端模块系统选项,#选项
)#清单面

__all__=[#仅中文公开名
    '应用',
    '客户端模块错误',
    '客户端模块系统',
    '解析启动清单',
    '启动清单',
    '启动模块行',
    '启动插件行',
    '网页启动入口',
    '网页启动图',
    '客户端插件交接',
    '客户端窗口',
    '客户端模块记录',
    '客户端模块加载器',
    '客户端模块系统选项',
]#公开面结束

def 应用(上下文):#安装浏览器半边
    """把内核建成的模块系统登记为 ctx.modules。"""
    窗口=globals()#窗口面
    if '__DSH_MODULES__' not in 窗口 or 窗口['__DSH_MODULES__'] is None:#槽位空
        raise 客户端模块错误('client-modules: window.__DSH_MODULES__ missing — the shell kernel must construct the module system before plugin boot')#大声失败
    模块=窗口['__DSH_MODULES__']#内核交接槽
    上下文.反射.提供服务('modules',模块)#提供 ctx.modules

apply=应用#框架槽
