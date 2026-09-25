"""IME 合成生命周期：本地键盘处理器要挡住合成中与合成刚结束那一记 keydown。
compositionend 后引擎仍可能立刻再派关闭键；刚结束把那一记也算进守卫，直到 keyup 或窗口 blur。
"""
__all__=['观察合成']#仅中文公开名

def 观察合成(文档):
    """观察合成直至关闭键释放或被消费。
    文档为其输入事件归属调用方的文档。
    返回含 guards / dispose 的守卫对象。
    """
    组合中=False#compositionstart～end 之间
    刚结束=False#刚 compositionend，等关闭键或 keyup
    def 开始():
        """进入合成。"""
        nonlocal 组合中#写
        组合中=True#开
    def 结束():
        """结束合成，并武装关闭键守卫。"""
        nonlocal 组合中,刚结束#写
        组合中=False#关
        刚结束=True#刚结束
    def 释放():
        """keyup 后关闭键窗口结束。"""
        nonlocal 刚结束#写
        刚结束=False#清
    def 失焦():
        """窗口失焦时两端状态一并清掉。"""
        nonlocal 组合中,刚结束#写
        组合中=False#关
        刚结束=False#清
    文档.addEventListener('compositionstart',开始,True)#捕获 start
    文档.addEventListener('compositionend',结束,True)#捕获 end
    文档.addEventListener('keyup',释放,True)#捕获 keyup
    视口=getattr(文档,'defaultView',None)#窗口
    if 视口 is not None:#有
        视口.addEventListener('blur',失焦)#窗 blur
    def 守卫(事件):
        """当前键是否仍属合成或刚结束的关闭键；读后清一次性刚结束。"""
        nonlocal 刚结束#写
        键码=getattr(事件,'keyCode',None)#旧键码 IME 229
        挡住=组合中 or 刚结束 or getattr(事件,'isComposing',False) or 键码==229#合成中 / 关闭键 / 229
        刚结束=False#关闭键窗口只拦一记
        return 挡住#是否应忽略
    def 拆除():
        """卸全部监听。"""
        文档.removeEventListener('compositionstart',开始,True)#卸 start
        文档.removeEventListener('compositionend',结束,True)#卸 end
        文档.removeEventListener('keyup',释放,True)#卸 keyup
        if 视口 is not None:#有窗
            视口.removeEventListener('blur',失焦)#卸 blur
    return {'guards':守卫,'dispose':拆除}#守卫与拆除
