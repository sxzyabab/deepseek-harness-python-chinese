"""会话状态点。

对齐上游 `ui-primitives/src/StateDot.tsx`。公开面仅中文名。
done/warning/error 为实心晕；ongoing 为 3x3 像素追逐。
"""

__all__=['状态点','状态表','矩阵格']#仅中文公开名

状态表=('done','warning','ongoing','error')#四态
矩阵格=((0,0),(4,0),(8,0),(8,4),(8,8),(4,8),(0,8),(0,4))#顺时针外圈

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

class 状态点:#状态指示
    """aria-hidden；旁配文案。"""

    def __init__(自身,属性=None,**关键字参数):#构造
        """合并 props。"""
        自身.属性=dict(属性 or {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):#刷新
        """刷新。"""
        自身.属性=dict(属性)#最新

    def 渲染(自身):#结构树
        """点或矩阵。"""
        属性=自身.属性#props
        态=取字段(属性,'state','done')#态
        if 态 not in 状态表:#非法
            态='done'#回退
        尺寸=取字段(属性,'size',10)#直径
        if 态=='ongoing':#追逐
            格=[]#格
            for 序,(x,y) in enumerate(矩阵格):#逐格
                格.append({'x':x,'y':y,'delayMs':(序-len(矩阵格))*125})#相位
            return {#矩阵
                'type':'state-dot',#类型
                'mode':'matrix',#模式
                'state':态,#态
                'size':尺寸,#尺寸
                'cells':格,#格
                'className':取字段(属性,'className'),#类
                'cssModule':'状态点.module.css',#样式
            }#视图结束
        return {#实心点
            'type':'state-dot',#类型
            'mode':'dot',#模式
            'state':态,#态
            'size':尺寸,#尺寸
            'className':取字段(属性,'className'),#类
            'cssModule':'状态点.module.css',#样式
        }#视图结束

    def __call__(自身,属性=None,**关键字参数):#调用形
        """对齐 React。"""
        if 属性 is not None or 关键字参数:#有
            合并=dict(属性 or {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()#渲
