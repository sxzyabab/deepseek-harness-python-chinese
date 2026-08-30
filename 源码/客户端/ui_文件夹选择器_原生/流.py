"""原生挑选占用者（包内；客户端表面只暴露 Loader 导出）。

对齐上游 `ui-directory-picker-native/src/client/flow.ts`。公开面仅中文名。
无渲染流占用者：每次 open 上升沿恰好跑一次挑选并报告恰好一次结果。
"""
import threading#后台观察挑选结果

__all__=['原生目录流','原生流注入面']#仅中文公开名

class 原生流注入面(dict):#注入面映射形状
    """本流驱动的线上调用。键：pick。"""

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

class 原生目录流:#无渲染：上升沿挑一次目录
    """无渲染流占用者：open 上升沿武装一次挑选；主人撤回 open 会重新武装。"""
    def __init__(自身,属性):#按合成 props 构造
        """记下主人对话与注入的 pick 调用。"""
        自身.属性=属性#合成 props
        自身.已武装=False#本轮 open 是否已武装过挑选
        自身.存活=True#本实例是否仍挂载
        自身.刷新打开()#首次同步 open 边沿

    def 更新(自身,属性):#props 变更
        """刷新主人处理函数并按 open 边沿武装。"""
        自身.属性=属性#始终指向最新主人处理函数
        自身.刷新打开()#按 open 武装

    def 卸载(自身):#卸载时标死
        """卸载时标死，丢弃后续结算。"""
        自身.存活=False#标死

    def 刷新打开(自身):#open 上升沿恰好挑一次
        """open 上升沿恰好挑一次。"""
        打开=取字段(自身.属性,'open')#打开旗
        if not 打开:#主人撤回或尚未打开
            自身.已武装=False#解除武装
            return#不启动挑选
        if 自身.已武装:#已武装过
            return#重渲染不再开第二个选择器
        自身.已武装=True#本轮 open 只武装一次
        挑选=取字段(自身.属性,'pick')#注入的挑选调用
        承诺=挑选()#打开原生选择器
        def 成功(路径):#选中路径或取消
            """选中路径或取消。"""
            if not 自身.存活:#实例已死
                return#丢弃结算
            if 路径 is None:#取消
                取字段(自身.属性,'onCancel')()#取消
            else:#采纳路径
                取字段(自身.属性,'onPicked')(路径)#采纳
        def 失败(原因):#挑选拒绝
            """挑选拒绝。"""
            if not 自身.存活:#实例已死
                return#丢弃结算
            if isinstance(原因,Exception):#标准异常
                消息=str(原因)#取字符串
            else:#其余
                消息=str(原因)#强制字符串
            取字段(自身.属性,'onError')(消息)#回报失败
        if hasattr(承诺,'wait') or hasattr(承诺,'等待') or callable(getattr(承诺,'then',None)):#可等待
            def 观察():#观察挑选
                """成败分别回报主人。"""
                try:#成功臂
                    成功(承诺.wait() if hasattr(承诺,'wait') else (承诺.等待() if hasattr(承诺,'等待') else 承诺))#等待或原样
                except BaseException as 原因:#失败臂
                    失败(原因)#回报失败
            threading.Thread(target=观察,daemon=True).start()#挂观察
        else:#同步结果
            try:#同步路径
                成功(承诺)#直接成功
            except Exception as 错误:#同步失败
                失败(错误)#失败臂

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用；返回 None（无渲染）。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return None#无渲染；选择器画在宿主显示器上
