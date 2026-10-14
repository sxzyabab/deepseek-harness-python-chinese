from contextlib import nullcontext as 空上下文
from nicegui import ui as 界面

__all__=['启动页']#仅中文公开名

样式表='''
.启动页{--dsh-boot-label-primary:#0f1115;--dsh-boot-label-secondary:#61666b;--dsh-boot-label-tertiary:#81858c;--dsh-boot-border:rgb(0 0 0 / 10%);--dsh-boot-brand:#0f1115;height:100%;display:grid;place-items:center;background:var(--dsw-alias-bg-base, var(--dsh-boot-bg, Canvas))}
body[data-ds-dark-theme] .启动页{--dsh-boot-label-primary:#f9fafb;--dsh-boot-label-secondary:#cfd3d6;--dsh-boot-label-tertiary:#adb2b8;--dsh-boot-border:rgb(255 255 255 / 12%);--dsh-boot-brand:#f9fafb}
.启动卡{display:flex;flex-direction:column;align-items:center;gap:16px}
.启动字标{font-size:16px;line-height:24px;font-weight:600;letter-spacing:0.08em;color:var(--dsw-alias-label-primary, var(--dsh-boot-label-primary))}
.启动提示{font-size:12px;line-height:18px;color:var(--dsw-alias-label-tertiary, var(--dsh-boot-label-tertiary))}
.启动弧{position:relative;width:20px;height:20px;border-radius:50%;border:2px solid var(--dsw-alias-border-l2, var(--dsh-boot-border));animation:启动弧转 0.8s linear infinite}
.启动弧::after{content:'';position:absolute;inset:-2px;border-radius:inherit;background:conic-gradient(var(--dsw-alias-brand-primary, var(--dsh-boot-brand)) var(--dsh-boot-arc, 72deg), transparent 0);-webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 2px), #000 0);mask:radial-gradient(farthest-side, transparent calc(100% - 2px), #000 0)}
@keyframes 启动弧转{to{transform:rotate(360deg)}}
.启动失败{max-width:480px;display:flex;flex-direction:column;gap:8px}
.启动失败标题{font-size:14px;line-height:22px;font-weight:600;color:var(--dsw-alias-label-primary, var(--dsh-boot-label-primary))}
.启动失败项{font-family:var(--ds-font-family-code, 'SF Mono', 'JetBrains Mono', 'Fira Code', Consolas, 'Liberation Mono', Menlo, Courier, 'PingFang SC', 'Microsoft YaHei');font-size:12px;line-height:18px;color:var(--dsw-alias-label-secondary, var(--dsh-boot-label-secondary));white-space:pre-wrap}
'''#样式表结束
界面.add_css(样式表,shared=True)

def 异常页面文案(错误):
    '页面上给调用方看的失败句：异常类型加说明，不带绝对路径'
    名=type(错误).__name__
    留下=[]
    for 词 in str(错误).split():
        统一=词.strip('\'"').replace('\\','/')
        if 统一.startswith('/') or (len(统一)>2 and 统一[0].isalpha() and 统一[1]==':' and 统一[2]=='/'):
            continue
        留下.append(词)
    说明=' '.join(留下).strip()
    if len(说明)==0 or 说明==名:
        return 名
    return 名+'：'+说明

class 启动页:#内核拥有的页面
    '挂在应用根之下；入口只构造，这里就要画'
    def __init__(自身,容器=None):
        '记下挂载点并画出加载态'
        自身.容器=容器#应用挂载点
        自身.画面=None#可反复清空的根
        自身.旋转=None#进度弧元素
        自身.状态表={}#条目状态表
        自身.已激活=set()#已激活条目
        自身.总数=0#进度弧代表的条目总数
        自身.失败文案=None#失败报告文案
        自身.渲染()#页面入口只调用构造

    def 设总数(自身,总数):
        '设置进度弧代表的加载器条目数'
        自身.总数=总数
        自身.刷新进度()#刷新弧

    def 设状态(自身,标识,状态):
        '投影一条加载器条目的纤程状态'
        自身.状态表[标识]=状态
        if 状态=='active':#激活后弧只增不减
            自身.已激活.add(标识)#计入
        自身.渲染()#重画

    def 显示失败(自身,消息):
        '显示启动失败报告'
        自身.失败文案=消息
        自身.渲染()#重画

    def 卸下(自身):
        '在 UI 渲染器接管挂载点之前或之后卸下本页'
        画面=自身.画面#当前根
        自身.画面=None#丢掉引用
        自身.旋转=None#弧随根走
        if 画面 is None:#尚未画出
            return
        删除=getattr(画面,'delete',None)#NiceGUI 拆除
        if callable(删除):
            try:#从页面卸下
                删除()#拆除
            except Exception:#画面已被页面拆掉
                raise
            return
        移除=getattr(画面,'remove',None)#DOM 拆除
        if callable(移除):
            移除()#移除

    def 失败名(自身):
        '当前状态为 failed 的条目名'
        return [标识 for 标识,状态 in 自身.状态表.items() if 状态=='failed']#失败条目

    def 渲染(自身):
        '先画字标与进度或失败报告，再返回根。样式在模块加载时已按共享表登记'
        if 自身.画面 is not None:#已有根
            try:
                自身.画面.clear()
            except Exception as 错误:#父级清掉容器后旧画面已不在页面上
                自身.画面=None#丢掉
                文案=异常页面文案(错误)
                if 自身.失败文案 is None:
                    自身.失败文案=文案
                elif 文案 not in 自身.失败文案:
                    自身.失败文案=自身.失败文案+'\n'+文案
        失败名=自身.失败名()#失败条目
        加载中=自身.失败文案 is None and len(失败名)==0#仍在加载
        if 自身.画面 is None:#新建根
            父=自身.容器 if 自身.容器 is not None and hasattr(自身.容器,'__enter__') and hasattr(自身.容器,'__exit__') else 空上下文()#NiceGUI 父级或当前页
            with 父:#挂到调用方容器
                自身.画面=界面.element('div').classes('启动页')#根
                自身.画面.props('data-dsh-boot')#启动页标记
        with 自身.画面:#根下
            with 界面.element('div').classes('启动卡'):#卡片
                界面.label('HARNESS').classes('启动字标')#字标
                if 加载中:#加载 UI
                    自身.旋转=界面.element('div').classes('启动弧')#进度弧
                    自身.旋转.props('data-dsh-boot-spinner')#旋转器标记
                    界面.label('正在加载插件…').classes('启动提示')#加载提示
                else:#失败报告
                    自身.旋转=None#弧已换下
                    with 界面.element('div').classes('启动失败'):#失败报告
                        界面.label('加载插件失败').classes('启动失败标题')#标题
                        for 标识 in 失败名:#失败条目名
                            界面.label(标识).classes('启动失败项')#一条
                        if 自身.失败文案 is not None:#总失败
                            界面.label(自身.失败文案).classes('启动失败项')#文案
        自身.刷新进度()#按当前激活数上色
        return 自身.画面#根

    def 刷新进度(自身):
        '随加载器条目激活单调增长旋转弧'
        if 自身.旋转 is None:#失败报告没有弧
            return
        比率=0.0 if 自身.总数==0 else min(len(自身.已激活)/自身.总数,1.0)#激活占比
        角度=str(round(72+比率*216))+'deg'#弧角度
        自身.旋转.style(replace='--dsh-boot-arc: '+角度)#弧变量
