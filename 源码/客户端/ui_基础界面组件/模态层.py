"""共享模态键盘归属与焦点生命周期：栈顶层独占 Escape / Tab，
关闭后把焦点还回打开前的控件（或下一层模态）。
"""
from weakref import WeakKeyDictionary as 弱键字典#文档 → 模态栈
from .键盘合成 import 观察合成#IME 守卫
from .焦点 import 无轮廓聚焦#无轮廓自动聚焦

__all__=['模态选择器','关栈顶模态','是否在模态后','使用模态层']#仅中文公开名

模态选择器='[role="dialog"][aria-modal="true"], [role="menu"]'#对话框与菜单
层表=弱键字典()#文档 → [{element, close}, ...]
可聚焦='button:not(:disabled), input:not(:disabled), textarea:not(:disabled), select:not(:disabled), a[href], [tabindex="0"]'#可聚焦控件

def 关栈顶模态(文档):
    """用当前 onClose 请求关闭已登记的前景模态。
    未登记对话框会挡住后方模态的关闭。
    """
    栈=层表.get(文档)#已登记栈
    if 栈 is None or len(栈)==0:#无栈
        return#停
    顶=栈[-1]#栈顶
    前景表=文档.querySelectorAll(模态选择器)#全部匹配
    前景=前景表[len(前景表)-1] if len(前景表)>0 else None#DOM 前景
    if 前景 is 顶['element']:#一致才关
        顶['close']()#关

def 是否在模态后(锚点):
    """锚点是否在当前模态后方，因而必须让出键盘输入。
    锚点为拥有输入处理器的本地控件；另有模态占前景时为 True。
    """
    if 锚点 is None:#无锚点
        return False#不算后方
    栈=层表.get(锚点.ownerDocument)#该文档栈
    if 栈 is None or len(栈)==0:#无栈
        return False#否
    顶=栈[-1]#栈顶
    return not 顶['element'].contains(锚点)#有栈顶且锚点不在其内

def 使用模态层(对话框,打开,关闭):
    """仅给栈顶模态 Escape 与 Tab 归属，关闭后恢复先前焦点。
    对话框为已挂载元素；打开为本层是否激活；关闭为栈顶 Escape 或应用层关闭。
    返回拆除器；未开或未挂载时返回空拆除。
    """
    if not 打开 or 对话框 is None:#未开或未挂载
        def 空拆():
            """无可拆。"""
            return None#无事
        return 空拆#空拆除
    文档=对话框.ownerDocument#所属文档
    合成=观察合成(文档)#IME 守卫
    先前=文档.activeElement#打开前焦点
    栈=层表.get(文档)#该文档栈
    if 栈 is None:#尚无
        栈=[]#新建
        层表[文档]=栈#登记
    关闭箱={'current':关闭}#最新关闭，避免抖动
    def 调关闭():
        """调最新关闭。"""
        关闭箱['current']()#关
    层={'element':对话框,'close':调关闭}#本层登记
    栈.append(层)#入栈
    初焦=对话框.querySelector('[data-modal-autofocus]')#显式 autofocus
    if 初焦 is None:#无显式
        初焦=对话框.querySelector(可聚焦)#第一个可聚焦
    if 初焦 is None:#仍无
        初焦=对话框#对话框自身
    活跃=文档.activeElement#当前焦点
    if 活跃 is None or not 对话框.contains(活跃):#层外才自动聚焦
        无轮廓聚焦(初焦)#无轮廓
    def 按键(事件):
        """仅栈顶层处理 Escape / Tab；合成与修饰键直接放过。"""
        if 栈[-1] is not 层:#非本层
            return#放行
        if getattr(事件,'defaultPrevented',False) or 合成['guards'](事件):#已处理或 IME
            return#放行
        if getattr(事件,'ctrlKey',False) or getattr(事件,'altKey',False) or getattr(事件,'metaKey',False):#修饰
            return#放行
        键=getattr(事件,'key',None)#键名
        if 键=='Escape' and not getattr(事件,'shiftKey',False):#Escape 关层
            事件.preventDefault()#吞掉
            if not getattr(事件,'repeat',False):#长按不连关
                关闭箱['current']()#关
            return#止
        if 键!='Tab':#其余键不拦
            return#放行
        活跃元素=文档.activeElement#当前
        if 活跃元素 is not None and 活跃元素.closest('[role="menu"]') is not None:#菜单自管
            return#放行
        项表=[]#可聚焦项
        for 项 in 对话框.querySelectorAll(可聚焦):#全可聚焦
            if 项.closest('[inert], [hidden]') is None:#非 inert/hidden
                项表.append(项)#收下
        首=项表[0] if len(项表)>0 else 对话框#环起点
        尾=项表[-1] if len(项表)>0 else 对话框#环终点
        移键=getattr(事件,'shiftKey',False)#Shift+Tab
        在边=(活跃元素 is 首) if 移键 else (活跃元素 is 尾)#是否在环边
        if 活跃元素 is 对话框 or (活跃元素 is not None and not 对话框.contains(活跃元素)) or 在边:#须折回
            事件.preventDefault()#阻止逃逸
            目标=尾 if 移键 else 首#反向或正向
            目标.focus()#折回
    文档.addEventListener('keydown',按键)#冒泡登记
    def 拆除():
        """出栈并可能归还焦点。"""
        关闭箱['current']=关闭#刷新最新
        合成['dispose']()#卸 IME
        是顶=len(栈)>0 and 栈[-1] is 层#出栈前是否栈顶
        if 层 in 栈:#仍在
            栈.remove(层)#出栈
        文档.removeEventListener('keydown',按键)#卸键盘
        if len(栈)==0:#空栈
            层表.pop(文档,None)#清 WeakMap
        if 是顶:#关掉的是栈顶才归还
            目标=None#归还目标
            if 先前 is not None and getattr(先前,'isConnected',False):#原焦点仍连通
                目标=先前#优先原焦点
            elif len(栈)>0:#有下一层
                目标=栈[-1]['element']#下一层
            if 目标 is not None:#有目标
                无轮廓聚焦(目标)#无轮廓归还
    return 拆除#拆除器
