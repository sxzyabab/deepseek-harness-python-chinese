import builtins#窗口选区
from .键图 import 登记作曲器键图#键图
from ..提交策略 import 解析提交模式#提交模式

__all__=[#公开面
    '揭示草稿选区','聚焦草稿编辑器','安装草稿滚轮','安装草稿文件选择器',
    '安装草稿键图','保持草稿焦点',
]

def 揭示草稿选区(滚动引用):
    """让草稿滚动口露出 DOM 选区。"""
    滚动=滚动引用['current']#滚动口
    if 滚动 is None:#无
        return#停
    if 滚动.scrollHeight<=滚动.clientHeight:#无需滚
        return#停
    选区=builtins.window.getSelection()#窗口选区
    if 选区 is None or 选区.rangeCount==0:#无范围
        return#停
    范围=选区.getRangeAt(0)#第一范围
    矩形=范围.getBoundingClientRect()#矩形
    if 矩形.height==0 and 矩形.width==0:#空行塌缩光标
        锚=选区.anchorNode#锚节点
        元素=锚 if 锚.是元素() is True else 锚.父元素()#行盒
        if 元素 is None:#无
            return#停
        矩形=元素.getBoundingClientRect()#行盒
    盒=滚动.getBoundingClientRect()#滚动盒
    if 矩形.bottom>盒.bottom:#偏下
        滚动.scrollTop+=矩形.bottom-盒.bottom#下滚
    elif 矩形.top<盒.top:#偏上
        滚动.scrollTop-=盒.top-矩形.top#上滚

def 聚焦草稿编辑器(编辑器,揭示选区):
    """聚焦借来的编辑器并露出恢复后的选区。"""
    根=编辑器.取根元素()#根
    if 根 is not None:#有根
        根.聚焦({'preventScroll':True})#不带动会话滚动
    编辑器.聚焦(揭示选区)#恢复选区后揭示

def 安装草稿滚轮(滚动引用):
    """草稿边缘的滚轮转给会话滚动口。"""
    元素=滚动引用['current']#滚动口
    if 元素 is None:#无
        return None#无拆除器
    def 滚轮(事件):
        """到顶/到底才转交。"""
        宿主=元素.closest('[data-conversation-scroll]')#会话滚动口
        if 宿主 is None or 事件['deltaY']==0:#无宿主或无位移
            return#停
        在顶=元素.scrollTop<=0#顶
        在底=元素.scrollTop+元素.clientHeight>=元素.scrollHeight-1#底
        向上=事件['deltaY']<0#向上
        if (向上 and not 在顶) or ((not 向上) and not 在底):#内部还能滚
            return#停
        事件.阻止默认()#占住
        宿主.scrollTop+=事件['deltaY']#转交
    元素.添加监听('wheel',滚轮,{'passive':False})#非被动才能 preventDefault
    def 拆除():
        """卸滚轮。"""
        元素.移除监听('wheel',滚轮)#卸
    return 拆除#拆除器

def 安装草稿文件选择器(键盘,门,文件输入引用):
    """经键盘面绑定本视图的文件对话框。"""
    def 可用():
        """门允许且输入还在。"""
        return 门['current']['canAcceptDrop'] is True and 文件输入引用['current'] is not None#可用
    def 打开():
        """点开原生文件框。"""
        输入=文件输入引用['current']#输入
        if 输入 is not None:#有
            输入.click()#打开
    return 键盘.bindFilePicker({'available':可用,'open':打开})#拆除器

def 安装草稿键图(编辑器,键盘,门):
    """把编辑器手势绑到视图守卫与会话操作。"""
    def 裁决(键,合成中):
        """菜单裁决。"""
        return 键盘.arbitrate(键,合成中)#裁决
    def 空格():
        """忙碌或锁定则放行。"""
        当前=门['current']#门
        if 当前['machineBusy'] is True or 当前['locked'] is True:#不可
            return False#放行
        return 键盘.space()#空格
    def 解散弹出():
        """关覆盖。"""
        键盘.dismissPopup()#关
    def 可提交():
        """未锁且机未忙。"""
        当前=门['current']#门
        return (not 当前['locked']) and (not 当前['machineBusy'])#可
    def 提交(加速):
        """空草稿加速回车改转向队列。"""
        当前=门['current']#门
        if 加速 is True and 当前['canSteerQueue'] is True:#转向队列
            键盘.steerQueue()#转向
            return#停
        if 当前['uploadsPending'] is True:#仍在上传
            当前['showToast'](当前['t']('file.stillUploading'))#提示
            return#停
        手势='accelerated' if 加速 is True else 'enter'#手势
        键盘.submit(解析提交模式(当前['busyEnter'],当前['running'],手势,当前['steeringAvailable']))#提交
    def 摄入文件(文件表):
        """交给门。"""
        门['current']['intakeFiles'](文件表)#摄入
    def 粘贴文本(文本):
        """忙碌或锁定则丢。"""
        当前=门['current']#门
        if 当前['machineBusy'] is True or 当前['locked'] is True:#不可
            return#停
        键盘.paste(文本)#粘贴
    return 登记作曲器键图(编辑器,{#键图
        'arbitrate':裁决,#裁决
        'space':空格,#空格
        'dismissPopup':解散弹出,#解散
        'canSubmit':可提交,#可提交
        'submit':提交,#提交
        'intakeFiles':摄入文件,#文件
        'pasteText':粘贴文本,#粘贴
    })#拆除器

def 保持草稿焦点(事件,编辑器):
    """工具栏按下不要把焦点带离草稿。"""
    事件.阻止默认()#占住
    if 编辑器 is None:#惰性视图
        return#停
    根=编辑器.取根元素()#根
    if 根 is not None:#有根
        根.聚焦({'preventScroll':True})#不滚会话
