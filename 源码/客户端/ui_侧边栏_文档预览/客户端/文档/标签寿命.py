"""文档视图状态归属标签记录，正文隐藏时亦然。"""
from .....工具.超时 import 等待中止#中止等待
import threading#后台监视
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
        if 信号 is not None and 信号.is_set():#已中止
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
        if 信号 is not None:#有信号
            def 监视():#等中止
                """置位后 forget。"""
                等待中止(信号)#等置位
                忘()#忘标签
            threading.Thread(target=监视,daemon=True).start()#后台监视

    return 登记#回调
