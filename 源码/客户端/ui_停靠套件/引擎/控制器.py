from .约束 import 可分割#限额
from .初值 import 创建标识铸造,创建初始状态#初值
from .规划 import (#规划
    活动停靠窗格标识 as _活动停靠,
    规划加标签,
    规划投放标签,
    规划复制标签,
    规划浮出标签,
    规划打开内容,
    规划安置标签,
    规划调整分割,
    规划设展开,
    规划设模式,
    规划分窗格,
    规划收回浮窗,
)#规划结束
from .序列 import 序列器#历史

__all__=['停靠快照','停靠控制器']#仅中文公开名


class 停靠快照:
    """渲染层只读的一份布局与限额快照。"""

    def __init__(自身,状态,可撤销,可重做,可分割标志,操作数,游标):
        """记下字段。"""
        自身.状态=状态#layout
        自身.可撤销=可撤销#undo
        自身.可重做=可重做#redo
        自身.可分割=可分割标志#budget
        自身.操作数=操作数#含重做枝
        自身.游标=游标#已施加意图数


class 停靠控制器:
    """一面：历史、限额、变更通知；满足停靠意图约定方法名。"""

    def __init__(自身,选项=None):
        """选项 dict 可含 makeInitialTab / makePaneTab / mode。"""
        if 选项 is None:#默认
            选项={}#空
        自身._铸造=创建标识铸造()#可调用
        自身._造窗格标签=选项['makePaneTab'] if 'makePaneTab' in 选项 else None#工厂
        模式=选项['mode'] if 'mode' in 选项 else None#模式
        造首=选项['makeInitialTab'] if 'makeInitialTab' in 选项 else None#首
        if 模式 is None:#默认推挤
            初=创建初始状态(自身._铸造,造首)#初
        else:#显式模式
            初=创建初始状态(自身._铸造,造首,模式)#初
        自身._序列=序列器(初)#序列
        自身._监听者=set()#订阅
        自身._快照=自身._建快照()#首快照

    def 订阅(自身,监听):
        """观察布局变更；返回拆除器。"""
        自身._监听者.add(监听)#登记
        def 拆除():
            """移除。"""
            自身._监听者.discard(监听)#去
        return 拆除#拆除器

    def 取快照(自身):
        """当前快照；布局不变则同一引用。"""
        return 自身._快照#快照

    @property
    def 操作表(自身):
        """已记操作（含重做枝）。"""
        return 自身._序列.操作表#表

    def _建快照(自身):
        """自序列器建快照。"""
        状态=自身._序列.状态#态
        return 停靠快照(#快照
            状态,
            自身._序列.可撤销,
            自身._序列.可重做,
            可分割(状态),
            len(自身._序列.操作表),
            自身._序列.游标,
        )#结束

    def _提交(自身):
        """换快照并通知。"""
        自身._快照=自身._建快照()#新
        for 监听 in list(自身._监听者):#派发
            监听()#回调

    @property
    def _状态(自身):
        """当前布局。"""
        return 自身._序列.状态#态

    def _运行(自身,操作表):
        """录一意图；空则 False。"""
        if 操作表 is None or len(操作表)==0:#空
            return False#未录
        自身._序列.派发全部(操作表)#录
        自身._提交()#通知
        return True#已录

    def 设展开(自身,展开):
        """展开或折叠停靠区。"""
        自身._运行(规划设展开(自身._状态,展开))#跑

    def 切换展开(自身):
        """翻转展开。"""
        自身.设展开(not 自身._状态['expanded'])#翻

    def 设模式(自身,模式):
        """切换呈现。"""
        自身._运行(规划设模式(自身._状态,模式))#跑

    def 打开内容(自身,入):
        """打开或聚焦；返回 tabId。入为 dict。"""
        规划=规划打开内容(自身._状态,自身._铸造,入)#规划
        自身._运行(规划['ops'])#跑
        return 规划['tabId']#落点

    def 撤销(自身):
        """撤销；无可退返回 False。"""
        if not 自身._序列.撤销():#无
            return False#否
        自身._提交()#通知
        return True#成

    def 重做(自身):
        """重做；无可进返回 False。"""
        if not 自身._序列.重做():#无
            return False#否
        自身._提交()#通知
        return True#成

    def 活动停靠窗格标识(自身):
        """新标签落点窗格。"""
        return _活动停靠(自身._状态)#窗

    def focusTab(自身,tabId):
        """聚焦标签。"""
        自身._运行([{'type':'focusTab','tabId':tabId}])#跑

    def focusPane(自身,paneId):
        """聚焦窗格。"""
        自身._运行([{'type':'focusPane','paneId':paneId}])#跑

    def splitPane(自身,paneId=None):
        """分割窗格。"""
        return 自身._运行(规划分窗格(自身._状态,自身._铸造,paneId,自身._造窗格标签))#跑

    def addTab(自身,paneId):
        """条带加签。"""
        return 自身._运行(规划加标签(自身._状态,自身._铸造,paneId,自身._造窗格标签))#跑

    def closeTab(自身,tabId):
        """关标签。"""
        自身._运行([{'type':'closeTab','tabId':tabId}])#跑

    def duplicateTab(自身,tabId):
        """复制；返回新 tabId。"""
        规划=规划复制标签(自身._状态,自身._铸造,tabId)#规划
        自身._运行(规划['ops'])#跑
        return 规划['tabId']#新

    def floatTab(自身,tabId,rect=None):
        """浮出；返回新 paneId。"""
        规划=规划浮出标签(自身._状态,自身._铸造,tabId,rect)#规划
        自身._运行(规划['ops'])#跑
        return 规划['paneId']#浮窗

    def unfloatPane(自身,paneId,toPaneId=None):
        """收回浮动。"""
        自身._运行(规划收回浮窗(自身._状态,paneId,toPaneId))#跑

    def placeTab(自身,tabId,toPaneId,index):
        """安放；无变返回 False。"""
        return 自身._运行(规划安置标签(自身._状态,tabId,toPaneId,index))#跑

    def dropTab(自身,tabId,targetPaneId,zone):
        """投放；无变返回 False。"""
        return 自身._运行(规划投放标签(自身._状态,自身._铸造,tabId,targetPaneId,zone))#跑

    def moveFloat(自身,paneId,x,y):
        """浮窗平移净位置。"""
        自身._运行([{'type':'moveFloat','paneId':paneId,'x':x,'y':y}])#跑

    def resizeFloat(自身,paneId,rect):
        """浮窗缩放净矩形。"""
        自身._运行([{'type':'resizeFloat','paneId':paneId,'rect':rect}])#跑

    def resizeSplit(自身,splitId,sizes):
        """分隔净份额。"""
        自身._运行(规划调整分割(splitId,sizes))#跑
