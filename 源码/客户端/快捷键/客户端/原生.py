'Desktop 手势使用实时焦点、模态状态和已验证的嵌入所有权'
import pywebbridge#页面上的未定义
from ...ui_基础界面组件.模态层 import 模态选择器#对话框与菜单

__all__=['安装原生键盘']

未定义=pywebbridge.undefined#属性缺失
可编辑选择='input, textarea, select, [contenteditable="true"], [contenteditable=""]'#可编辑
侧栏网页视图='webview[data-sidebar-browser-frame]'#侧栏 webview
侧栏框架='iframe[data-sidebar-browser-frame], iframe[data-html-preview]'#侧栏 iframe

def 安装原生键盘(窗口,键盘,注册表,取快照,重置=None):
    '把原生菜单、主 frame 和嵌入 frame 的输入接到共享命令注册表'
    文档=窗口.document#文档

    def 是内嵌框架(节点):
        '是否 iframe。标签名是能从页面读回的字符串'
        if 节点 is None or 节点 is 未定义:#空
            return False#否
        标签=节点.tagName#标签
        if 标签 is None or 标签 is 未定义:#没有标签
            return False#否
        return str(标签).upper()=='IFRAME'#内嵌框架

    def 手势自(输入):
        '从已验证输入取出分发用手势'
        手势={
            'code':输入['code'],
            'control':输入['control'],
            'alt':输入['alt'],
            'shift':输入['shift'],
            'meta':输入['meta'],
            'repeat':输入['repeat'],
            'composing':False,
            'defaultPrevented':False,
        }
        if 输入.get('secondCode') is not None and 输入.get('secondCode') is not 未定义:#有次码
            手势['secondCode']=输入['secondCode']#写入
        return 手势#手势

    def 空消费():
        '原生侧已经消费，这里不再阻止默认'
        return None#无事

    def 处理(输入):
        '一条已验证的原生输入'
        if 输入['revision']!=取快照()['revision']:#修订不符
            return#丢弃
        if 重置 is not None:#清固定序列
            重置()#重置
        目标=文档.activeElement#焦点
        while 目标 is not None and 目标 is not 未定义:#深入 shadow
            影=目标.shadowRoot#shadow
            if 影 is None or 影 is 未定义:#无影
                break#止
            内焦=影.activeElement#影内焦点
            if 内焦 is None or 内焦 is 未定义:#无
                break#止
            if 目标.matches(侧栏网页视图):#停在 webview
                break#止
            目标=内焦#深入
        对话框=文档.querySelectorAll(模态选择器)#模态
        长度=对话框.length#数量
        顶=None if 长度==0 else 对话框[长度-1]#最前
        if 目标 is not None and 目标 is not 未定义 and 目标.closest('.xterm'):#终端
            区域='terminal'#终端
        elif 目标 is not None and 目标 is not 未定义 and 目标.matches(可编辑选择):#可编辑
            区域='editable'#可编辑
        else:#页面
            区域='page'#页面
        if 顶 is None:#无模态
            模态=None#空
        else:#有模态
            声明=顶.dataset.shortcutModal#声明
            模态='other' if 声明 is 未定义 or 声明 is None else 声明#未声明归其他
        上下文={'target':目标,'region':区域,'modal':模态}#上下文
        种类=输入['kind']#种类
        if 种类=='menu':#菜单
            注册表.invoke(输入['commandId'],上下文)#调用
            return#止
        if 种类=='keyboard':#主 frame 键盘
            注册表.dispatch(手势自(输入),上下文,空消费)#分发
            return#止
        if 种类=='webview':#嵌入网页
            if 目标 is None or 目标 is 未定义:#无目标
                return#丢弃
            if 目标.matches(侧栏网页视图) is not True or not 目标.isConnected:#不是还连着的侧栏 webview
                return#丢弃
            if 输入['frameName']=='' or 目标.getAttribute('name')!=输入['frameName']:#身份不符
                return#丢弃
            注册表.dispatch(手势自(输入),{**上下文,'source':'webview'},空消费)#分发
            return#止
        if not 是内嵌框架(目标) or not 目标.isConnected:#不是还连着的 iframe
            return#丢弃
        if not 目标.matches(侧栏框架):#不是侧栏或预览帧
            return#丢弃
        if 输入['frameName']=='' or 目标.name!=输入['frameName']:#身份不符
            return#丢弃
        注册表.dispatch(手势自(输入),{**上下文,'source':'iframe'},空消费)#分发

    return 键盘.subscribe(处理)#订阅并返回拆除器
