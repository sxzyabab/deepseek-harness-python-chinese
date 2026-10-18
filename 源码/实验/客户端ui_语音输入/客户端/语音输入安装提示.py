'组合包激活后的安装引导。只负责打开详情，不开始下载'
from ....客户端.模块.客户端.通告 import 取握手窗口
from .语音输入安装对话框 import 语音输入安装对话框#共用模态

__all__=['语音输入安装提示']#激活槽


def 取(对象,键,默认=None):
    '字典用键，对象用同名属性'
    if isinstance(对象,dict):#字典
        return 对象[键] if 键 in 对象 else 默认#键
    return getattr(对象,键,默认)#属性


def 全选(值):
    '选择整份就绪快照'
    return 值#原样


def 取窗口(属性):
    '调用方窗口优先，否则用当前页'
    if isinstance(属性,dict) and 属性.get('window') is not None:#份额里带了窗口
        return 属性['window']#调用方窗口
    return 取握手窗口()#当前页


class 语音输入安装提示:
    '所选本地识别器还要准备时，才显示安装引导'
    def __init__(自身,属性=None):
        '记下导航回调，并订上就绪'
        自身.属性=属性 if isinstance(属性,dict) else {}#绘制属性
        自身.根=None#模态节点
        自身.对话框=语音输入安装对话框({'window':取窗口(自身.属性),'open':False})#共用模态
        自身.退订=[]#就绪订阅
        自身.已关阶段=None#避免同一次阶段反复关闭
        自身.已关需要=None#同上
        钩=自身.属性.get('useSpeechReadiness')#就绪钩子
        if callable(钩) and hasattr(钩,'_subscribe'):#能订
            自身.退订.append(钩._subscribe(自身.源变了))#就绪变了就重画
        自身.渲染()#构造时画出

    def 更新(自身,属性):
        '换成新的回调'
        自身.属性=属性 if isinstance(属性,dict) else {}#最新

    def 源变了(自身):
        '就绪变了就重画'
        自身.渲染()#重画

    def 拆除(自身):
        '退订并拆掉模态'
        for 退 in 自身.退订:#逐个
            if callable(退):#是函数
                退()#退订
        自身.退订=[]#清空
        自身.对话框.拆除()#拆模态
        自身.根=None#记下

    def 找提供方(自身,目录):
        '按当前选择找出提供方'
        if isinstance(目录,dict) is False:#没有目录
            return None#没有
        标识=取(目录.get('selection'),'providerId')#选中的 id
        列表=目录.get('providers')#提供方
        if isinstance(列表,list) is False:#不是列表
            return None#没有
        for 项 in 列表:#逐个
            if 取(项,'id')==标识:#就是这一个
                return 项#找到
        return None#没有

    def 渲染(自身):
        '检查完成且不需要安装时关掉。需要安装才打开模态'
        钩=自身.属性.get('useSpeechReadiness')#就绪钩子
        就绪=钩(全选) if callable(钩) else {'catalog':None,'connected':False,'error':None}#快照
        if isinstance(就绪,dict) is False:#不是字典
            就绪={'catalog':None,'connected':False,'error':None}#空
        提供方=自身.找提供方(就绪.get('catalog'))#所选提供方
        阶段=None#还没连上就不当成某个阶段
        if 就绪.get('connected') is True and 提供方 is not None:#已经连上
            阶段=取(取(提供方,'preparation'),'phase')#准备阶段
        需要=阶段=='unprepared' and 取(提供方,'location')=='host-local'#本地且未准备
        if 阶段 is not None and 阶段!='checking' and 需要 is False:#不用安装
            if 自身.已关阶段!=阶段 or 自身.已关需要!=需要:#这一状态还没关过
                自身.已关阶段=阶段#记下
                自身.已关需要=需要#记下
                关闭=自身.属性.get('onDismiss')#激活槽的关闭
                if callable(关闭):#有回调
                    关闭()#关掉激活提示
        窗口=取窗口(自身.属性)#窗口
        自身.对话框.更新({#交给共用模态
            'window':窗口,#窗口
            'open':需要,#仅需要安装时打开
            'needsInstallation':True,#这是安装引导
            'onDismiss':自身.属性.get('onDismiss'),#稍后
            'onOpenDetails':自身.属性.get('onOpenDetails'),#前往详情
        })
        自身.根=自身.对话框.渲染()#模态或空
        return 自身.根#节点

    def __call__(自身,属性=None):
        '宿主再次绘制时重画'
        if 属性 is not None:#有新份额
            自身.更新(属性)#换上
        return 自身.渲染()#重画
