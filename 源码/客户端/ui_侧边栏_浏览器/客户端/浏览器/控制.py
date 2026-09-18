import threading#中止监听线程
from .帧 import 内嵌帧实现#iframe 实现
from .导航 import 浏览器导航#导航状态机
from .地址 import 解析浏览器地址#地址解析

__all__=['浏览器控制','创建浏览器控制表']#仅中文公开名

class 浏览器控制:#每标签控制器
    """拥有一浏览器标签的 URL 状态、加载寿命与四条导航命令。"""
    def __init__(自身,选项):
        """选项含标签标识、持久化写者、应用源与寿命信号。"""
        自身.选项=选项#依赖
        初始=选项['initial'] if 'initial' in 选项 else None#持久化初态
        自身.导航=浏览器导航(初始)#导航机
        def 沙箱变更(_沙箱):
            """沙箱翻转后重载受控目标。"""
            自身.刷新()#刷新
        自身.帧=内嵌帧实现(沙箱变更,自身._帧已加载)#帧
        自身.已拆除=False#拆除标志
        信号=选项['signal']#中止信号 Event
        if 信号 is not None:#有信号
            def 监视():#等中止
                信号.wait()#阻塞
                自身._拆除()#拆除
            threading.Thread(target=监视,daemon=True).start()#守护

    def 加载地址(自身,值):
        """校验并加载地址；同址则刷新。"""
        if 自身.已拆除:#已死
            return#停
        解析=解析浏览器地址(值,自身.选项['applicationOrigin'])#解析
        if not 解析['ok']:#拒绝
            自身.导航.地址失败(解析['reason'])#失败
            自身._发布()#发布
            return#停
        当前=浏览器导航.当前(自身.导航.快照)#当前
        if 当前 is not None and 当前['url']==解析['target']['url']:#同址
            自身.刷新()#刷新
            return#停
        自身._开始(自身.导航.导航(解析['target']))#导航

    def 后退(自身):
        """退到前一条应用已知地址。"""
        if 自身.已拆除:#已死
            return#停
        请求=自身.导航.后退()#后退
        if 请求 is not None:#有请求
            自身._开始(请求)#开始

    def 前进(自身):
        """进到后一条应用已知地址。"""
        if 自身.已拆除:#已死
            return#停
        请求=自身.导航.前进()#前进
        if 请求 is not None:#有请求
            自身._开始(请求)#开始

    def 刷新(自身):
        """重载最后一条应用已知地址，不增历史。"""
        if 自身.已拆除:#已死
            return#停
        请求=自身.导航.刷新()#刷新
        if 请求 is not None:#有请求
            自身._开始(请求)#开始

    def _开始(自身,请求):
        """发布并装上准备文档。"""
        自身._发布()#发布导航
        自身.帧.清文档()#清旧
        自身.帧.设文档({#新文档
            'target':请求['target'],#目标
            'src':请求['target']['url'],#源
            'revision':请求['revision'],#修订
        })#设文档

    def _帧已加载(自身,修订):
        """帧加载回调。"""
        if 自身.已拆除:#已死
            return#停
        先前=自身.导航.快照#先前
        自身.导航.帧已加载(修订)#推进
        if 自身.导航.快照 is not 先前:#有变
            自身._发布()#发布

    def _发布(自身):
        """把导航快照写入存储。"""
        自身.选项['actions']['replace'](自身.选项['tabId'],自身.导航.快照)#替换

    def _拆除(自身):
        """拆除并清文档。"""
        自身.已拆除=True#死
        自身.帧.清文档()#清

def 创建浏览器控制表(动作):
    """把浏览器控制器绑到一会话及其持久化写者。返回注入面。"""
    表={}#标签标识 → {signal, controller}

    def 取控(标签标识):
        """取存活控制器。"""
        项=表[标签标识] if 标签标识 in 表 else None#项
        return None if 项 is None else 项['controller']#控制器

    def 挂载(标签标识,信号,应用源,初始=None):
        """挂载或复用本 occurrence 的控制器。"""
        持有=表[标签标识] if 标签标识 in 表 else None#已有
        if 持有 is not None and 持有['signal'] is 信号:#同信号
            return#复用
        选项={'tabId':标签标识,'signal':信号,'applicationOrigin':应用源,'actions':动作}#选项
        if 初始 is not None:#有初态
            选项['initial']=初始#初态
        创建=浏览器控制(选项)#新建
        表[标签标识]={'signal':信号,'controller':创建}#登记
        if 信号 is not None:#有信号
            def 清理():#中止清理
                信号.wait()#等
                现=表[标签标识] if 标签标识 in 表 else None#现
                if 现 is None or 现['controller'] is not 创建:#已换
                    return#停
                del 表[标签标识]#删
                动作['forget'](标签标识)#遗忘
            threading.Thread(target=清理,daemon=True).start()#守护

    def 取帧(键):
        """带键席位要的帧可观察源。"""
        控=取控(键)#控制器
        return None if 控 is None else 控.帧#帧

    def 加载地址命令(标签,值):
        """校验并加载。"""
        控=取控(标签)#控制器
        if 控 is not None:控.加载地址(值)#加载

    def 后退命令(标签):
        """后退。"""
        控=取控(标签)#控制器
        if 控 is not None:控.后退()#退

    def 前进命令(标签):
        """前进。"""
        控=取控(标签)#控制器
        if 控 is not None:控.前进()#进

    def 刷新命令(标签):
        """刷新。"""
        控=取控(标签)#控制器
        if 控 is not None:控.刷新()#刷

    def 切换沙箱命令(标签):
        """切换沙箱。"""
        控=取控(标签)#控制器
        if 控 is not None:控.帧.切换沙箱()#沙箱

    def 报告已加载命令(标签,修订):
        """报告已加载。"""
        控=取控(标签)#控制器
        if 控 is not None:控.帧.报告已加载(修订)#已加载

    def 报告加载失败命令(标签,修订):
        """报告加载失败。"""
        控=取控(标签)#控制器
        if 控 is not None:控.帧.报告加载失败(修订)#失败

    return {#注入面
        'keyedHooks':{'browserFrame':取帧},#带键帧钩
        'mount':挂载,#挂载
        'loadUrl':加载地址命令,#加载
        'goBack':后退命令,#后退
        'goForward':前进命令,#前进
        'reload':刷新命令,#刷新
        'toggleSandbox':切换沙箱命令,#沙箱
        'reportLoaded':报告已加载命令,#已加载
        'reportLoadFailed':报告加载失败命令,#失败
    }#面结束
