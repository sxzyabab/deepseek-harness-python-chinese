
from nicegui import ui as 界面

__all__=['菜单','是分隔','是标题','视口边距','样式表']#仅中文公开名

样式表='''
.菜单{position:relative;display:inline-flex}
.菜单列,.子菜单{box-sizing:border-box;display:flex;flex-direction:column;gap:0;padding:4px;background:var(--dsw-specific-menu);border-radius:var(--dsw-radius-lg);box-shadow:var(--dsw-elevation-prominent)}
.菜单列{position:absolute;top:calc(100% + 4px);left:0;z-index:100;min-width:144px;max-width:360px}
.菜单.top .菜单列{top:auto;bottom:calc(100% + 4px)}
.菜单.end .菜单列{left:auto;right:0}
.子菜单{position:absolute;bottom:-4px;left:calc(100% + 10px);z-index:101;min-width:163px}
button.q-btn.菜单项{width:100%;height:auto;min-height:34px;padding:6px 8px;justify-content:flex-start;border-radius:var(--dsw-radius-md);background:transparent !important;box-shadow:none !important;color:var(--dsw-alias-label-primary) !important;font-size:13px;line-height:20px;font-weight:400}
button.q-btn.菜单项 .q-btn__content{gap:6px;justify-content:flex-start;flex-wrap:nowrap;width:100%}
button.q-btn.菜单项:hover{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.菜单项.菜单危险{color:var(--dsw-alias-state-error-primary) !important}
button.q-btn.菜单项.菜单危险:hover{background:var(--dsw-alias-interactive-bg-hover-danger) !important}
button.q-btn.菜单项.菜单选中{background:var(--dsw-alias-interactive-bg-hover) !important}
button.q-btn.菜单项:disabled{opacity:0.4}
.菜单标{padding:6px 8px;font-size:11px;line-height:15px;color:var(--dsw-alias-label-tertiary)}
.菜单隔{height:0.5px;margin:3px 2px;background:var(--dsw-alias-border-l2)}
.菜单脚{margin-top:3px;padding-top:3px;border-top:0.5px solid var(--dsw-alias-border-l2)}
'''

样式已登记=False

def 登记样式():
    '同一段样式整个进程只登记一次'
    global 样式已登记
    if 样式已登记 is True:
        return
    界面.add_css(样式表)
    样式已登记=True

视口边距=12#portal 边距

def 是分隔(条目):
    'type==separator。条目为 dict'
    return 'type' in 条目 and 条目['type']=='separator'#分隔

def 是标题(条目):
    'type==label。条目为 dict'
    return 'type' in 条目 and 条目['type']=='label'#标题

class 菜单:#锚定下拉
    '业主控 open；点外/Escape 关'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.开子菜单=None#子菜单 id

    def 更新(自身,属性):
        '刷新'
        自身.属性=dict(属性)#最新

    def 开子(自身,标识):
        '打开子菜单'
        自身.开子菜单=标识
    def 规范化条目(自身,条目表):
        '产出统一条目视图'
        选中=自身.属性['selectedId'] if 'selectedId' in 自身.属性 else None#单选
        多选列=自身.属性['selectedIds'] if 'selectedIds' in 自身.属性 else None#多选
        多选=多选列 if 多选列 is not None else []#空则空表
        列=条目表 if 条目表 is not None else []#空则空表
        结果=[]#行
        for 条目 in 列:#逐条
            if 是分隔(条目) is True:#分隔
                结果.append({'kind':'separator','id':条目['id'] if 'id' in 条目 else None})#隔
                continue#下
            if 是标题(条目) is True:#标题
                结果.append({'kind':'label','id':条目['id'] if 'id' in 条目 else None,'text':条目['text'] if 'text' in 条目 else ''})#标
                continue#下
            标识=条目['id'] if 'id' in 条目 else None#id
            已选=标识==选中 or 标识 in 多选#选中
            子=条目['submenu'] if 'submenu' in 条目 else None#子菜单
            结果.append({#行
                'kind':'item',#项
                'id':标识,#id
                'label':条目['label'] if 'label' in 条目 else None,#标签
                'disabled':条目['disabled'] is True if 'disabled' in 条目 else False,#禁用
                'danger':条目['danger'] is True if 'danger' in 条目 else False,#危险
                'icon':条目['icon'] if 'icon' in 条目 else None,#图标
                'selected':已选,#选中
                'submenu':自身.规范化条目(子) if 子 is not None else None,#子；空表仍规范化（JS 空数组为真）
                'submenuOpen':自身.开子菜单==标识,#子开
            })#行结束
        return 结果#列表

    def 渲染(自身):
        '画出锚，打开时画出条目'
        登记样式()
        属性=自身.属性#props
        打开=属性['open'] is True if 'open' in 属性 else False#开
        条目列=属性['items'] if 'items' in 属性 else None#条目
        条目列=条目列 if 条目列 is not None else []#空则空表
        脚列=属性['footer'] if 'footer' in 属性 else None#脚
        选回调=属性['onSelect'] if 'onSelect' in 属性 else None#选
        关回调=属性['onClose'] if 'onClose' in 属性 else None#关
        离开关=属性['closeOnPointerLeave'] is True if 'closeOnPointerLeave' in 属性 else False#离开关
        锚内容=属性['anchor'] if 'anchor' in 属性 else None#锚
        对齐=属性['align'] if 'align' in 属性 else 'start'#对齐
        侧=属性['side'] if 'side' in 属性 else 'bottom'#侧
        根=界面.column().classes('菜单 '+str(对齐)+' '+str(侧))#根
        类名=属性['className'] if 'className' in 属性 else None#类
        if isinstance(类名,str) and 类名!='':
            根.classes(类名)#附
        态={'开':打开}#本地开合
        def 画子(内容):
            '字符串做标签，组件自己画'
            if 内容 is None:#无
                return
            if isinstance(内容,str):#文案
                界面.label(内容)#标签
                return
            if isinstance(内容,(list,tuple)):#多项
                for 项 in 内容:#逐项
                    画子(项)#递归
                return
            if hasattr(内容,'渲染'):#组件
                内容.渲染()#自画
        def 画条目(条目表):
            '分隔、标题和可点项'
            for 条目 in 条目表:#逐条
                if 条目['kind']=='separator':#分隔
                    界面.element('div').classes('菜单隔')#线
                    continue#下
                if 条目['kind']=='label':#标题
                    文=条目['text'] if 条目['text'] is not None else ''#文
                    界面.label(文).classes('菜单标')#标题
                    continue#下
                文=条目['label'] if 条目['label'] is not None else ''#标签
                if isinstance(文,str) is False:#非串
                    文='' if 文 is None else str(文)#转
                标识=条目['id']#id
                子菜单=条目['submenu']#子
                def 点项(标识=标识,子菜单=子菜单):
                    '选中、打开子菜单或关闭'
                    if 子菜单 is not None:
                        自身.开子(标识)
                        重画()#重画
                        return
                    态['开']=False#关
                    重画()#先关
                    if 选回调 is not None:
                        选回调(标识)#调用
                    if 关回调 is not None:
                        关回调()#调用
                钮=界面.button(文 if 文!='' else ' ',on_click=点项).props('flat no-caps align=left').classes('菜单项')#项
                if 条目['disabled'] is True:#禁用
                    钮.props('disable')#禁
                if 条目['danger'] is True:#危险
                    钮.classes(add='菜单危险')#色
                if 条目['selected'] is True:#选中
                    钮.classes(add='菜单选中')#填充
                图标=条目['icon']#图标
                if isinstance(图标,str) and 图标!='':
                    尾=图标.rsplit('-',1)[-1]#尺寸后缀
                    图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#名
                    钮.props('icon='+图标名)#图
                if 子菜单 is not None and 条目['submenuOpen'] is True:#子开
                    with 界面.column().classes('子菜单'):#子列
                        画条目(子菜单)#子
        def 重画():
            '按开合重画列表'
            根.clear()
            with 根:#内容
                画子(锚内容)#锚
                if 态['开'] is False:#关
                    return#只留锚
                with 界面.column().classes('菜单列'):#列表
                    画条目(自身.规范化条目(条目列))#条目
                    脚=自身.规范化条目(脚列)#脚
                    if len(脚)>0:
                        with 界面.column().classes('菜单脚'):#脚
                            画条目(脚)#脚
        def 离开():
            '指针离开则关闭'
            if 离开关 is False:#不关
                return
            态['开']=False#关
            重画()#重画
            if 关回调 is not None:
                关回调()#调用
        根.on('mouseleave',离开)#离开
        重画()#首画

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()