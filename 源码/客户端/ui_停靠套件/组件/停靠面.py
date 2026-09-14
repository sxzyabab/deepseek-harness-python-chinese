from ..引擎.约束 import 钳制尺寸,浮动默认尺寸,最小窗格份额#约束
from ..引擎.树 import 取分割,右上窗格标识#树
from ..引擎.几何 import 含点,分割条尺寸,落点浮动矩形,插入下标,已过阈值,矩形区位#几何
from .测量 import 取可放,量测窗格可放,可放相同#测量
from .面板回调 import 建面板回调,分割阻断预算#回调
from .指针 import 手势会话#手势
from .窗格树 import 窗格树#树

__all__=['停靠面']#仅中文公开名

_尺寸容差=1e-9#份额同值容差


def _份额相同(甲,乙):
    """两份额表是否同分割。"""
    if len(甲)!=len(乙):#长
        return False#异
    for 序号,份额 in enumerate(甲):#逐
        if abs(份额-乙[序号])>=_尺寸容差:#异
            return False#异
    return True#同


def _命中(#指针落点
    窗格几何表,横,纵,可分割标志,可放表,投放模式,
):
    """窗格几何表为有序 list[{paneId,pane,strip,tabs}]，tabs 为芯片矩形表。"""
    for 项 in 窗格几何表:#逐窗
        窗格标识=项['paneId']#窗
        矩=项['pane']#盒
        if not 含点(矩,横,纵):#外
            continue#下
        条=项['strip']#条带
        if 条 is not None and 含点(条,横,纵):#在条
            return {'kind':'strip','paneId':窗格标识,'index':插入下标(项['tabs'],横)}#条带
        if 投放模式=='horizontal':#水平
            可放=取可放(可放表,窗格标识)#可放
            if 可分割标志 and 可放['row']:#可左右
                区='left' if 横<矩['x']+矩['width']/2 else 'right'#半
            else:#中心
                区='center'#中
        else:#边带
            区=矩形区位(矩,横,纵)#区
        if 区!='center':#边
            可放=取可放(可放表,窗格标识)#可放
            够=可放['row'] if 区=='left' or 区=='right' else 可放['column']#轴
            if not 可分割标志 or not 够:#不可分
                return None#非移动
        return {'kind':'zone','paneId':窗格标识,'zone':区}#区位
    return None#未中


def _拖后份额(拖,横,纵,下限):
    """分隔拖到的钳制份额。"""
    动=(横 if 拖['axis']=='row' else 纵)-拖['origin']#位移
    增量=动/拖['extent'] if 拖['extent']>0 else 0#份额增量
    return 钳制尺寸(分割条尺寸(拖['sizes'],拖['index'],增量),下限)#钳


class 停靠面:
    """分割树与手势驱动；产出结构树。"""

    def __init__(#构造
        自身,状态,可分割标志,意图,文案,渲标签,
        渲标签标题=None,渲菜单附加=None,铬=None,可加标签=None,
        投放模式='edges',最小份额=最小窗格份额,满员藏分割=False,房间回调=None,
    ):
        """记下布局、限额与出口。"""
        自身.状态=状态#布局
        自身.可分割=可分割标志#预算
        自身.意图=意图#意图
        自身.文案=文案#文案
        自身.渲标签=渲标签#正文
        自身.渲标签标题=渲标签标题#标题
        自身.渲菜单附加=渲菜单附加#菜单
        自身.铬=铬#铬
        自身.可加标签=可加标签 if 可加标签 is not None else (lambda _:#恒真
            True
        )#可加
        自身.投放模式=投放模式#edges|horizontal
        自身.最小份额=最小份额#下限
        自身.满员藏分割=满员藏分割#藏
        自身.房间回调=房间回调#onRoom
        自身._预览={'draggingTabId':None,'dropTarget':None,'sizes':None}#预览
        自身._可放={}#量测
        自身._几何表=[]#宿主更新的命中几何
        自身._手势=手势会话(自身._清预览)#手势

    def 更新(自身,**字段):
        """更新构造字段。"""
        for 名,值 in 字段.items():#逐
            setattr(自身,名,值)#挂

    def _清预览(自身):
        """复位手势预览。"""
        自身._预览={'draggingTabId':None,'dropTarget':None,'sizes':None}#空

    def 设窗格几何(自身,几何表):
        """宿主量测后写入：命中用。每项含 paneId/pane/strip/tabs。"""
        自身._几何表=list(几何表)#表

    def 重测可放(自身,窗格测量表):
        """宿主量测后更新房间规则；有变则回调。"""
        下一=量测窗格可放(窗格测量表)#可放
        if 可放相同(自身._可放,下一):#无变
            return#止
        自身._可放=下一#换
        if 自身.房间回调 is not None:#通知
            自身.房间回调(下一)#房间

    def _分割阻断(自身,窗格标识):
        """预算优先，再宽度。"""
        if not 自身.可分割:#满
            return 分割阻断预算#预算
        return None if 取可放(自身._可放,窗格标识)['row'] else 'width'#宽

    def _标签按下(自身,标签标识,事件):
        """芯片按下：阈值后拖，释放报意图。"""
        起横=事件['clientX']#x
        起纵=事件['clientY']#y
        拖中=[False]#可变

        def 移动(事):
            """移动。"""
            横=事['clientX']#x
            纵=事['clientY']#y
            if not 拖中[0]:#尚未
                if not 已过阈值(起横,起纵,横,纵):#未过
                    return#等
                拖中[0]=True#开始
            自身._预览={#预览
                'draggingTabId':标签标识,
                'dropTarget':_命中(自身._几何表,横,纵,自身.可分割,自身._可放,自身.投放模式),
                'sizes':None,
            }#预览

        def 抬起(事):
            """释放。"""
            if not 拖中[0]:#点击
                return#无报
            横=事['clientX']#x
            纵=事['clientY']#y
            目标=_命中(自身._几何表,横,纵,自身.可分割,自身._可放,自身.投放模式)#命中
            if 目标 is None:#区外或不可分
                面=事['surface'] if 'surface' in 事 else None#可选面矩形
                if 面 is not None and 含点(面,横,纵):#面内无窗
                    return#非移动
                自身.意图.floatTab(标签标识,落点浮动矩形(横,纵,浮动默认尺寸))#浮出
                return#止
            if 目标['kind']=='strip':#条带
                自身.意图.placeTab(标签标识,目标['paneId'],目标['index'])#安放
            else:#区位
                自身.意图.dropTab(标签标识,目标['paneId'],目标['zone'])#投放

        return 自身._手势.开始(移动,抬起)#喂入

    def _分隔按下(自身,分割标识,下标,事件):
        """分隔按下。事件需含 extent（轴长）。"""
        分割=取分割(自身.状态,分割标识)#分割
        拖={#拖态
            'splitId':分割标识,
            'index':下标,
            'axis':分割['axis'],
            'origin':事件['clientX'] if 分割['axis']=='row' else 事件['clientY'],
            'extent':事件['extent'],
            'sizes':list(分割['sizes']),
        }#拖

        def 移动(事):
            """预览份额。"""
            自身._预览={#预览
                'draggingTabId':None,
                'dropTarget':None,
                'sizes':{'splitId':分割标识,'sizes':_拖后份额(拖,事['clientX'],事['clientY'],自身.最小份额)},
            }#预览

        def 抬起(事):
            """落定。"""
            份额=_拖后份额(拖,事['clientX'],事['clientY'],自身.最小份额)#终
            if _份额相同(份额,拖['sizes']):#未变
                return#无
            自身.意图.resizeSplit(分割标识,份额)#报

        return 自身._手势.开始(移动,抬起)#喂入

    def 渲染(自身):
        """结构树。"""
        回调=建面板回调(#回调
            自身.意图.focusTab,
            自身.意图.focusPane,
            自身.意图.splitPane,
            自身.意图.addTab,
            自身.意图.closeTab,
            自身._标签按下,
            自身._分隔按下,
            自身._分割阻断,
            自身.可加标签,
            自身._预览['dropTarget'],
            自身._预览['draggingTabId'],
            自身.文案,
            自身.渲标签,
            自身.渲标签标题,
            自身.渲菜单附加,
            右上窗格标识(自身.状态),
            自身.铬,
            自身.满员藏分割,
            自身.投放模式=='horizontal',
        )#结束
        return {#面
            'type':'surface',
            'data':'dockkit-surface',
            'dropZones':自身.投放模式,
            'child':窗格树(自身.状态,自身.状态['rootId'],回调,自身._预览['sizes']).渲染(),
        }#结束
