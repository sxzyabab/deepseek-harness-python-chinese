"""轨迹时间线：Chrome-Network 式总览，聚焦账本选区。

对齐上游 `TrajectoryTimeline.tsx` + `TrajectoryTimeline.module.css`。公开面仅中文名。
样式正文落在同目录 轨迹时间线.module.css；本模块读成 样式表，并提供结构树视图与手势逻辑。
"""
import math#有限数判定
import os#同目录样式路径
from datetime import datetime#记录时刻格式化
from .时间线 import 派生轨迹时间线,格式化时间线偏移#模型派生
from .轨迹记录 import 取字段#字段读取

__all__=[#仅中文公开名
    '样式表',
    '样式文件',
    '轨迹时间线',
    '最小拖动像素',
    '最小缩放操作数',
    '边平移区比例',
    '边平移步进比例',
    '最大边平移像素',
    '时间线提示延迟毫秒',
]#公开面结束

_本目录=os.path.dirname(os.path.abspath(__file__))#本包目录
样式文件='轨迹时间线.module.css'#上游单文件
最小拖动像素=3#拖动阈值
最小缩放操作数=4#序列模式最小可见操作数
边平移区比例=0.08#轨道边缘平移带
边平移步进比例=0.025#边缘平移步进
最大边平移像素=32#边缘带像素上限
时间线提示延迟毫秒=500#Tooltip 延迟

def _读样式(文件名):#读真实 CSS
    """从同目录读取样式正文。"""
    路径=os.path.join(_本目录,文件名)#绝对路径
    with open(路径,'r',encoding='utf-8') as 文件:#读文件
        return 文件.read()#全文

样式表=_读样式(样式文件)#完整时间线样式

def 助手计时明细(指标):#从助手指标拆 TTFT/解码
    """有完整计时则返回 ttftMs/decodingMs，否则空映射。"""
    起点=取字段(指标,'stepStartTime')#步进起点
    首词=取字段(指标,'firstTokenTime')#首 token
    完成=取字段(指标,'completedTime')#完成
    if (取字段(指标,'timingRecorded') is not True#未记录
            or not isinstance(起点,(int,float)) or not math.isfinite(起点)#起点无效
            or not isinstance(首词,(int,float)) or not math.isfinite(首词)#首词无效
            or not isinstance(完成,(int,float)) or not math.isfinite(完成)#完成无效
            or 首词<起点 or 完成<首词):#时序颠倒
        return {}#无明细
    return {'ttftMs':首词-起点,'decodingMs':完成-首词}#TTFT 与解码

def 时间线记录明细(单元格):#格子的时长/起点/助手计时
    """从格子合成 Tooltip 用明细。"""
    秒=取字段(单元格,'timeSeconds')#秒时长
    时长毫秒=None if 秒 is None or not isinstance(秒,(int,float)) or not math.isfinite(秒) else max(0,秒*1000)#毫秒
    起点=取字段(单元格,'startedAt')#起点
    起点值=None if 起点 is None or not isinstance(起点,(int,float)) or not math.isfinite(起点) else 起点#有限起点
    明细={}#累加
    if 时长毫秒 is not None:#有时长
        明细['durationMs']=时长毫秒#总时长
    if 起点值 is not None:#有起点
        明细['startedAt']=起点值#起点
    明细.update(助手计时明细(取字段(单元格,'assistantMetrics')))#助手计时
    return 明细#明细

def 时间线种类标签(种类):#种类 → Tooltip 标题
    """格子种类的大写展示名。"""
    表={#种类标签
        'system':'SYSTEM','user':'USER','context':'CONTEXT','compacted':'COMPACTED',
        'message':'ASSISTANT','tool':'TOOL','subtool':'SUBTOOL',
    }#表结束
    return 表.get(种类,种类)#缺省原样

def 格式化记录时刻(时间戳):#本地时分秒.毫秒
    """把毫秒时间戳格式成本地时刻串。"""
    时刻=datetime.fromtimestamp(时间戳/1000.0)#秒级 datetime
    return 时刻.strftime('%H:%M:%S.')+f'{int(时刻.microsecond/1000):03d}'#含毫秒

def 时间线提示文案(种类,明细=None):#跨度 Tooltip
    """种类标题 + 起止时刻 + TTFT/解码。"""
    标题=时间线种类标签(种类)#标题行
    if 明细 is None:#无明细
        return 标题#仅标题
    时长=None if 取字段(明细,'durationMs') is None else f"Total {格式化时间线偏移(明细['durationMs'])}"#总时长行
    起点=取字段(明细,'startedAt')#起点
    时长毫秒=取字段(明细,'durationMs')#时长
    if 起点 is None:#无起点
        区间=None#无区间行
    elif 时长毫秒 is None:#仅起点
        区间=f'Started {格式化记录时刻(起点)}'#起点行
    else:#起止
        区间=f'{格式化记录时刻(起点)} → {格式化记录时刻(起点+时长毫秒)}'#区间行
    ttft=取字段(明细,'ttftMs')#TTFT
    解码=取字段(明细,'decodingMs')#解码
    分段=None if ttft is None or 解码 is None else f'TTFT {格式化时间线偏移(ttft)} · Decoding {格式化时间线偏移(解码)}'#分段行
    计时=' · '.join(段 for 段 in (时长,分段) if 段)#计时行
    return '\n'.join(段 for 段 in (标题,区间,计时) if 段)#多行提示

def 有序区间(左,右):#小数闭区间按序
    """保证 start<=end。"""
    return {'start':左,'end':右} if 左<=右 else {'start':右,'end':左}#有序

def 钳制比例(值):#钳到 [0,1]
    """把比例钳到单位区间。"""
    return min(1,max(0,值))#钳制

def 居中区间(中心,宽度,最小,最大):#在域内居中一段宽度
    """以中心铺开宽度，钳在 [最小,最大]。"""
    钳宽=min(最大-最小,max(0,宽度))#合法宽度
    起点=min(max(中心-钳宽/2,最小),最大-钳宽)#起点
    return {'start':起点,'end':起点+钳宽}#闭区间

def 区间比例(区间,起点,时长,最小,最大):#选区 → 轨道比例
    """把投影选区换成相对当前域的比例区间。"""
    有界=有序区间(#先钳进域
        min(最大,max(最小,取字段(区间,'start'))),#起点
        min(最大,max(最小,取字段(区间,'end'))),#终点
    )#有界结束
    return {#比例
        'start':(有界['start']-起点)/时长,#左
        'end':(有界['end']-起点)/时长,#右
    }#比例结束

def 车道标签结构():#三车道标签
    """Input / Model / Tools。"""
    return {#标签列
        'type':'lane-labels','ariaHidden':True,#无障碍隐藏
        'items':['Input','Model','Tools'],#三道
    }#结束

def 更早历史边界结构(加载中,可加载):#截断前缀控件
    """加载更早历史的省略按钮结构。"""
    return {#按钮
        'type':'earlier-history',#类型
        'loading':加载中,#加载中
        'disabled':加载中 or not 可加载,#禁用
        'label':'Loading earlier history…' if 加载中 else 'Click to load earlier history',#提示
        'aria':'Loading earlier history' if 加载中 else 'Load earlier history',#无障碍
        'text':'…',#省略号
        'delayMs':时间线提示延迟毫秒,#提示延迟
    }#结束

class 轨迹时间线:#全域总览时间线
    """拖选区间、点击聚焦、滚轮缩放、右键平移、Escape 清空。"""
    def __init__(自身,属性=None):#可选 props
        """记下 props 与手势/视口状态。"""
        自身.属性=属性 or {}#合成
        自身.草稿=None#拖选草稿区间
        自身.悬停=None#悬停比例点
        自身.加载更早中=False#更早历史加载中
        自身.平移中=False#右键平移中
        自身.视口=None#缩放视口
        自身.动画视口=False#选中跟随时动画
        自身._拖动手势=None#左键拖选
        自身._平移手势=None#右键平移

    def 更新(自身,属性):#刷新 props
        """刷新 props，并校正越界选区/视口。"""
        自身.属性=属性 or {}#新
        自身._校正选区()#越界则清空
        自身._校正视口()#越界则清空视口

    def _轮次(自身):#当前轮次布局
        """从 props 取未过滤轮次。"""
        return 取字段(自身.属性,'turns') or []#轮次

    def _模式(自身):#投影模式
        """sequence / duration / time / actual。"""
        return 取字段(自身.属性,'mode','sequence')#默认序列

    def _选区(自身):#已提交选区
        """当前焦点闭区间。"""
        return 取字段(自身.属性,'range')#可空

    def _模型(自身):#派生全域模型
        """没有可见记录时为 None。"""
        return 派生轨迹时间线(自身._轮次(),自身._模式())#派生

    def _明细表(自身):#下标 → 记录明细
        """摊平全部格子的 Tooltip 明细。"""
        表={}#下标映射
        for 轮 in 自身._轮次():#逐回合
            for 组 in 取字段(轮,'groups') or []:#各组
                for 单元格 in 取字段(组,'cells') or []:#各格
                    表[取字段(单元格,'index')]=时间线记录明细(单元格)#记下
        return 表#明细表

    def _校正选区(自身):#选区越界则清空
        """模型与选区不相交时回调清空。"""
        模型=自身._模型()#模型
        区间=自身._选区()#选区
        if 模型 is None or 区间 is None:#无模型或无选区
            return#无需
        if 取字段(区间,'end')<模型['start'] or 取字段(区间,'start')>模型['end']:#不相交
            回调=取字段(自身.属性,'onRangeChange')#清空回调
            if callable(回调):#有
                回调(None)#清空

    def _校正视口(自身):#视口越界则清空
        """模型切换后视口越界则丢弃。"""
        模型=自身._模型()#模型
        if 模型 is None:#无模型
            return#无需
        自身.动画视口=False#关掉动画
        当前=自身.视口#视口
        if 当前 is not None and (当前['end']<模型['start'] or 当前['start']>模型['end']):#越界
            自身.视口=None#清空

    def _跟随选中(自身):#选中跨度滚进视口
        """选中记录不在当前视口时平移视口。"""
        模型=自身._模型()#模型
        选中下标=取字段(自身.属性,'selectedIndex')#选中
        if 模型 is None or 选中下标 is None:#无
            return#无需
        选中跨=next((跨 for 跨 in 模型['spans'] if 跨['index']==选中下标),None)#找跨度
        if 选中跨 is None:#无
            return#无需
        当前=自身.视口#视口
        if 当前 is None:#全域
            return#不跟
        if 选中跨['end']>当前['start'] and 选中跨['start']<当前['end']:#已可见
            return#保持
        自身.动画视口=True#开动画
        时长=max(1,当前['end']-当前['start'])#当前视口宽
        期望起点=选中跨['start'] if 选中跨['end']<=当前['start'] else 选中跨['end']-时长#跟到左或右
        下一起点=min(max(期望起点,模型['start']),max(模型['start'],模型['end']-时长))#钳域
        if 下一起点==当前['start']:#未变
            return#保持
        自身.视口={'start':下一起点,'end':下一起点+时长}#新视口

    def _域几何(自身,模型):#当前投影域几何
        """全时长、视口时长、域起点、域时长。"""
        全时长=max(1,(模型['end'] if 模型 else 0)-(模型['start'] if 模型 else 0))#全域宽
        视口=自身.视口#视口
        视口时长=min(全时长,max(1,(视口['end'] if 视口 else 0)-(视口['start'] if 视口 else 0)))#视口宽
        if 模型 is None or 视口 is None:#全域
            视口起点=模型['start'] if 模型 else 0#起点
        else:#钳视口
            视口起点=min(max(视口['start'],模型['start']),模型['end']-视口时长)#钳
        域时长=全时长 if 视口 is None else 视口时长#当前域宽
        域起点=模型['start'] if 模型 and 视口 is None else (0 if 模型 is None else 视口起点)#当前域起
        return {#几何包
            'fullDuration':全时长,#全
            'viewportDuration':视口时长,#视口
            'viewportStart':视口起点,#视口起
            'domainDuration':域时长,#域宽
            'domainStart':域起点,#域起
        }#结束

    def _投影域样式(自身,模型,几何):#CSS 变量
        """把全域相对当前视口写成 CSS 变量。"""
        if 模型 is None:#无模型
            return None#无
        域起=几何['domainStart']#域起
        域宽=几何['domainDuration']#域宽
        全宽=几何['fullDuration']#全宽
        return {#变量
            '--trajectory-domain-left':f'{-(域起-模型["start"])/域宽*100}%',#左偏移
            '--trajectory-domain-width':f'{全宽/域宽*100}%',#宽度比
        }#结束

    def _改选区(自身,区间):#提交选区
        """回调宿主写入 range。"""
        回调=取字段(自身.属性,'onRangeChange')#回调
        if callable(回调):#有
            回调(区间)#写入

    def _比例于(自身,客户X,轨道左,轨道宽):#客户坐标 → 比例
        """指针在轨道上的 [0,1] 位置。"""
        return 钳制比例((客户X-轨道左)/max(1,轨道宽))#比例

    def 处理动作(自身,动作,载荷=None):#分发手势与键盘
        """pointer/wheel/key/load-earlier 等动作。"""
        载荷=载荷 or {}#载荷
        模型=自身._模型()#模型
        几何=自身._域几何(模型)#几何
        域起=几何['domainStart']#域起
        域宽=几何['domainDuration']#域宽
        全宽=几何['fullDuration']#全宽
        if 动作=='sync-selected':#跟选中
            自身._跟随选中()#跟视口
            return 自身.渲染()#重渲
        if 动作=='load-earlier':#加载更早
            加载=取字段(自身.属性,'onLoadEarlier')#注入
            if 自身.加载更早中 or not callable(加载):#不可
                return False#失败
            自身.加载更早中=True#标记
            try:#执行
                return 加载()#返回是否变了
            finally:#收尾
                自身.加载更早中=False#清除
        if 动作=='keydown':#键盘
            if 取字段(载荷,'key')=='Escape' and 自身._选区() is not None:#Escape
                自身._改选区(None)#清空
            return 自身.渲染()#重渲
        if 动作=='dblclick':#双击清空
            自身._改选区(None)#清空
            return 自身.渲染()#重渲
        if 动作=='pointer-leave':#离开轨道
            if 自身._拖动手势 is None and 自身._平移手势 is None:#无手势
                自身.悬停=None#清悬停
            return 自身.渲染()#重渲
        if 动作=='pointer-cancel':#取消
            自身._拖动手势=None#清拖
            自身._平移手势=None#清平移
            自身.草稿=None#清草稿
            自身.悬停=None#清悬停
            自身.平移中=False#清标记
            return 自身.渲染()#重渲
        if 动作=='wheel':#滚轮缩放
            if 模型 is None:#无模型
                return 自身.渲染()#重渲
            自身.动画视口=False#关动画
            锚比例=钳制比例(取字段(载荷,'fraction',0.5))#锚点比例
            增量=取字段(载荷,'deltaY',0)#滚轮增量
            最小宽=min(最小缩放操作数 if 自身._模式()=='sequence' else 20,全宽)#最小可见
            下一宽=min(全宽,max(最小宽,域宽*math.exp(增量*0.0015)))#指数缩放
            if 下一宽>=全宽*0.999:#接近全域
                自身.视口=None#恢复全域
                return 自身.渲染()#重渲
            锚时刻=域起+锚比例*域宽#锚时刻
            下一起=min(max(锚时刻-锚比例*下一宽,模型['start']),模型['end']-下一宽)#新起点
            自身.视口={'start':下一起,'end':下一起+下一宽}#视口
            return 自身.渲染()#重渲
        if 动作=='pointer-down':#按下
            按钮=取字段(载荷,'button',0)#键
            客户X=取字段(载荷,'clientX',0)#X
            指针标识=取字段(载荷,'pointerId',0)#指针
            记录下标=取字段(载荷,'recordIndex')#记录
            比例=自身._比例于(客户X,取字段(载荷,'trackLeft',0),取字段(载荷,'trackWidth',1))#比例
            if 按钮==2:#右键平移
                自身._平移手势={#记下
                    'anchorClientX':客户X,#锚 X
                    'anchorStart':域起,#锚域起
                    'moved':False,#是否移动
                    'pannable':自身.视口 is not None,#仅缩放后可平移
                    'pointerId':指针标识,#指针
                }#手势
                if 自身.视口 is not None:#有视口
                    自身.动画视口=False#关动画
                自身.平移中=True#标记
                return 自身.渲染()#重渲
            if 按钮!=0:#非左键
                return 自身.渲染()#忽略
            锚时刻=域起+比例*域宽#锚时刻
            自身.悬停={'fraction':比例,'recordIndex':记录下标}#悬停
            自身._拖动手势={#拖选
                'pointerId':指针标识,#指针
                'anchorTime':锚时刻,#锚时刻
                'anchorClientX':客户X,#锚 X
                'recordIndex':记录下标,#记录
            }#手势
            自身.草稿={'start':锚时刻,'end':锚时刻}#点选草稿
            return 自身.渲染()#重渲
        if 动作=='pointer-move':#移动
            客户X=取字段(载荷,'clientX',0)#X
            轨道左=取字段(载荷,'trackLeft',0)#左
            轨道宽=取字段(载荷,'trackWidth',1)#宽
            比例=自身._比例于(客户X,轨道左,轨道宽)#比例
            记录下标=取字段(载荷,'recordIndex')#记录
            自身.悬停={'fraction':比例,'recordIndex':记录下标}#悬停
            平移=自身._平移手势#平移手势
            指针标识=取字段(载荷,'pointerId',0)#指针
            if 平移 is not None and 平移['pointerId']==指针标识:#右键平移中
                if abs(客户X-平移['anchorClientX'])>=最小拖动像素:#过阈值
                    平移['moved']=True#记移动
                if not 平移['pannable'] or 模型 is None:#不可平移
                    return 自身.渲染()#重渲
                增量=(客户X-平移['anchorClientX'])/max(1,轨道宽)#比例增量
                下一起=min(max(平移['anchorStart']-增量*域宽,模型['start']),模型['end']-域宽)#新起点
                自身.视口={'start':下一起,'end':下一起+域宽}#视口
                return 自身.渲染()#重渲
            拖动=自身._拖动手势#拖选手势
            if 拖动 is None or 拖动['pointerId']!=指针标识 or 模型 is None:#无拖选
                return 自身.渲染()#重渲
            下一域起=域起#默认
            if 自身.视口 is not None:#缩放态可边缘平移
                局部X=客户X-轨道左#局部
                边宽=min(最大边平移像素,max(1,轨道宽*边平移区比例))#边带
                方向=-1 if 局部X<边宽 else (1 if 局部X>轨道宽-边宽 else 0)#方向
                if 方向!=0:#在边带
                    边距=边宽-局部X if 方向<0 else 局部X-(轨道宽-边宽)#距边
                    强度=钳制比例(边距/边宽)#强度
                    期望=域起+方向*域宽*边平移步进比例*max(0.2,强度)#期望起点
                    下一域起=min(max(期望,模型['start']),模型['end']-域宽)#钳
                    if 下一域起!=域起:#变了
                        自身.动画视口=False#关动画
                        自身.视口={'start':下一域起,'end':下一域起+域宽}#视口
            点时刻=下一域起+比例*域宽#当前时刻
            自身.草稿=有序区间(拖动['anchorTime'],点时刻)#草稿选区
            return 自身.渲染()#重渲
        if 动作=='pointer-up':#抬起
            客户X=取字段(载荷,'clientX',0)#X
            轨道左=取字段(载荷,'trackLeft',0)#左
            轨道宽=取字段(载荷,'trackWidth',1)#宽
            比例=自身._比例于(客户X,轨道左,轨道宽)#比例
            记录下标=取字段(载荷,'recordIndex')#记录
            指针标识=取字段(载荷,'pointerId',0)#指针
            平移=自身._平移手势#平移
            if 平移 is not None and 平移['pointerId']==指针标识:#结束平移
                已移=平移['moved'] or abs(客户X-平移['anchorClientX'])>=最小拖动像素#是否移动
                自身._平移手势=None#清
                自身.平移中=False#清
                if not 已移:#单击右键清空选区
                    自身._改选区(None)#清空
                return 自身.渲染()#重渲
            拖动=自身._拖动手势#拖选
            if 拖动 is None or 拖动['pointerId']!=指针标识 or 模型 is None:#无拖选
                return 自身.渲染()#重渲
            点时刻=域起+比例*域宽#抬起时刻
            选中=有序区间(拖动['anchorTime'],点时刻)#选区
            自身.悬停={'fraction':比例,'recordIndex':记录下标}#悬停
            自身._拖动手势=None#清拖
            自身.草稿=None#清草稿
            点击=abs(客户X-拖动['anchorClientX'])<最小拖动像素#是否点击
            点中跨=None#点中跨度
            if 点击 and 拖动['recordIndex'] is not None:#点在跨度上
                点中跨=next((跨 for 跨 in 模型['spans'] if 跨['index']==拖动['recordIndex']),None)#找
            if 点中跨 is not None:#点中块
                自身._改选区(None)#清选区
                选记录=取字段(自身.属性,'onRecordSelect')#选记录
                if callable(选记录):#有
                    选记录(点中跨['index'])#选中
                return 自身.渲染()#重渲
            最小选宽=min(域宽,全宽/max(1,len(模型['spans'])))#最小选区宽
            if 选中['end']-选中['start']<最小选宽:#过窄则居中扩
                中心=选中['start'] if 点击 else (选中['start']+选中['end'])/2#中心
                提交=居中区间(中心,最小选宽,模型['start'],模型['end'])#扩
            else:#够宽
                提交=选中#原样
            自身._改选区(提交)#提交
            if 点击:#空白点击聚焦最近
                时间点=选中['start']#点
                def 距离(跨):#到跨度距离
                    if 时间点<跨['start']:#左侧
                        return 跨['start']-时间点#距
                    if 时间点>跨['end']:#右侧
                        return 时间点-跨['end']#距
                    return 0#落在内
                最近=min(模型['spans'],key=距离)#最近跨度
                聚焦=取字段(自身.属性,'onRecordFocus')#聚焦回调
                if callable(聚焦):#有
                    聚焦(最近['index'])#聚焦
            return 自身.渲染()#重渲
        return 自身.渲染()#未知动作重渲

    def 渲染(自身):#结构树
        """产出时间线总览结构树。"""
        自身._校正选区()#先校正
        自身._校正视口()#再校正视口
        模型=自身._模型()#模型
        几何=自身._域几何(模型)#几何
        有更早=bool(取字段(自身.属性,'hasEarlierRecords',False))#截断前缀
        可加载=callable(取字段(自身.属性,'onLoadEarlier'))#有加载
        显示更早边界=有更早 and 模型 is not None and 几何['domainStart']==模型['start']#贴左才显示
        if 模型 is None:#无计时数据
            return {#空态
                'type':'trajectory-timeline',#类型
                'aria':'Trajectory timeline',#无障碍
                'empty':True,#空
                'plot':{#绘图区
                    'labels':车道标签结构(),#车道标签
                    'track':{#轨道
                        'empty':'No timing data',#空文案
                        'earlierHistory':更早历史边界结构(自身.加载更早中,可加载) if 有更早 else None,#更早
                    },#轨道结束
                },#绘图结束
                'css':样式表,#样式
            }#空态结束
        域起=几何['domainStart']#域起
        域宽=几何['domainDuration']#域宽
        全宽=几何['fullDuration']#全宽
        投影样式=自身._投影域样式(模型,几何)#CSS 变量
        选区=自身._选区()#已提交
        已提交比例=None if 选区 is None else 区间比例(选区,域起,域宽,模型['start'],模型['end'])#比例
        草稿比例=None if 自身.草稿 is None else 区间比例(自身.草稿,域起,域宽,模型['start'],模型['end'])#草稿比例
        可见比例=草稿比例 if 草稿比例 is not None else 已提交比例#可见选区
        活动区间=自身.草稿 if 自身.草稿 is not None else 选区#活动区间
        明细表=自身._明细表()#明细
        搜索命中=取字段(自身.属性,'searchMatchIndexes')#搜索
        选中下标=取字段(自身.属性,'selectedIndex')#选中
        模式=自身._模式()#模式
        跨度们=[]#可见跨度结构
        for 跨 in 模型['spans']:#逐跨度
            if not (跨['index']==选中下标 or (跨['end']>=域起 and 跨['start']<=域起+域宽)):#不可见
                continue#跳过
            左=(跨['start']-模型['start'])/全宽#左比例
            宽=(跨['end']-跨['start'])/全宽#宽比例
            宽百分=宽*100#宽%
            明细=明细表.get(跨['index'])#明细
            ttft=取字段(明细,'ttftMs') if 明细 else None#TTFT
            解码=取字段(明细,'decodingMs') if 明细 else None#解码
            ttft比例=None#助手分段
            if ttft is not None and 解码 is not None and ttft+解码>0:#可分段
                ttft比例=ttft/(ttft+解码)#TTFT 占比
            样式变量={#跨度 CSS 变量
                '--trajectory-span-left':f'{左*100}%',#左
                '--trajectory-span-width':f'{宽百分}%',#宽
                '--trajectory-span-gap':f'min({宽百分*0.08}%, 1px)',#缝
                '--trajectory-span-lane':跨['lane'],#车道
            }#变量
            if ttft比例 is not None:#助手分段
                样式变量['--trajectory-assistant-ttft']=f'{ttft比例*100}%'#TTFT 宽
            是否选中=None#选区态
            if 活动区间 is not None:#有活动选区
                是否选中=跨['start']<=取字段(活动区间,'end') and 跨['end']>=取字段(活动区间,'start')#相交
            搜索态=None#搜索态
            if 搜索命中 is not None:#有查询
                搜索态='true' if 跨['index'] in 搜索命中 else 'false'#命中
            跨度们.append({#跨度节点
                'type':'timeline-span',#类型
                'index':跨['index'],#下标
                'kind':跨['kind'],#种类
                'lane':跨['lane'],#车道
                'isError':跨['isError'],#错误
                'label':时间线提示文案(跨['kind'],明细),#提示
                'delayMs':时间线提示延迟毫秒,#延迟
                'assistantTiming':ttft比例 is not None,#助手计时
                'equalDuration':模式=='time',#等时长点
                'current':跨['index']==选中下标,#当前选中记录
                'hovered':自身.悬停 is not None and 自身.悬停.get('recordIndex')==跨['index'],#悬停
                'searchMatch':搜索态,#搜索
                'selected':是否选中,#选区相交
                'style':样式变量,#变量
            })#跨度结束
        边界们=[]#回合边界
        for 边界 in 模型['turnBoundaries']:#逐边界
            时刻=边界['time']#时刻
            if not (时刻>模型['start'] and 时刻>=域起 and 时刻<=域起+域宽):#不可见
                continue#跳过
            边界们.append({#边界节点
                'type':'turn-boundary',#类型
                'turn':边界['turn'],#回合号
                'style':{'--trajectory-turn-left':f'{(时刻-模型["start"])/全宽*100}%'},#位置
            })#边界结束
        悬停线=None#悬停竖线
        if 自身.悬停 is not None and 自身.悬停.get('recordIndex') is None and 自身.草稿 is None:#空白悬停
            悬停线={#竖线
                'type':'hover-line',#类型
                'style':{'--trajectory-hover-left':f'{自身.悬停["fraction"]*100}%'},#位置
            }#竖线结束
        选区层=None#选区层
        if 可见比例 is not None:#有可见选区
            选区样式={#选区变量
                '--trajectory-selection-left':f'{可见比例["start"]*100}%',#左
                '--trajectory-selection-width':f'{(可见比例["end"]-可见比例["start"])*100}%',#宽
            }#变量
            选区层={#选区
                'selection':{'style':选区样式,'dragging':自身.草稿 is not None},#填充
                'selectionEdges':{'style':选区样式,'dragging':自身.草稿 is not None},#边
            }#选区结束
        return {#根
            'type':'trajectory-timeline',#类型
            'aria':'Trajectory timeline',#无障碍
            'empty':False,#非空
            'panning':自身.平移中,#平移中
            'animateViewport':自身.动画视口,#动画
            'domainStyle':投影样式,#域变量
            'plot':{#绘图区
                'labels':车道标签结构(),#车道
                'track':{#轨道
                    'aria':'Timeline overview; drag horizontally to focus events',#无障碍
                    'earlierHistory':更早历史边界结构(自身.加载更早中,可加载) if 显示更早边界 else None,#更早
                    'hoverLine':悬停线,#悬停线
                    'selection':选区层['selection'] if 选区层 else None,#选区
                    'selectionEdges':选区层['selectionEdges'] if 选区层 else None,#边
                    'turnBoundaries':边界们,#边界
                    'spans':跨度们,#跨度
                },#轨道结束
            },#绘图结束
            'css':样式表,#样式
        }#根结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷新
        return 自身.渲染()#渲
