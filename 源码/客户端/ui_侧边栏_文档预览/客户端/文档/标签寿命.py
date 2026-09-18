"""文档视图状态归属标签记录，正文隐藏时亦然。"""

__all__=['保留文档标签']#仅中文公开名

def 保留文档标签(上下文):
    """在标签关闭或插件拆除时释放保留的视图状态。返回登记回调。"""
    已保留={}#信号 → 拆除

    def 寿命():#插件寿命
        """拆除时全部 forget。"""
        def 拆除():#卸载
            """逐个 forget。"""
            for 忘 in list(已保留.values()):#快照
                忘()#忘
            已保留.clear()#清空
        return 拆除#拆除器
    上下文.副作用(寿命,'document-preview.tab-lifetime')#寿命

    def 登记(标签标识,信号,忘记标签):
        """接受标签、寿命信号与存储 forget。"""
        if getattr(信号,'已中止',False) or getattr(信号,'aborted',False):#已中止
            忘记标签(标签标识)#立刻忘
            return#停
        if 信号 in 已保留:#已登记
            return#共享
        def 忘():#中止回调
            """卸监听并 forget。"""
            if 信号 in 已保留:#仍在
                del 已保留[信号]#出表
            忘记标签(标签标识)#忘标签
        已保留[信号]=忘#记下
        if hasattr(信号,'addEventListener'):#AbortSignal
            信号.addEventListener('abort',忘,{'once':True})#一次
        elif hasattr(信号,'subscribe'):#事件
            信号.subscribe(忘)#订阅

    return 登记#回调
