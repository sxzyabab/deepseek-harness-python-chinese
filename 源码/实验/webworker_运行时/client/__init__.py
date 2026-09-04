"""页面半：部署到达 worker 托管 harness 所需的一切。

这是 **Cordis 前 glue，不是客户端插件**：它安装传输全局并执行 boot 注入表，
客户端插件图稍后经该表加载，因此它本身不能是图中的一行。

对齐上游 `webworker-runtime/src/client/index.ts`。公开面仅中文名。
"""
from ..镜像布局 import 镜像文件名#镜像叶名
from ..fixture清单 import (#fixture面
    预览fixture清单文件,#叶名
    预览fixture清单版本,#版本
    解析预览fixture清单,#解析
)#fixture目录
from .客户端 import 工作线程隧道#页面隧道
from .应用注入 import 应用索引注入#注入表解释器
from .源选择器 import 选择预览源#来源选择器

__all__=[#仅中文公开名
    '工作线程隧道','应用索引注入','镜像文件名',
    '解析预览fixture清单','预览fixture清单文件','预览fixture清单版本',
    '选择工作线程宿主源','连接工作线程宿主',
]#公开面结束

def boot就绪屏障():#获取或创建屏障
    """与客户端入口 pre-boot await 共享的 boot 就绪 deferred。"""
    全局=globals()#全局
    键='__DSH_BOOT_READY__'#共享键
    if 键 not in 全局 or 全局[键] is None:#惰性创建
        盒={'resolve':None,'reject':None,'done':False,'error':None}#deferred盒
        def 兑现():#结算就绪
            """标记就绪。"""
            盒['done']=True#就绪
        def 拒绝(原因):#结算失败
            """标记失败。"""
            盒['done']=True#完成
            盒['error']=原因#错误
        盒['resolve']=兑现#挂兑现
        盒['reject']=拒绝#挂拒绝
        全局[键]=盒#写入
    return 全局[键]#返回屏障

def 扣住工作线程宿主boot():#扣住boot
    """在异步来源选择器等待用户输入之前安装页面 boot 屏障。"""
    boot就绪屏障()#取屏障

def 选择工作线程宿主源(选项=None):#选择来源
    """运行可选的 pre-boot 来源选择阶段。

    参数:
        选项: 基础镜像与可选 fixture 目录位置。
    返回:
        用户选定的有序 overlays。
    """
    if 选项 is None:#缺省
        选项={}#空
    扣住工作线程宿主boot()#先扣住
    镜像=选项.get('image') or 镜像文件名#镜像位置
    清单=选项.get('fixtureManifest') or 预览fixture清单文件#目录位置
    try:#选择
        覆盖层=选择预览源(清单)#用户选择
        return {'overlays':覆盖层}#返回
    except Exception as 原因:#失败
        boot就绪屏障()['reject'](原因)#结算失败
        raise#继续抛出

def 连接工作线程宿主(工作线程,选项=None):#连接宿主
    """连接已派生的宿主 worker 并完成 Cordis 前握手。

    参数:
        工作线程: 宿主 worker。
        选项: 基础镜像与 overlay 位置覆盖。
    返回:
        连接；把 loadBundle 交给壳入口的 boot 缝。
    """
    if 选项 is None:#缺省
        选项={}#空
    就绪=boot就绪屏障()#取屏障
    try:#握手
        隧道=工作线程隧道(工作线程)#建隧道
        镜像=选项.get('image') or 镜像文件名#镜像
        覆盖层=选项.get('overlays') or []#overlays
        隧道.初始化(镜像,[str(层) for 层 in 覆盖层])#开局init
        载荷=隧道.boot载荷()#等boot载荷
        全局=globals()#全局
        全局['__DSH_TRANSPORT__']={#安装传输全局
            'fetch':隧道.拉取,#隧道fetch
            'openStream':隧道.打开,#开流
            'loadBundle':隧道.加载束,#加载束
            'ownsHost':True,#页面拥有Host
        }#全局结束
        应用索引注入(载荷['injections'],隧道.加载束)#执行注入表
        就绪['resolve']()#结算就绪
        return {'worker':工作线程,'tunnel':隧道,'loadBundle':隧道.加载束}#返回连接
    except Exception as 原因:#握手失败
        就绪['reject'](原因)#结算失败
        raise#继续抛出
