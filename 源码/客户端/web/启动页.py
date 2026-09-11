"""无框架启动页与失败报告。

对齐上游 `web/src/boot-page.ts`。公开面仅中文名。
客户端插件失败时仍可用。错误与提示文案原样英文。
"""

__all__=['启动页']#仅中文公开名

def 建区块(文档,类名,文本=None):
    """创建带一个模块类与可选文本的 div。"""
    元素=文档.createElement('div')#新建
    元素.className=类名 if 类名 is not None else ''#类名
    if 文本 is not None:#有文本
        元素.textContent=文本#写下
    return 元素#元素

class 启动页:#内核拥有的页面
    """挂在应用根元素之下。"""
    def __init__(自身,容器):
        """构建并挂上启动页。"""
        文档=容器.ownerDocument#文档
        自身.根=建区块(文档,'boot')#根
        自身.根.dataset.dshBoot=''#启动页标记
        自身.卡片=建区块(文档,'card')#卡片
        自身.字标=建区块(文档,'wordmark','HARNESS')#字标
        自身.旋转=建区块(文档,'spinner')#进度弧
        自身.旋转.dataset.dshBootSpinner=''#旋转器标记
        自身.提示=建区块(文档,'hint','Loading plugins…')#加载提示
        自身.卡片.append(自身.字标,自身.旋转,自身.提示)#卡片子树
        自身.根.append(自身.卡片)#根下挂卡片
        容器.append(自身.根)#挂到应用容器
        自身.状态表={}#条目状态表
        自身.已激活=set()#已激活条目
        自身.总数=0#进度弧代表的条目总数
        自身.失败文案=None#失败报告文案
        自身.刷新进度()#初始进度弧

    def setTotal(自身,总数):
        """设置进度弧代表的加载器条目数。"""
        自身.总数=总数#记下
        自身.刷新进度()#刷新弧

    def setState(自身,标识,状态):
        """投影一条加载器条目的光纤状态。"""
        自身.状态表[标识]=状态#记下
        if 状态=='active':#激活
            自身.已激活.add(标识)#计入
        自身.刷新进度()#刷新弧
        自身.重绘()#重绘内容

    def fail(自身,消息):
        """显示启动失败报告。"""
        自身.失败文案=消息#记下
        自身.重绘()#重绘

    def dispose(自身):
        """在 UI 渲染器接管挂载点之前或之后卸下本页。"""
        自身.根.remove()#从 DOM 移除

    def 重绘(自身):
        """重绘字标下方依赖状态的内容。"""
        失败名=[标识 for 标识,状态 in 自身.状态表.items() if 状态=='failed']#失败条目
        if 自身.失败文案 is None and len(失败名)==0:#仍在加载
            if 自身.旋转.parentElement is not 自身.卡片:#卡片被失败报告替换过
                自身.卡片.replaceChildren(自身.字标,自身.旋转,自身.提示)#恢复加载 UI
            return#无需失败报告
        文档=自身.根.ownerDocument#文档
        报告=建区块(文档,'failed')#失败报告根
        报告.append(建区块(文档,'failedTitle','Failed to load plugins'))#标题
        for 标识 in 失败名:#失败条目名
            报告.append(建区块(文档,'failedItem',标识))#一条
        if 自身.失败文案 is not None:#总失败
            报告.append(建区块(文档,'failedItem',自身.失败文案))#文案
        自身.卡片.replaceChildren(自身.字标,报告)#换上失败报告

    def 刷新进度(自身):
        """随加载器条目激活单调增长旋转弧。比率 float。"""
        比率=0.0 if 自身.总数==0 else min(len(自身.已激活)/自身.总数,1.0)#完成比
        角度=str(round(72+比率*216))+'deg'#弧角度
        自身.旋转.style.setProperty('--dsh-boot-arc',角度)#弧变量
