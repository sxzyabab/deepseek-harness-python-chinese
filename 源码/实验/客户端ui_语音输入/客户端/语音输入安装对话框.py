'语音激活和识别不可用时共用的模态'
from ....客户端.模块.客户端.通告 import 取握手窗口
from ....客户端.ui_基础界面组件.按钮 import 按钮#稍后、前往
from ....客户端.ui_基础界面组件.模态 import 模态#对话框

__all__=['语音输入安装对话框']#引导和麦克风点击共用


def 取窗口(属性):
    '调用方窗口优先，否则用当前页'
    if isinstance(属性,dict) and 属性.get('window') is not None:#份额里带了窗口
        return 属性['window']#调用方窗口
    return 取握手窗口()#当前页


def 画按钮(窗口,属性):
    '画出按钮，再补上原子按钮没写上的属性'
    节点=按钮(属性).渲染()#按钮节点
    if 属性.get('data-modal-autofocus') is True:#打开后应聚焦
        节点.setAttribute('data-modal-autofocus','true')#交给模态
    return 节点#节点


class 语音输入安装对话框:
    '把激活或麦克风点击导向已有的插件详情。从不启动准备或录音'
    def __init__(自身,属性=None):
        '记下可见性、是否需要安装和导航回调'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#模态节点
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的可见性和回调'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 拆除(自身):
        '从页面拿掉模态'
        if 自身.根 is not None:#还在
            自身.根.remove()#拆掉
            自身.根=None#记下

    def 渲染(自身):
        '需要安装时用安装文案，否则说明尚未就绪'
        窗口=取窗口(自身.属性)#窗口
        打开=自身.属性.get('open') is True#是否打开
        if 打开 is False:#关上
            自身.拆除()#不留空罩
            return None#没有节点
        要安装=自身.属性.get('needsInstallation') is True#本地模型还没准备
        if 要安装:#首次安装
            标题='使用语音输入前需要安装'#中文表
            正文='语音输入插件已开启。首次使用需要在本机下载并准备识别模型，请前往插件详情页查看空间、内存和时间说明，再开始安装。'#中文表
            前往文='前往安装'#中文表
        else:#识别还不可用
            标题='语音识别尚未就绪'#中文表
            正文='请前往语音插件详情页查看识别服务状态、准备进度或错误信息'#中文表
            前往文='前往语音插件设置'#中文表
        文档=窗口.document#文档
        段=文档.createElement('p')#说明
        段.textContent=正文#正文
        稍后=画按钮(窗口,{#次按钮
            'window':窗口,#窗口
            'variant':'ghost',#幽灵
            'children':'稍后',#中文表
            'onClick':自身.属性.get('onDismiss'),#关闭
        })
        前往=画按钮(窗口,{#主按钮
            'window':窗口,#窗口
            'variant':'primary',#主操作
            'children':前往文,#安装或详情
            'onClick':自身.属性.get('onOpenDetails'),#打开详情
            'data-modal-autofocus':True,#打开后聚焦
        })
        旧=自身.根#上一份
        父=None#挂载点
        if 旧 is not None:#先记住位置
            父=旧.parentNode#父节点
            旧.remove()#拆掉
        根=模态({#受控模态
            'window':窗口,#窗口
            'open':True,#已经确认要开
            'title':标题,#标题
            'closeLabel':'取消',#中文表
            'onClose':自身.属性.get('onDismiss'),#关闭
            'footer':[稍后,前往],#两个按钮
            'children':段,#说明
        }).渲染()#罩层
        自身.根=根#留下
        if 父 is not None and 根 is not None and 根.parentNode is not 父:#挂回原处
            父.appendChild(根)#挂上
        return 根#节点

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画
