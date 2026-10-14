from nicegui import ui as 界面
from .异常 import 叠页面失败

__all__=['附件轨','滚轮行像素']#仅中文公开名

滚轮行像素=16#LINE 模式每步近似像素

class 附件轨:#水平缩略图轨
    '草稿附件缩略图轨；拥有方仅在有条目时挂载'
    def __init__(自身,属性):#构造
        '记下 props'
        自身.属性=属性#合成 props
        自身.滚动左=0#scrollLeft
        自身.滚动宽=0#scrollWidth
        自身.可视宽=0#clientWidth
        自身.上次条数=None#首次布局为 None
        自身.左缘=False#尚未几何时无左箭
        自身.右缘=False#尚未几何时无右箭
        自身.存活=True#存活
        自身.画面失败=None

    def 更新(自身,属性):#props 变更
        '条数增长时滚到末尾'
        旧表=自身.属性['items'] if 'items' in 自身.属性 and 自身.属性['items'] is not None else []#旧条目；空列表保留
        旧条=len(旧表)#旧条数；判的是 length
        自身.属性=属性#最新
        新表=自身.属性['items'] if 'items' in 自身.属性 and 自身.属性['items'] is not None else []#新条目；空列表保留
        新条=len(新表)#新条数；判的是 length
        if 自身.上次条数 is not None and 新条>自身.上次条数:#增长
            自身.滚动左=max(0,自身.滚动宽-自身.可视宽)#末尾
        自身.上次条数=新条#记下
        if 旧条!=新条:#条数变
            自身.刷新边缘()#刷新

    def 卸载(自身):#卸载
        '标死'
        自身.存活=False#死

    def 设几何(自身,滚动左,滚动宽,可视宽):#由宿主写入滚动几何
        '更新几何并刷新边缘'
        自身.滚动左=滚动左#左
        自身.滚动宽=滚动宽#宽
        自身.可视宽=可视宽#可视
        自身.刷新边缘()#边缘

    def 刷新边缘(自身):#重算左右箭头
        '1px 松弛：引擎在边缘报分数滚动'
        自身.左缘=自身.滚动左>1#左可滚
        自身.右缘=自身.滚动左<自身.滚动宽-自身.可视宽-1#右可滚

    def 翻页(自身,方向):#按视口翻页
        '一步视口减一卡；窄轨至少 200'
        步=方向*max(自身.可视宽-64,200)#步长
        自身.滚动左=max(0,min(自身.滚动左+步,max(0,自身.滚动宽-自身.可视宽)))#夹紧
        自身.刷新边缘()#边缘

    def 滚轮(自身,deltaX,deltaY,deltaMode=0):#垂直滚轮转水平
        '纯水平 pan 保持原生；有垂直分量则消费'
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
        '投影轨与条目'
        条目表=自身.属性['items'] if 'items' in 自身.属性 and 自身.属性['items'] is not None else []#条目；空列表保留
        文案=自身.属性['labels'] if 'labels' in 自身.属性 and 自身.属性['labels'] is not None else {}#文案
        return {#视图
            'group':文案['group'] if 'group' in 文案 else None,#组名
            'open':文案['open'] if 'open' in 文案 else None,#打开提示
            'scrollLeft':文案['scrollLeft'] if 'scrollLeft' in 文案 else None,#左箭头
            'scrollRight':文案['scrollRight'] if 'scrollRight' in 文案 else None,#右箭头
            'showLeft':自身.左缘,#显左箭
            'showRight':自身.右缘,#显右箭
            'scrollLeftPx':自身.滚动左,#滚动位置
            'items':[{#缩略项
                'id':项['id'] if 'id' in 项 else None,#身份
                'previewUrl':项['previewUrl'] if 'previewUrl' in 项 else None,#预览
                'alt':项['alt'] if 'alt' in 项 else None,#替代文本
                'removeLabel':项['removeLabel'] if 'removeLabel' in 项 else None,#移除文案
            } for 项 in 条目表],#项表
        }#视图结束

    def 打开(自身,项):#单击打开
        '转调 onOpen'
        回调=自身.属性['onOpen'] if 'onOpen' in 自身.属性 else None#回调
        if 回调 is not None:#有
            回调(项)#打开

    def 移除(自身,项):#移除
        '转调 onRemove'
        回调=自身.属性['onRemove'] if 'onRemove' in 自身.属性 else None#回调
        if 回调 is not None:#有
            回调(项)#移除

    def 渲染(自身):
        '左右翻页与缩略图、移除'
        视=自身.视图()
        旧=getattr(自身,'根',None)
        if 旧 is not None:
            try:
                旧.clear()
            except Exception as 错误:
                自身.根=None
                自身.画面失败=叠页面失败(自身.画面失败,错误)
        if getattr(自身,'根',None) is None:
            自身.根=界面.row().classes('attachment-rail')
        条目表=自身.属性['items'] if 'items' in 自身.属性 and 自身.属性['items'] is not None else []
        画项=自身.属性['renderItem'] if 'renderItem' in 自身.属性 else None
        with 自身.根:
            if isinstance(自身.画面失败,str) and 自身.画面失败!='':
                界面.label(自身.画面失败)
            组名=视['group']
            if isinstance(组名,str) and 组名!='':
                界面.label(组名).style('position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)')
            if 视['showLeft'] is True and isinstance(视['scrollLeft'],str) and 视['scrollLeft']!='':
                def 点左():
                    '向左翻页'
                    自身.翻页(-1)
                    自身.渲染()
                界面.button(视['scrollLeft'],on_click=点左).props('flat no-caps')
            for 下标,项视 in enumerate(视['items']):
                原项=条目表[下标] if 下标<len(条目表) else 项视
                if callable(画项):
                    画项(原项 if isinstance(原项,dict) else 项视)
                    continue
                if isinstance(项视['previewUrl'],str) and 项视['previewUrl']!='':
                    图=界面.image(项视['previewUrl'])
                    def 点开(_事件=None,项=原项):
                        '打开原图'
                        自身.打开(项)
                    图.on('click',点开)
                elif isinstance(项视['alt'],str) and 项视['alt']!='':
                    界面.label(项视['alt'])
                if isinstance(项视['removeLabel'],str) and 项视['removeLabel']!='':
                    def 点除(_事件=None,项=原项):
                        '移除这条附件'
                        自身.移除(项)
                    界面.button(项视['removeLabel'],on_click=点除).props('flat no-caps')
            if 视['showRight'] is True and isinstance(视['scrollRight'],str) and 视['scrollRight']!='':
                def 点右():
                    '向右翻页'
                    自身.翻页(1)
                    自身.渲染()
                界面.button(视['scrollRight'],on_click=点右).props('flat no-caps')

    def __call__(自身,属性=None):#组件调用形
        '对齐 React 组件调用'
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()
