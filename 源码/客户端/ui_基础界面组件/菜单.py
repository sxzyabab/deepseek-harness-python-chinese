from .菜单表面 import 菜单表面
from .点外关闭 import 点外关闭
from .覆盖层顶边距 import 覆盖层顶边距

__all__=['菜单','处理菜单','是分隔','是标题','视口边距','样式表']#仅中文公开名

样式表='''
.菜单{position:relative;display:inline-flex}
.菜单列,.子菜单{box-sizing:border-box;display:flex;flex-direction:column;gap:0;padding:4px;background:var(--dsw-specific-menu);border-radius:var(--dsw-radius-lg);box-shadow:var(--dsw-elevation-prominent)}
.菜单列{position:absolute;top:calc(100% + 4px);left:0;z-index:100;min-width:144px;max-width:360px}
.菜单.top .菜单列{top:auto;bottom:calc(100% + 4px)}
.菜单.end .菜单列{left:auto;right:0}
.子菜单{position:absolute;bottom:-4px;left:calc(100% + 10px);z-index:101;min-width:163px}
button.菜单项{width:100%;height:auto;min-height:34px;padding:6px 8px;border:0;justify-content:flex-start;align-items:center;gap:6px;flex-wrap:nowrap;border-radius:var(--dsw-radius-md);background:transparent;box-shadow:none;color:var(--dsw-alias-label-primary);font-size:13px;line-height:20px;font-weight:400;cursor:pointer;display:flex;text-align:left}
button.菜单项:hover{background:var(--dsw-alias-interactive-bg-hover)}
button.菜单项.菜单危险{color:var(--dsw-alias-state-error-primary)}
button.菜单项.菜单危险:hover{background:var(--dsw-alias-interactive-bg-hover-danger)}
button.菜单项.菜单选中{background:var(--dsw-alias-interactive-bg-hover)}
button.菜单项:disabled{opacity:0.4}
.菜单标{padding:6px 8px;font-size:11px;line-height:15px;color:var(--dsw-alias-label-tertiary)}
.菜单隔{height:0.5px;margin:3px 2px;background:var(--dsw-alias-border-l2)}
.菜单脚{margin-top:3px;padding-top:3px;border-top:0.5px solid var(--dsw-alias-border-l2);display:flex;flex-direction:column}
'''

视口边距=12#portal 边距

def 是分隔(条目):
    'type==separator。条目为 dict'
    return 'type' in 条目 and 条目['type']=='separator'#分隔

def 是标题(条目):
    'type==label。条目为 dict'
    return 'type' in 条目 and 条目['type']=='label'#标题

def 处理菜单(window,属性):
    '画出锚，打开时画出条目。有 parent 就挂上去'
    文档=window.document
    if 文档.getElementById('菜单样式') is None:
        样式=文档.createElement('style')
        样式.id='菜单样式'
        样式.textContent=样式表
        文档.head.appendChild(样式)
    菜单=属性['菜单']
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
    根=文档.createElement('div')
    根.className='菜单 '+str(对齐)+' '+str(侧)
    类名=属性['className'] if 'className' in 属性 else None#类
    if isinstance(类名,str) and 类名!='':
        根.className=根.className+' '+类名
    态={'开':打开}#本地开合
    def 清空(节点):
        while 节点.firstElementChild is not None:
            节点.firstElementChild.remove()
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
    def 画条目(条目表,父):
        '分隔、标题和可点项'
        for 条目 in 条目表:#逐条
            if 条目['kind']=='separator':#分隔
                线=文档.createElement('div')
                线.className='菜单隔'
                父.appendChild(线)
                continue#下
            if 条目['kind']=='label':#标题
                文=条目['text'] if 条目['text'] is not None else ''#文
                标=文档.createElement('div')
                标.className='菜单标'
                标.textContent=文
                父.appendChild(标)
                continue#下
            文=条目['label'] if 条目['label'] is not None else ''#标签
            if isinstance(文,str) is False:#非串
                文='' if 文 is None else str(文)#转
            标识=条目['id']#id
            子菜单=条目['submenu']#子
            def 点项(事件,标识=标识,子菜单=子菜单):
                '选中、打开子菜单或关闭'
                if 子菜单 is not None:
                    菜单.开子(标识)
                    重画()#重画
                    return
                态['开']=False#关
                重画()#先关
                if 选回调 is not None:
                    选回调(标识)#调用
                if 关回调 is not None:
                    关回调()#调用
            钮=文档.createElement('button')
            钮.type='button'
            钮.className='菜单项'
            钮.textContent=文 if 文!='' else ' '
            钮.disabled=条目['disabled'] is True
            if 条目['danger'] is True:#危险
                钮.classList.add('菜单危险')
            if 条目['selected'] is True:#选中
                钮.classList.add('菜单选中')
            图标=条目['icon']#图标
            if isinstance(图标,str) and 图标!='':
                尾=图标.rsplit('-',1)[-1]#尺寸后缀
                图标名=图标.rsplit('-',1)[0] if 尾.isdigit() else 图标#名
                图=文档.createElement('span')
                图.className='材料图标'
                图.setAttribute('aria-hidden','true')
                图.textContent=图标名
                钮.textContent=''
                钮.appendChild(图)
                字=文档.createElement('span')
                字.textContent=文 if 文!='' else ' '
                钮.appendChild(字)
            钮.addEventListener('click',点项)
            父.appendChild(钮)
            if 子菜单 is not None and 条目['submenuOpen'] is True:#子开
                子列=文档.createElement('div')
                子列.className='子菜单'
                画条目(子菜单,子列)
                父.appendChild(子列)
    def 重画():
        '按开合重画列表'
        清空(根)
        画子(锚内容,根)#锚
        if getattr(菜单,'拆外面',None) is not None:
            菜单.拆外面()
            菜单.拆外面=None
        if getattr(菜单,'拆键',None) is not None:
            菜单.拆键()
            菜单.拆键=None
        if getattr(菜单,'拆锚',None) is not None:
            菜单.拆锚()
            菜单.拆锚=None
        if getattr(菜单,'表面',None) is not None and 菜单.表面.背板 is not None:
            菜单.表面.背板.remove()
            菜单.表面.背板=None
            菜单.表面=None
        if 态['开'] is False:#关
            return#只留锚
        表面=菜单表面({
            'window':window,
            'compact':属性.get('compact') is True,
            'className':'菜单列',
            'role':'menu',
        })
        列=表面.渲染()
        菜单.表面=表面
        画条目(菜单.规范化条目(条目列),列)#条目
        脚=菜单.规范化条目(脚列)#脚
        if len(脚)>0:
            脚盒=文档.createElement('div')
            脚盒.className='菜单脚'
            画条目(脚,脚盒)#脚
            列.appendChild(脚盒)
        传送=属性.get('portal') is True
        if 传送:
            文档.body.appendChild(列)
            列.style.visibility='hidden'
            def 放置():
                '传送菜单跟着锚，滚动和缩放都重测，顶边距读窗框'
                矩形=根.getBoundingClientRect()
                宽=列.offsetWidth if 列.offsetWidth is not None else 0
                高=列.offsetHeight if 列.offsetHeight is not None else 0
                顶边距=覆盖层顶边距(视口边距)
                if 侧=='right':
                    左=矩形.right+4
                    顶=矩形.top
                elif 对齐=='start':
                    左=矩形.left
                    顶=矩形.bottom+4 if 侧=='bottom' else 矩形.top-高-4
                else:
                    左=矩形.right-宽
                    顶=矩形.bottom+4 if 侧=='bottom' else 矩形.top-高-4
                if 宽>0:
                    if 左<视口边距:
                        左=视口边距
                    右限=window.innerWidth-宽-视口边距
                    if 左>右限:
                        左=右限
                if 高>0:
                    if 顶<顶边距:
                        顶=顶边距
                    下限=window.innerHeight-高-视口边距
                    if 顶>下限:
                        顶=下限
                列.style.position='fixed'
                列.style.left=str(左)+'px'
                列.style.top=str(顶)+'px'
                列.style.visibility='visible'
            放置()
            window.addEventListener('scroll',放置,True)
            window.addEventListener('resize',放置)
            菜单.拆锚=lambda: (
                window.removeEventListener('scroll',放置,True),
                window.removeEventListener('resize',放置),
            )
        else:
            根.appendChild(列)
            菜单.拆锚=None
        def 置关(开着):
            '点外面关掉'
            if 开着:
                return
            态['开']=False
            重画()
            if 关回调 is not None:
                关回调()
        if getattr(菜单,'拆外面',None) is not None:
            菜单.拆外面()
        菜单.拆外面=点外关闭(根,True,置关,列 if 传送 else None)
        def 按键(事件):
            'Escape 关掉'
            if 事件.key!='Escape':
                return
            置关(False)
        文档.addEventListener('keydown',按键)
        菜单.拆键=lambda: 文档.removeEventListener('keydown',按键)
    def 离开(事件):
        '指针离开则关闭'
        if 离开关 is False:#不关
            return
        态['开']=False#关
        重画()#重画
        if 关回调 is not None:
            关回调()#调用
    根.addEventListener('mouseleave',离开)#离开
    重画()#首画
    if 'parent' in 属性:
        属性['parent'].appendChild(根)
    return 根

class 菜单:#锚定下拉
    '业主控 open；点外/Escape 关'
    def __init__(自身,属性=None,**关键字参数):
        '合并 props。构造不画'
        自身.属性=dict(属性 if 属性 is not None else {})#基础
        自身.属性.update(关键字参数)#覆盖
        自身.开子菜单=None#子菜单 id
        自身.根=None

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
        '拆掉旧菜单，再画一次'
        if 自身.根 is not None:
            自身.根.remove()
        绘制=dict(自身.属性)
        绘制['菜单']=自身
        自身.根=处理菜单(自身.属性['window'],绘制)
        return 自身.根

    def __call__(自身,属性=None,**关键字参数):
        '对齐 React'
        if 属性 is not None or len(关键字参数)>0:#有；判 length
            合并=dict(属性 if 属性 is not None else {})#基
            合并.update(关键字参数)#覆
            自身.更新(合并)#刷
        return 自身.渲染()
