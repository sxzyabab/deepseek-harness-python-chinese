"""草稿附件缩略图轨。



对齐上游 `ui-attachment/src/AttachmentRail.tsx`。公开面仅中文名。

无滚动条的水平溢出由边缘箭头分页；悬停显示移除；单击打开。

"""



__all__=['附件轨','滚轮行像素']#仅中文公开名



滚轮行像素=16#LINE 模式每步近似像素



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



class 附件轨:#水平缩略图轨

    """草稿附件缩略图轨；拥有方仅在有条目时挂载。"""

    def __init__(自身,属性):#构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.滚动左=0#scrollLeft

        自身.滚动宽=0#scrollWidth

        自身.可视宽=0#clientWidth

        自身.上次条数=None#首次布局为 None

        自身.存活=True#存活



    def 更新(自身,属性):#props 变更

        """条数增长时滚到末尾。"""

        旧条=len(取字段(自身.属性,'items') or [])#旧条数

        自身.属性=属性#最新

        新条=len(取字段(自身.属性,'items') or [])#新条数

        if 自身.上次条数 is not None and 新条>自身.上次条数:#增长

            自身.滚动左=max(0,自身.滚动宽-自身.可视宽)#末尾

        自身.上次条数=新条#记下

        if 旧条!=新条:#条数变

            自身.刷新边缘()#刷新



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死



    def 设几何(自身,滚动左,滚动宽,可视宽):#由宿主写入滚动几何

        """更新几何并刷新边缘。"""

        自身.滚动左=滚动左#左

        自身.滚动宽=滚动宽#宽

        自身.可视宽=可视宽#可视

        自身.刷新边缘()#边缘



    def 刷新边缘(自身):#重算左右箭头

        """1px 松弛：引擎在边缘报分数滚动。"""

        自身.左缘=自身.滚动左>1#左可滚

        自身.右缘=自身.滚动左<自身.滚动宽-自身.可视宽-1#右可滚



    def 翻页(自身,方向):#按视口翻页

        """一步视口减一卡；窄轨至少 200。"""

        步=方向*max(自身.可视宽-64,200)#步长

        自身.滚动左=max(0,min(自身.滚动左+步,max(0,自身.滚动宽-自身.可视宽)))#夹紧

        自身.刷新边缘()#边缘



    def 滚轮(自身,deltaX,deltaY,deltaMode=0):#垂直滚轮转水平

        """纯水平 pan 保持原生；有垂直分量则消费。"""

        if deltaY==0:#无垂直

            return False#不消费

        比例=滚轮行像素 if deltaMode==1 else (自身.可视宽 if deltaMode==2 else 1)#缩放

        if deltaX!=0:#对角

            左移=deltaX*比例#水平意图

        else:#纯垂直

            符号=1 if deltaY>0 else -1#符号

            左移=符号*min(abs(deltaY)*比例,60)#夹紧

        自身.滚动左=max(0,min(自身.滚动左+左移,max(0,自身.滚动宽-自身.可视宽)))#夹紧

        自身.刷新边缘()#边缘

        return True#已消费



    def 视图(自身):#读视图模型

        """投影轨与条目。"""

        条目表=取字段(自身.属性,'items') or []#条目

        文案=取字段(自身.属性,'labels') or {}#文案

        if not hasattr(自身,'左缘'):#尚未几何

            自身.刷新边缘()#默认边缘

        return {#视图

            'group':取字段(文案,'group'),#组名

            'open':取字段(文案,'open'),#打开提示

            'scrollLeft':取字段(文案,'scrollLeft'),#左箭头

            'scrollRight':取字段(文案,'scrollRight'),#右箭头

            'showLeft':自身.左缘,#显左箭

            'showRight':自身.右缘,#显右箭

            'scrollLeftPx':自身.滚动左,#滚动位置

            'items':[{#缩略项

                'id':取字段(项,'id'),#身份

                'previewUrl':取字段(项,'previewUrl'),#预览

                'alt':取字段(项,'alt'),#替代文本

                'removeLabel':取字段(项,'removeLabel'),#移除文案

            } for 项 in 条目表],#项表

        }#视图结束



    def 打开(自身,项):#单击打开

        """转调 onOpen。"""

        回调=取字段(自身.属性,'onOpen')#回调

        if 回调 is not None:#有

            回调(项)#打开



    def 移除(自身,项):#移除

        """转调 onRemove。"""

        回调=取字段(自身.属性,'onRemove')#回调

        if 回调 is not None:#有

            回调(项)#移除



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


