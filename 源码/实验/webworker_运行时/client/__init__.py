from ....基础设施.js特性 import PromiseEX as 期约扩展#boot就绪期约与握手链
from ..镜像布局 import 镜像文件名
from ..fixture清单 import (
    预览fixture清单文件,
    预览fixture清单版本,
    解析预览fixture清单,
)
from .客户端 import 工作线程隧道
from .应用注入 import 应用索引注入
from .源选择器 import 选择预览源

__all__=[
    '工作线程隧道','应用索引注入','镜像文件名',
    '解析预览fixture清单','预览fixture清单文件','预览fixture清单版本',
    '选择工作线程宿主源','连接工作线程宿主',
]

def boot就绪屏障():
    '与客户端入口共享的 boot 就绪期约，握手成功时解决，失败时拒绝'
    全局=globals()
    键='__DSH_BOOT_READY__'
    if 键 not in 全局 or 全局[键] is None:
        全局[键]=期约扩展()
    return 全局[键]

def 扣住工作线程宿主boot():
    '在来源选择器等待用户输入之前安装页面 boot 屏障'
    boot就绪屏障()

def 选择工作线程宿主源(选项=None):
    """运行可选的 pre-boot 来源选择阶段。

    参数:
        选项: 基础镜像与可选 fixture 目录位置。
    返回:
        期约，兑现值是用户选定的有序 overlays
    """
    if 选项 is None:
        选项={}
    扣住工作线程宿主boot()
    if 'fixtureManifest' not in 选项: 清单=预览fixture清单文件#??默认清单，空串合法
    else: 清单=选项['fixtureManifest']
    def 包装覆盖层(覆盖层):#来源选择完成后调用
        '包装成来源选择结果'
        return {'overlays':覆盖层}
    def 拒绝就绪屏障(原因):#来源选择失败后调用
        '让 boot 屏障带着失败原因落定，再把原因交还调用方'
        boot就绪屏障().拒绝(原因)
        raise 原因
    try:
        选择期约=选择预览源(清单)
    except Exception as 原因:#选择预览源同步校验可能抛运行时错误，契约未定所以收不窄
        拒绝就绪屏障(原因)
    return 选择期约.然后(包装覆盖层,拒绝就绪屏障)

def 连接工作线程宿主(工作线程,选项=None):
    """连接已派生的宿主 worker 并完成 Cordis 前握手。

    参数:
        工作线程: 宿主 worker。
        选项: 基础镜像与 overlay 位置覆盖。
    返回:
        期约，兑现值是连接；把 loadBundle 交给壳入口的 boot 缝
    """
    if 选项 is None:
        选项={}
    就绪=boot就绪屏障()
    def 应用载荷(载荷):#boot 载荷取回后调用
        '安装传输全局、应用索引注入并让 boot 屏障落定'
        全局=globals()
        全局['__DSH_TRANSPORT__']={
            'fetch':隧道.拉取,
            'openStream':隧道.打开,
            'loadBundle':隧道.加载束,
            'ownsHost':True,
        }
        应用索引注入(载荷['injections'],隧道.加载束)
        就绪.解决()
        return {'worker':工作线程,'tunnel':隧道,'loadBundle':隧道.加载束}
    def 拒绝就绪屏障(原因):#握手任一步失败后调用
        '让 boot 屏障带着失败原因落定，再把原因交还调用方'
        就绪.拒绝(原因)
        raise 原因
    try:
        隧道=工作线程隧道(工作线程)
        if 'image' not in 选项: 镜像=镜像文件名#??默认镜像，空串合法
        else: 镜像=选项['image']
        if 'overlays' not in 选项: 覆盖层=[]#??空列表，空 overlays 合法
        else: 覆盖层=选项['overlays']
        隧道.初始化(镜像,[str(层) for 层 in 覆盖层])
        载荷期约=隧道.boot载荷()
    except Exception as 原因:#隧道初始化可能抛连接错误，契约未定所以收不窄
        拒绝就绪屏障(原因)
    return 载荷期约.然后(应用载荷).捕获(拒绝就绪屏障)
