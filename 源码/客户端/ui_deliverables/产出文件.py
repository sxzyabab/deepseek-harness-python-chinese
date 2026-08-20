"""产出文件行：回合尾链上的可打开芯片。



对齐上游 `ui-deliverables/src/client/ProducedFiles.tsx`。公开面仅中文名。

路径来自变更工具 locations，从不来自收口散文。

"""



__all__=['适配产出文件','产出文件行','展示上限']#仅中文公开名



展示上限=6#一行摘要最多六枚芯片



def 取字段(对象,键,缺省=None):#从映射或对象读字段

    """从映射或对象读字段，缺席为缺省。"""

    if 对象 is None:#空

        return 缺省#缺席

    if isinstance(对象,dict):#映射

        if 键 in 对象:#自有键

            return 对象[键]#值

        return 缺席#缺席

    return getattr(对象,键,缺省)#属性



def 适配产出文件(可用宽,间隙,芯片宽表,更多宽按展示):#选最大能装下的前缀

    """对齐 fitProducedFiles：量宽适配可见芯片数。"""

    if 可用宽<=0:#不可用宽则全显

        return len(芯片宽表)#全显

    前缀=[0]#前缀宽

    累加=0#累加宽

    for 宽 in 芯片宽表:#每枚

        累加+=宽#加

        前缀.append(累加)#记下

    最大适配=0#最大 shown

    for 展示,宽 in enumerate(前缀):#候选 shown

        更多=更多宽按展示[展示] if 展示<len(更多宽按展示) else None#更多宽

        项数=展示+(0 if 更多 is None else 1)#项数

        需要=宽+(更多 or 0)+max(0,项数-1)*间隙#所需宽

        if 需要<=可用宽:#装得下

            最大适配=展示#记下

    return 最大适配#返回



def 更多文案(翻译,计数):#剩余文件文案

    """一个用 moreOne，否则带 count。"""

    if 计数==1:#恰好一

        return 翻译('produced.moreOne')#单数

    return 翻译('produced.more',{'count':str(计数)})#复数



def 路径末段(路径):#取路径末段

    """最后一段。"""

    斜=路径.rfind('/')#正斜杠

    反=路径.rfind('\\')#反斜杠

    位=斜 if 斜>反 else 反#最后分隔

    return 路径 if 位==-1 else 路径[位+1:]#末段



class 产出文件行:#回合尾产出行

    """渲染可打开芯片；量宽逻辑由调用方传入可用宽可选触发。"""

    def __init__(自身,属性):#构造

        """记下 props。"""

        自身.属性=属性#合成 props

        自身.展示数=None#量宽后的展示数；None 表示用上限

        自身.存活=True#存活



    def 更新(自身,属性):#props 变更

        """刷新。"""

        自身.属性=属性#最新



    def 卸载(自身):#卸载

        """标死。"""

        自身.存活=False#死



    def 设展示数(自身,数量):#量宽结果

        """写入可见芯片数。"""

        自身.展示数=数量#记下



    def 视图(自身):#读视图模型

        """投影芯片行。"""

        路径表=list(取字段(自身.属性,'matched') or [])#匹配路径

        翻译=取字段(自身.属性,'t',lambda 键,参=None:键 if 参 is None else 键)#文案

        打开文件=取字段(自身.属性,'openFile',lambda 路径:None)#打开

        回环=bool(取字段(自身.属性,'isLoopback'))#回环

        用宿主描述=取字段(自身.属性,'useHostDescription')#宿主描述钩子

        能开路径=False#默认不能

        if 回环 and 用宿主描述 is not None:#回环且有钩子

            能开路径=bool(用宿主描述(lambda 描述:取字段(描述,'canOpenPath') is True))#读能力

        上限=min(len(路径表),展示上限)#上限

        可见=上限 if 自身.展示数 is None else min(自身.展示数,上限)#可见数

        显示=路径表[:可见]#可见路径

        隐藏=len(路径表)-len(显示)#隐藏数

        芯片=[{#芯片

            'path':路径,#全路径

            'name':路径末段(路径),#末段

            'aria':翻译('produced.open',{'name':路径}),#无障碍

        } for 路径 in 显示]#芯片表

        return {#视图

            'label':翻译('produced.label'),#产物标签

            'chips':芯片,#芯片

            'more':更多文案(翻译,隐藏) if 隐藏>0 else None,#更多

            'showInFolder':翻译('produced.showInFolder') if 隐藏>0 and 能开路径 else None,#文件夹

            'paths':路径表,#全路径（量宽用）

            'limit':上限,#上限

            'openFile':打开文件,#打开器

        }#视图结束



    def __call__(自身,属性=None):#组件调用形

        """对齐 React 组件调用。"""

        if 属性 is not None:#有新 props

            自身.更新(属性)#刷新

        return 自身.视图()#视图


