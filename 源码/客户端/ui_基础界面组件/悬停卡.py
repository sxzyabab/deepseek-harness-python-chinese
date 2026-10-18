from threading import Timer as 定时器
from .指针宽限 import 指针宽限#离开宽限
from .剪贴板 import 写剪贴板#复制

__all__=['悬停卡','处理悬停卡','默认打开延迟毫秒']#仅中文公开名

默认打开延迟毫秒=500#悬停驻留

样式表='''
.悬停卡锚{position:relative;display:block}
.悬停卡{position:fixed;z-index:100;box-sizing:border-box;width:244px;padding:12px 16px;border-radius:var(--dsw-radius-lg);background:#2C2C2E;box-shadow:var(--dsw-shadow-lv3);color:#fff}
'''

def 处理悬停卡(window,属性):
    '画出锚，悬停后画出卡片。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('悬停卡样式') is None:
        样式=文档.createElement('style')
        样式.id='悬停卡样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    组件=属性['组件']
    可复制=('copyText' in 属性) and 属性['copyText'] is not None#可复制
    延迟=属性['openDelayMs'] if 'openDelayMs' in 属性 else 默认打开延迟毫秒#驻留
    禁用=属性['disabled'] is True if 'disabled' in 属性 else False#禁
    锚内容=属性['anchor'] if 'anchor' in 属性 else None#锚
    卡内容=属性['content'] if 'content' in 属性 else None#卡内容
    复制前=属性['copyLabel'] if 'copyLabel' in 属性 else '复制'#复制前
    复制后=属性['copiedLabel'] if 'copiedLabel' in 属性 else '复制成功'#成功
    if 复制前 is None:#缺
        复制前='复制'#默认
    if 复制后 is None:#缺
        复制后='复制成功'#默认
    def 画子(内容,父):
        '字符串做标签，组件自己画'
        if 内容 is None:#无
            return
        if isinstance(内容,str):#文案
            标=文档.createElement('span')
            标.textContent=内容
            父.appendChild(标)
            return
        if isinstance(内容,(list,tuple)):#多项
            for 项 in 内容:#逐项
                画子(项,父)#递归
            return
        if hasattr(内容,'tagName'):
            父.appendChild(内容)
            return
        if hasattr(内容,'渲染'):#组件
            if hasattr(内容,'属性') and isinstance(内容.属性,dict):
                内容.属性['window']=window
            节点=内容.渲染()
            if 节点 is not None and hasattr(节点,'tagName'):
                父.appendChild(节点)
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
    锚=文档.createElement('div')
    锚.className='悬停卡锚'
    画子(锚内容,锚)
    卡=文档.createElement('div')
    卡.className='悬停卡'
    卡.hidden=True
    代={'n':0}#悬停代际
    def 画卡():
        '重画卡片正文和复制'
        清空(卡)
        画子(卡内容,卡)
        if 可复制:#可复制
            文=复制后 if 组件.已复制 else 复制前#文案
            def 点复制(事件):
                '写入剪贴板并刷新文案'
                组件.复制()
                画卡()
            钮=文档.createElement('button')
            钮.type='button'
            钮.textContent=文
            钮.addEventListener('click',点复制)
            卡.appendChild(钮)
    def 进入(事件):
        '延迟后打开'
        if 禁用:#禁
            return
        代['n']+=1#新代
        当前=代['n']
        def 打开():
            '代际未变才打开'
            if 代['n']!=当前:#已离开
                return
            组件.打开卡()
            画卡()
            卡.hidden=False
        if 延迟<=0:#无延迟
            打开()
            return
        定时器(延迟/1000,打开).start()
    def 离开(事件):
        '宽限后关闭'
        代['n']+=1#新代
        当前=代['n']
        def 关掉():
            '代际未变才关闭'
            if 代['n']!=当前:#已返回
                return
            组件.关闭()
            卡.hidden=True
        定时器(0.2,关掉).start()
    if 禁用 is False:#可悬停
        锚.addEventListener('mouseenter',进入)
        锚.addEventListener('mouseleave',离开)
        卡.addEventListener('mouseenter',进入)
        卡.addEventListener('mouseleave',离开)
    壳=文档.createElement('div')
    壳.appendChild(锚)
    壳.appendChild(卡)
    if 'parent' in 属性:
        属性['parent'].appendChild(壳)
    return 壳

class 悬停卡:#悬停预览
    '状态机：打开延迟、宽限关闭、可选点卡复制'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props 与本地态。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.已打开=False#卡是否开
        自身.已复制=False#复制反馈
        自身.位置=None#固定坐标
        自身.宽限=指针宽限(自身.关闭)#离开宽限
        自身.根=None

    def 更新(自身,属性):
        '刷新 props；禁用则立即关'
        自身.属性=dict(属性)#最新
        禁用=自身.属性['disabled'] is True if 'disabled' in 自身.属性 else False#禁用
        if 禁用 is True:#禁用
            自身.宽限.取消()#取消宽限
            自身.关闭()#关

    def 关闭(自身):
        '清复制反馈并关'
        自身.已复制=False
        自身.已打开=False#关
        自身.位置=None

    def 打开卡(自身):
        '置开；宿主再量锚定位'
        自身.已打开=True#开

    def 复制(自身):
        '有 copyText 且未在反馈中才写'
        文本=自身.属性['copyText'] if 'copyText' in 自身.属性 else None#可复制值
        if 文本 is None or 自身.已复制 is True:#无或反馈中
            return False#跳
        if 写剪贴板(str(文本)) is False:#拒绝
            return False#失败
        自身.已复制=True#反馈
        return True#成功

    def 渲染(自身):
        '拆掉旧卡，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['组件']=自身
        自身.根=处理悬停卡(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
