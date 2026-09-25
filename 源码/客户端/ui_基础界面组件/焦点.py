"""自动聚焦约定：程序送焦时不画轮廓，直到键盘导航或失焦。
主题靠 data-dsh-automatic-focus 压掉 outline。
"""
from weakref import WeakKeyDictionary as 弱键字典#元素 → 释放器

__all__=['无轮廓聚焦']#仅中文公开名

释放表=弱键字典()#元素 → 解除自动焦点标记
导航键=frozenset(('Tab','ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Home','End'))#会恢复轮廓的导航键

def 无轮廓聚焦(元素,选项=None):
    """聚焦自动目标，键盘导航或 blur 前不显示焦点轮廓。
    元素为接收自动焦点的控件或容器；选项为浏览器 focus 选项。
    """
    旧=释放表.get(元素)#上一轮
    if 旧 is not None:#有旧会话
        旧()#拆掉
    def 释放():
        """解除标记并拆监听。"""
        元素.removeAttribute('data-dsh-automatic-focus')#去标记
        元素.removeEventListener('blur',释放)#卸 blur
        元素.removeEventListener('keydown',导航,True)#卸导航键
        释放表.pop(元素,None)#从表去掉
    def 导航(事件):
        """真导航键则恢复轮廓；合成与修饰键不算。"""
        if (not getattr(事件,'isComposing',False)
            and not getattr(事件,'ctrlKey',False)
            and not getattr(事件,'altKey',False)
            and not getattr(事件,'metaKey',False)
            and getattr(事件,'key',None) in 导航键):#真导航
            释放()#释放
    释放表[元素]=释放#登记
    元素.setAttribute('data-dsh-automatic-focus','')#挂标记
    元素.addEventListener('blur',释放)#失焦即释放
    元素.addEventListener('keydown',导航,True)#捕获导航键
    if 选项 is None:#无选项
        元素.focus()#聚焦
    else:#有选项
        元素.focus(选项)#聚焦
    匹配=getattr(元素,'matches',None)#matches
    if callable(匹配) and not 匹配(':focus'):#未真正拿到焦点
        释放()#清残留
