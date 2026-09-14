from concurrent.futures import Future as 原生结果#单次操作结果
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

class 操作任务:
    """本文件内单次操作结果，只留兑现、拒绝、等待。"""
    def __init__(自身):
        """构造未决任务。"""
        自身._结果=原生结果()#底层 Future

    def 兑现(自身,值=None):
        """成功结算。"""
        if not 自身._结果.done():#尚未结算
            自身._结果.set_result(值)#写入结果
        return 值#返回兑现值

    def 拒绝(自身,错误):
        """失败结算。"""
        if not 自身._结果.done():#尚未结算
            if isinstance(错误,BaseException):#已是异常
                自身._结果.set_exception(错误)#原样拒绝
            else:#非异常
                自身._结果.set_exception(Exception(str(错误)))#包装拒绝

    def 等待(自身,超时=None):
        """阻塞等到结算。"""
        return 自身._结果.result(timeout=超时)#取结果或抛错

def boot就绪屏障():#获取或创建屏障
    """与客户端入口共享的 boot 就绪任务。"""
    全局=globals()#全局
    键='__DSH_BOOT_READY__'#共享键
    if 键 not in 全局 or 全局[键] is None:#惰性创建
        全局[键]=操作任务()#直接存任务
    return 全局[键]#返回任务

def 扣住工作线程宿主boot():#扣住boot
    """在来源选择器等待用户输入之前安装页面 boot 屏障。"""
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
    镜像=选项.get('image')#镜像位置
    if 镜像 is None: 镜像=镜像文件名#??默认镜像，空串合法
    清单=选项.get('fixtureManifest')#fixture 清单
    if 清单 is None: 清单=预览fixture清单文件#??默认清单，空串合法
    try:#选择
        覆盖层=选择预览源(清单)#用户选择
        return {'overlays':覆盖层}#返回
    except Exception as 原因:#选择预览源可能抛 IO/解析/UI 错误，契约未定所以收不窄
        boot就绪屏障().拒绝(原因)#结算失败
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
        镜像=选项.get('image')#镜像
        if 镜像 is None: 镜像=镜像文件名#??默认镜像，空串合法
        覆盖层=选项.get('overlays')#overlays
        if 覆盖层 is None: 覆盖层=[]#??空列表，空 overlays 合法
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
        就绪.兑现()#结算就绪
        return {'worker':工作线程,'tunnel':隧道,'loadBundle':隧道.加载束}#返回连接
    except Exception as 原因:#隧道握手可能抛连接/解码/注入错误，契约未定所以收不窄
        就绪.拒绝(原因)#结算失败
        raise#继续抛出
