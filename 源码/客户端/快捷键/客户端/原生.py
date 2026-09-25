"""Desktop 手势使用实时焦点、模态状态与已验证嵌入所有权。"""
from .dom import 模态选择器#模态选择器

__all__=['安装原生键盘']#仅中文公开名

可编辑选择='input, textarea, select, [contenteditable="true"], [contenteditable=""]'#可编辑
侧栏网页视图='webview[data-sidebar-browser-frame]'#侧栏 webview
侧栏框架='iframe[data-sidebar-browser-frame], iframe[data-html-preview]'#侧栏 iframe

def 安装原生键盘(窗口,键盘,注册表,取快照,重置=None):
    """把原生菜单、主 frame 与嵌入 frame 输入接到共享命令注册表。"""
    def 处理(输入):
        """一条已验证原生输入。"""
        if 输入['revision']!=取快照()['revision']:#修订不符
            return#丢弃
        if 重置 is not None:#清固定序列
            重置()#重置
        目标=窗口.document.activeElement#焦点
        while True:#深入 shadow
            if 目标 is None:#无
                break#止
            影=getattr(目标,'shadowRoot',None)#shadow
            if 影 is None:#无影
                break#止
            内焦=getattr(影,'activeElement',None)#影内焦点
            if 内焦 is None:#无
                break#止
            if callable(getattr(目标,'matches',None)) and 目标.matches(侧栏网页视图):#停在 webview
                break#止
            目标=内焦#深入
        对话框=窗口.document.querySelectorAll(模态选择器)#模态
        顶=对话框[len(对话框)-1] if len(对话框)>0 else None#最前
        if 目标 is not None and callable(getattr(目标,'closest',None)) and 目标.closest('.xterm'):#终端
            区域='terminal'#终端
        elif 目标 is not None and callable(getattr(目标,'matches',None)) and 目标.matches(可编辑选择):#可编辑
            区域='editable'#可编辑
        else:#页面
            区域='page'#页面
        if 顶 is None:#无模态
            模态=None#空
        else:#有
            数据=getattr(顶,'dataset',None)#dataset
            声明=getattr(数据,'shortcutModal',None) if 数据 is not None else None#声明
            模态=声明 if 声明 is not None else 'other'#其他
        上下文={'target':目标,'region':区域,'modal':模态}#上下文
        种类=输入['kind']#种类
        if 种类=='menu':#菜单
            注册表.invoke(输入['commandId'],上下文)#调用
            return#止
        手势={#键盘类共用手势
            'code':输入['code'],
            'control':输入['control'],
            'alt':输入['alt'],
            'shift':输入['shift'],
            'meta':输入['meta'],
            'repeat':输入['repeat'],
            'composing':False,
            'defaultPrevented':False,
        }#手势
        if 输入.get('secondCode') is not None:#次码
            手势['secondCode']=输入['secondCode']#写入
        def 空消费():
            """原生侧已消费。"""
            return None#无事
        if 种类=='keyboard':#主 frame 键盘
            注册表.dispatch(手势,上下文,空消费)#分发
            return#止
        #渲染进程焦点与嵌入身份可能在 preload 校验后变化
        if 种类=='webview':#webview
            if 目标 is None or not callable(getattr(目标,'matches',None)):#无目标
                return#丢弃
            if 目标.matches(侧栏网页视图) is not True:#非侧栏
                return#丢弃
            if not 目标.isConnected:#已卸
                return#丢弃
            if 输入['frameName']=='' or 目标.getAttribute('name')!=输入['frameName']:#身份不符
                return#丢弃
            注册表.dispatch(手势,{**上下文,'source':'webview'},空消费)#分发
            return#止
        #iframe
        if 目标 is None or 目标.__class__.__name__!='HTMLIFrameElement':#非 iframe
            #duck：有 tagName=='IFRAME'
            标签=getattr(目标,'tagName',None)#标签
            if 标签 is None or str(标签).upper()!='IFRAME':#仍非
                return#丢弃
        if not 目标.isConnected:#已卸
            return#丢弃
        if not callable(getattr(目标,'matches',None)) or not 目标.matches(侧栏框架):#非侧栏帧
            return#丢弃
        if 输入['frameName']=='' or getattr(目标,'name',None)!=输入['frameName']:#身份
            return#丢弃
        注册表.dispatch(手势,{**上下文,'source':'iframe'},空消费)#分发
    return 键盘.subscribe(处理)#订阅并返回拆除器
