from nicegui import ui as 界面

__all__=['状态点','状态表','矩阵格','样式表']#仅中文公开名

状态表=('done','warning','ongoing','error')#四态
矩阵格=((0,0),(4,0),(8,0),(8,4),(8,8),(4,8),(0,8),(0,4))#顺时针外圈
样式表='''
.状态点{position:relative;display:inline-block;flex:none}
.状态点.点::after{content:'';position:absolute;inset:20%;border-radius:50%;background:currentColor}
.状态点[data-state=done]{color:var(--dsw-alias-state-success-primary)}
.状态点[data-state=warning]{color:var(--dsw-alias-state-warn-primary)}
.状态点[data-state=error]{color:var(--dsw-alias-state-error-primary)}
.状态点[data-state=idle]{color:var(--dsw-alias-state-idle-primary)}
.状态点.转{flex:none;color:var(--dsw-alias-label-tertiary)}
.状态点 .转运动{transform-origin:center;animation:dsh-state-dot-spin 1.5s linear infinite}
.状态点 .转轨,.状态点 .转弧{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round}
.状态点 .转轨{opacity:0.25}
.状态点 .转弧{stroke-dasharray:12 150;animation:dsh-state-dot-dash 1.5s ease-in-out infinite}
@keyframes dsh-state-dot-spin{to{transform:rotate(360deg)}}
@keyframes dsh-state-dot-dash{0%{stroke-dasharray:12 150;stroke-dashoffset:0}50%{stroke-dasharray:24 150;stroke-dashoffset:-6}100%{stroke-dasharray:12 150;stroke-dashoffset:0}}
@media (prefers-reduced-motion:reduce){.状态点 .转运动,.状态点 .转弧{animation:none}.状态点 .转弧{stroke-dasharray:18 150;stroke-dashoffset:-3}}
.状态点.步{display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box;border-radius:50%;border:1.5px solid var(--dsw-alias-label-tertiary);color:var(--dsw-alias-label-primary-foreground)}
.状态点.步[data-state=done]{border-color:var(--dsw-alias-state-success-primary);background:var(--dsw-alias-state-success-primary)}
.状态点.步[data-state=error]{border-color:var(--dsw-alias-state-error-primary);background:var(--dsw-alias-state-error-primary)}
.状态点.步[data-state=warning]{border-color:var(--dsw-alias-state-warn-primary)}
'''

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

class 状态点:#状态指示
    'aria-hidden；旁配文案'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 渲染(自身):
        '画出实心点或追逐矩阵'
        登记样式()
        属性=自身.属性#props
        态=属性['state'] if 'state' in 属性 else 'done'#态
        if 态 not in 状态表:#非法
            态='done'#回退
        外观=属性['appearance'] if 'appearance' in 属性 else 'dot'#点或步
        尺寸=属性['size'] if 'size' in 属性 else (14 if 态=='ongoing' else 10)#边长
        类名=属性['className'] if 'className' in 属性 else None#类
        if 态=='ongoing':#转圈
            标记=界面.html('<svg class="状态点 转" data-state="ongoing" width="'+str(尺寸)+'" height="'+str(尺寸)+'" viewBox="0 0 24 24" aria-hidden="true"><g class="转运动"><circle class="转轨" cx="12" cy="12" r="9.5"></circle><circle class="转弧" cx="12" cy="12" r="9.5"></circle></g></svg>',sanitize=False)#转
        else:#实心
            步=' 步' if 外观=='step' else ' 点'
            标记=界面.html('<span aria-hidden="true" class="状态点'+步+'" data-state="'+态+'" style="width:'+str(尺寸)+'px;height:'+str(尺寸)+'px"></span>',sanitize=False)#点
        标记.classes('状态点 '+态)#类
        if isinstance(类名,str) and 类名!='':#附加类
            标记.classes(类名)#附

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
