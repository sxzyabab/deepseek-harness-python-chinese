"""历史消息图与图库。



对齐上游 `ui-attachment/src/MessageImage.tsx`。公开面仅中文名。

可重试加载；单击打开原图灯箱；单图按 singleFit，多图 64px 方砖。

"""

from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

from .原图灯箱 import 原图灯箱#灯箱



__all__=['消息图','图库','单图适配']#仅中文公开名



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



def 解开(值):#承诺则等待否则原样

    """承诺则等待，否则原样返回。"""

    if 是否thenable(值):#可等待

        return 值.等待()#等待

    return 值#同步



def 单图适配(附件):#单图显示盒

    """长边 240px，宽高比夹在 [0.25,4]，不放大超过自然尺寸。"""

    宽=取字段(附件,'width') or 1#宽

    高=取字段(附件,'height') or 1#高

    自然=宽/高#自然比

    比例=min(4,max(0.25,自然))#夹紧比

    if 比例>=1:#横图

        盒宽,盒高=240,240/比例#盒

    else:#竖图

        盒宽,盒高=240*比例,240#盒

    缩放=min(1,宽/盒宽,高/盒高)#不放大

    物位='center top' if 自然<0.25 else ('left center' if 自然>4 else 'center')#锚点

    return {#适配

        'width':max(1,round(盒宽*缩放)),#宽

        'height':max(1,round(盒高*缩放)),#高

        'objectPosition':物位,#物位

    }#适配结束



class 消息图:#历史缩略图

    """可重试加载与单击原图预览。"""

    def __init__(自身,属性):#构造

        """记下 props 并首载。"""

        自身.属性=属性#合成 props

        自身.源=None#已解析 URL

        自身.错误=False#失败

        自身.打开中=False#灯箱

        自身.尝试=0#重试计数

        自身.存活=True#存活

        自身.灯箱=None#内嵌灯箱

        自身.加载()#首载



    def 更新(自身,属性):#props 变更

        """附件或加载器变则重载。"""

        旧附=取字段(自身.属性,'attachment')#旧

        旧载=取字段(自身.属性,'load')#旧载

        自身.属性=属性#最新

        if 取字段(自身.属性,'attachment') is not 旧附 or 取字段(自身.属性,'load') is not 旧载:#变

            自身.加载()#重载



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死

        if 自身.灯箱 is not None:#有灯箱

            自身.灯箱.卸载()#拆



    def 加载(自身):#拉取 URL

        """同一存活守卫下加载。"""

        自身.错误=False#清错

        自身.源=None#清源

        加载器=取字段(自身.属性,'load')#加载器

        附件=取字段(自身.属性,'attachment')#附件

        try:#加载

            地址=解开(加载器(附件)) if 加载器 is not None else None#结算

        except Exception:#失败

            if 自身.存活:#仍活

                自身.错误=True#失败

            return#结束

        if not 自身.存活:#已死

            return#丢弃

        自身.源=地址#记下



    def 重试(自身):#失败后重试

        """抬尝试计数并再载。"""

        自身.尝试+=1#计数

        自身.加载()#再载



    def 打开(自身):#开灯箱

        """有源才开。"""

        if 自身.源 is None:#无源

            return#结束

        自身.打开中=True#打开

        文案=取字段(自身.属性,'labels') or {}#文案

        附件=取字段(自身.属性,'attachment') or {}#附件

        名=取字段(附件,'name') or 取字段(文案,'image')#显示名

        自身.灯箱=原图灯箱({#灯箱 props

            'src':自身.源,#URL

            'alt':名,#替代

            'labels':取字段(文案,'lightbox') or {},#灯箱文案

            'onClose':自身.关闭灯箱,#关闭

        })#铸造



    def 关闭灯箱(自身):#关灯箱

        """关掉。"""

        自身.打开中=False#关

        if 自身.灯箱 is not None:#有

            自身.灯箱.卸载()#拆

            自身.灯箱=None#清



    def 视图(自身):#读视图模型

        """投影缩略或重试钮。"""

        文案=取字段(自身.属性,'labels') or {}#文案

        附件=取字段(自身.属性,'attachment') or {}#附件

        变体=取字段(自身.属性,'variant') or 'tile'#变体

        名=取字段(附件,'name') or 取字段(文案,'image')#显示名

        开名=取字段(文案,'openNamed')#命名打开

        if callable(开名):#函数

            无障碍=开名(名)#调用

        else:#缺席

            无障碍=名#退回

        if 自身.错误:#失败

            return {'status':'error','variant':变体,'retryLabel':取字段(文案,'loadFailed')}#重试

        适配=单图适配(附件) if 变体=='single' else None#单图适配

        结果={#就绪视图

            'status':'ready',#状态

            'variant':变体,#变体

            'src':自身.源,#URL

            'alt':名,#替代

            'title':取字段(文案,'open'),#提示

            'aria':无障碍,#无障碍

            'loading':取字段(文案,'loading') if 自身.源 is None else None,#加载中

            'fit':适配,#适配

            'lightbox':自身.灯箱() if 自身.打开中 and 自身.灯箱 is not None else None,#灯箱

        }#结果结束

        return 结果#返回



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图



class 图库:#消息图组

    """单图大显，多图方砖。"""

    def __init__(自身,属性):#构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.子图=[]#子消息图

        自身.重建子图()#首建



    def 重建子图(自身):#按 images 重建

        """变体随条数变。"""

        图列=取字段(自身.属性,'images') or []#图列

        变体='single' if len(图列)==1 else 'tile'#变体

        加载=取字段(自身.属性,'load')#加载器

        文案=取字段(自身.属性,'labels')#文案

        自身.子图=[消息图({#子图

            'attachment':取字段(图,'attachment'),#附件

            'load':加载,#加载

            'variant':变体,#变体

            'labels':文案,#文案

        }) for 图 in 图列]#铸造



    def 更新(自身,属性):#props 变更

        """刷新并重建。"""

        自身.属性=属性#最新

        for 子 in 自身.子图:#旧子

            子.卸载()#拆

        自身.重建子图()#重建



    def 卸载(自身):#卸载

        """拆子图。"""

        for 子 in 自身.子图:#每个

            子.卸载()#拆

        自身.子图=[]#清



    def 视图(自身):#读视图模型

        """空图列返回 None。"""

        图列=取字段(自身.属性,'images') or []#图列

        if len(图列)==0:#空

            return None#不渲染

        return {#视图

            'align':取字段(自身.属性,'align'),#对齐

            'images':[子() for 子 in 自身.子图],#子视图

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


