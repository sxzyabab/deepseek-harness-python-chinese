"""轨迹表：分块样式拼装 + 轮次感知事件账本与本地记录检查器。

对齐上游 `ui-trajectory/src/client/TrajectoryTable.tsx` + `TrajectoryTable.module.css`。
公开面仅中文名。React 像素半（虚拟滚动 DOM、指针拖拽）以结构树动作描述；完整 DOM 仍以上游为准。
样式正文按壳/行/详情/载荷/目录分块落盘，本模块拼成 样式表 与 样式分块。
本文件为权威唯一实现；旧 `轨迹表.py` 与同名包 `轨迹表/` 仅废弃说明，勿从彼处导入。
"""
import json#系统提示词工具目录差分
import os#同目录样式路径
from .轨迹记录 import 轨迹记录身份,格式化已用秒数,取字段#记录面
from .虚拟行 import 编组轨迹虚拟行,轨迹虚拟记录键#虚拟行
from .轨迹表投影 import (#投影纯函数
    底部跟随阈值像素,
    更早加载阈值像素,
    历史加载行高像素,
    虚拟化阈值,
    种类标签,
    详情最小宽,
    工具请求占比,
    详情缩放步长,
    请求标签页,
    钳制详情宽,
    默认工具请求宽,
    格式化时长毫秒,
    格式化开始时刻,
    总耗时文案,
    首字耗时文案,
    生成耗时文案,
    吞吐文案,
    展平记录,
    过滤记录,
    请求键,
    索引请求边界,
    段落标签,
    索引请求编号,
    索引请求边界游程,
    折叠轮次记录,
    折叠助手记录,
    记录状态,
    状态标签,
    输入合计,
    消息来源标签,
    父级记录,
    是否Markdown记录,
    Markdown源,
    详情标签页,
    记录呈现,
    解析工具Schema,
    解析JSON容器,
    提示词差分行,
    是否仅工具调用,
)#投影结束

__all__=[#仅中文公开名
    '样式表',
    '样式分块',
    '样式文件',
    '轨迹表',
    '种类样式类',
]#公开面结束

_本目录=os.path.dirname(os.path.abspath(__file__))#本包目录
样式文件='轨迹表.module.css'#上游入口名（分块 @import）
_样式分块文件=(#拼装顺序与 轨迹表.module.css 一致
    ('壳','轨迹表-壳.module.css'),
    ('行','轨迹表-行.module.css'),
    ('详情','轨迹表-详情.module.css'),
    ('载荷','轨迹表-载荷.module.css'),
    ('目录','轨迹表-目录.module.css'),
)#分块清单

def _读样式(文件名):#读真实 CSS
    """从同目录读取样式正文。"""
    路径=os.path.join(_本目录,文件名)#绝对路径
    with open(路径,'r',encoding='utf-8') as 文件:#读文件
        return 文件.read()#全文

样式分块={名:_读样式(文件) for 名,文件 in _样式分块文件}#分块映射
样式表='\n'.join(样式分块[名] for 名,_ in _样式分块文件)#完整表样式

种类样式类={#种类 → CSS 修饰
    'system':'systemNeutral','user':'user','context':'contextGreen','compacted':'compacted',
    'message':'assistantVioletBright','tool':'toolAmber','subtool':'subtoolAmber',
}#结束

class 轨迹表:#账本 + 详情检查器
    """消费轮次模型，产出分栏账本与可选详情面板结构树。"""

    def __init__(自身,属性=None):#可选 props
        """记下 props 与检查器局部状态。"""
        自身.属性=属性 or {}#合成
        自身.选中记录身份=None#检查器记录 id
        自身.选中请求=None#检查器请求
        自身.活动标签='overview'#详情标签
        自身.思考展开=False#思考块
        自身.详情宽=None#拖拽宽
        自身.工具请求偏移=None#工具栏偏移
        自身.标签历史=['overview']#近用标签
        自身.跟随表尾=False#贴底跟随
        自身.表滚动就绪=False#首屏就绪
        自身.更早加载中=False#分页忙
        自身.待滚记录身份=None#待滚 id
        自身.已应用记录选择=None#外部选择句柄
        自身.已应用记录焦点=None#外部焦点句柄

    def 更新(自身,属性):#刷新 props
        """刷新 props 并消化外部选择/焦点/巡检。"""
        自身.属性=属性 or {}#新
        自身._消化外部选择()#选择
        自身._消化外部焦点()#焦点
        自身._消化巡检调用()#巡检

    def _消化外部选择(自身):#外部 recordSelection
        """一次性外部选中。"""
        选择=取字段(自身.属性,'recordSelection')#选择
        if 选择 is None or 选择 is 自身.已应用记录选择:#无/已用
            return#停
        自身.已应用记录选择=选择#记
        自身.选中记录(取字段(选择,'index'))#选
        全部=自身._全部记录()#全部
        记录=next((候 for 候 in 全部 if 取字段(取字段(候,'cell'),'index')==取字段(选择,'index')),None)#找
        自身.待滚记录身份=None if 记录 is None else 轨迹记录身份(取字段(记录,'cell'))#待滚

    def _消化外部焦点(自身):#外部 recordFocus
        """一次性外部焦点（不改检查器选中）。"""
        焦点=取字段(自身.属性,'recordFocus')#焦点
        if 焦点 is None or 焦点 is 自身.已应用记录焦点:#无/已用
            return#停
        自身.已应用记录焦点=焦点#记
        全部=自身._全部记录()#全部
        记录=next((候 for 候 in 全部 if 取字段(取字段(候,'cell'),'index')==取字段(焦点,'index')),None)#找
        自身.待滚记录身份=None if 记录 is None else 轨迹记录身份(取字段(记录,'cell'))#待滚

    def _消化巡检调用(自身):#inspectCallId
        """跨视图巡检：打开调用摘要。"""
        调用=取字段(自身.属性,'inspectCallId')#调用
        if 调用 is None:#无
            return#停
        全部=展平记录(取字段(自身.属性,'turns') or [])#展平
        目标=next((候 for 候 in 全部 if 取字段(取字段(候,'cell'),'callId')==调用),None)#找
        if 目标 is None:#未解析
            return#等历史
        自身.打开记录摘要(目标)#开
        自身.待滚记录身份=轨迹记录身份(取字段(目标,'cell'))#待滚
        应答=取字段(自身.属性,'onInspectApplied')#应答
        if callable(应答):#有
            应答()#应答

    def _全部记录(自身):#当前展平
        """当前 turns 展平。"""
        return 展平记录(取字段(自身.属性,'turns') or [])#展平

    def _流式格表(自身):#流式格按 index
        """streamingCells → index 映射。"""
        return {取字段(格,'index'):格 for 格 in (取字段(自身.属性,'streamingCells') or [])}#表

    def _当前记录(自身,记录):#叠流式格
        """用流式格替换结构格。"""
        流式=自身._流式格表().get(取字段(取字段(记录,'cell'),'index'))#流式
        return 记录 if 流式 is None else dict(记录,cell=流式)#叠

    def _可见记录(自身):#搜索/折叠后
        """过滤或折叠后的账本记录。"""
        全部=自身._全部记录()#全部
        匹配=取字段(自身.属性,'searchMatchIndexes')#搜索
        if 匹配 is not None:#搜索态
            return 过滤记录(全部,匹配)#过滤
        折叠轮=取字段(自身.属性,'collapsedTurns') or set()#折轮
        轮记录=全部 if len(折叠轮)==0 else 折叠轮次记录(全部,折叠轮)#折轮
        折叠助=取字段(自身.属性,'collapsedAssistants') or set()#折助
        return 轮记录 if len(折叠助)==0 else 折叠助手记录(轮记录,折叠助)#折助

    def 激活标签(自身,标签):#切换详情标签
        """写入活动标签并刷新近用历史。"""
        if 标签 in 自身.标签历史:#已有
            自身.标签历史.remove(标签)#挪
        自身.标签历史.append(标签)#末
        自身.活动标签=标签#活动

    def 清空检查器(自身):#清检查器选中
        """清记录与请求选中。"""
        自身.选中记录身份=None#清记录
        自身.选中请求=None#清请求

    def 清空全部选中(自身):#清宿主+检查器
        """清检查器并通知宿主。"""
        自身.清空检查器()#检查器
        回调=取字段(自身.属性,'onClearSelection')#宿主
        if callable(回调):#有
            回调()#回调

    def 选中记录(自身,下标):#按 index 选记录
        """选中账本记录并挑可用标签。"""
        全部=自身._全部记录()#全部
        记录=next((候 for 候 in 全部 if 取字段(取字段(候,'cell'),'index')==下标),None)#找
        回调=取字段(自身.属性,'onRecordSelect')#回调
        if callable(回调):#有
            回调(下标)#通知
        自身.选中请求=None#清请求
        自身.选中记录身份=None if 记录 is None else 轨迹记录身份(取字段(记录,'cell'))#身份
        if 记录 is None:#无
            return#停
        页们=详情标签页(记录)#页
        可用={页['id'] for 页 in 页们}#可用
        近用=next((标签 for 标签 in reversed(自身.标签历史) if 标签 in 可用),None)#近用
        自身.活动标签=近用 or (页们[0]['id'] if 页们 else 'overview')#活动
        变=取字段(自身.属性,'onSelectedIndexChange')#变
        if callable(变):#有
            变(下标)#通知

    def 选择请求(自身,请求,标签='overview'):#选请求
        """打开请求检查器。"""
        自身.选中记录身份=None#清记录
        自身.选中请求=请求#请求
        自身.激活标签(标签)#标签

    def 打开记录摘要(自身,目标):#打开摘要并展开折叠
        """必要时展开轮次/助手后打开 overview。"""
        全部=自身._全部记录()#全部
        位=next((下标 for 下标,候 in enumerate(全部) if 取字段(取字段(候,'cell'),'index')==取字段(取字段(目标,'cell'),'index')),-1)#位
        折轮=取字段(自身.属性,'collapsedTurns') or set()#折轮
        切轮=取字段(自身.属性,'onToggleTurn')#切轮
        if 取字段(目标,'turn') is not None and 取字段(目标,'turn') in 折轮 and callable(切轮):#需展轮
            切轮(取字段(目标,'turn'))#展
        种类=取字段(取字段(目标,'cell'),'kind')#种类
        if 种类 in ('tool','subtool') and 位>0:#工具需展助手
            折助=取字段(自身.属性,'collapsedAssistants') or set()#折助
            切助=取字段(自身.属性,'onToggleAssistant')#切助
            for 候 in reversed(全部[:位]):#向前
                if 取字段(候,'turn')!=取字段(目标,'turn'):#出轮
                    break#停
                if 取字段(取字段(候,'cell'),'kind')!='message':#非助手
                    continue#跳
                助身份=轨迹记录身份(取字段(候,'cell'))#身份
                if 助身份 in 折助 and callable(切助):#需展
                    切助(助身份)#展
                break#停
        自身.选中请求=None#清请求
        自身.选中记录身份=轨迹记录身份(取字段(目标,'cell'))#身份
        自身.激活标签('overview')#概览

    def 打开调用摘要(自身,调用标识):#按 callId
        """解析 callId 后打开摘要。"""
        目标=next((候 for 候 in 自身._全部记录() if 取字段(取字段(候,'cell'),'callId')==调用标识),None)#找
        if 目标 is not None:#有
            自身.打开记录摘要(目标)#开

    def 处理动作(自身,动作,载荷=None):#动作分发
        """结构树交互：选中、折叠、加载更早、标签、拖拽宽。"""
        载荷=载荷 or {}#载荷
        if 动作=='select-record':#选记录
            自身.选中记录(取字段(载荷,'index'))#选
            return#已
        if 动作=='select-request':#选请求
            自身.选择请求({'turn':取字段(载荷,'turn'),'group':取字段(载荷,'group'),**({'seq':取字段(载荷,'seq')} if 取字段(载荷,'seq') is not None else {})},取字段(载荷,'tab','overview'))#选
            return#已
        if 动作=='clear-inspector':#清检查器
            自身.清空检查器()#清
            return#已
        if 动作=='clear-all':#清全部
            自身.清空全部选中()#清
            return#已
        if 动作=='activate-tab':#标签
            自身.激活标签(取字段(载荷,'tab','overview'))#切
            return#已
        if 动作=='toggle-thinking':#思考
            自身.思考展开=not 自身.思考展开#翻
            return#已
        if 动作=='set-thinking':#写思考
            自身.思考展开=bool(取字段(载荷,'expanded',False))#写
            return#已
        if 动作=='open-call':#开调用
            自身.打开调用摘要(取字段(载荷,'callId'))#开
            return#已
        if 动作=='open-record':#开记录
            目标=next((候 for 候 in 自身._全部记录() if 取字段(取字段(候,'cell'),'index')==取字段(载荷,'index')),None)#找
            if 目标 is not None:#有
                自身.打开记录摘要(目标)#开
            return#已
        if 动作=='toggle-collapsed-summary':#折叠摘要点击
            种类=取字段(载荷,'kind')#种类
            if 种类=='turn':#轮
                切=取字段(自身.属性,'onToggleTurn')#切
                if callable(切) and 取字段(载荷,'turn') is not None:#有
                    切(取字段(载荷,'turn'))#切
            else:#助手
                切=取字段(自身.属性,'onToggleAssistant')#切
                if callable(切) and 取字段(载荷,'id') is not None:#有
                    切(取字段(载荷,'id'))#切
            return#已
        if 动作=='double-toggle-turn':#双击轮
            切=取字段(自身.属性,'onToggleTurn')#切
            if callable(切) and 取字段(载荷,'turn') is not None:#有
                切(取字段(载荷,'turn'))#切
            return#已
        if 动作=='double-toggle-assistant':#双击助手
            切=取字段(自身.属性,'onToggleAssistant')#切
            if callable(切) and 取字段(载荷,'id') is not None:#有
                切(取字段(载荷,'id'))#切
            return#已
        if 动作=='load-older':#加载更早
            加载=取字段(自身.属性,'onLoadOlder')#加载
            if not callable(加载) or 自身.更早加载中 or 取字段(自身.属性,'olderHistoryLoading'):#忙
                return False#拒
            自身.更早加载中=True#忙
            try:#执行
                return 加载()#加载
            finally:#收尾
                自身.更早加载中=False#闲
        if 动作=='resize-details':#详情宽
            分栏宽=取字段(载荷,'splitWidth',0) or 0#分栏
            下一=钳制详情宽(取字段(载荷,'width',详情最小宽),分栏宽)#钳
            旧=自身.详情宽 if 自身.详情宽 is not None else 取字段(载荷,'startWidth',下一)#旧
            自身.详情宽=下一#写
            基偏=自身.工具请求偏移 if 自身.工具请求偏移 is not None else (分栏宽*工具请求占比-默认工具请求宽(分栏宽))#基偏
            自身.工具请求偏移=基偏+(下一-旧)*工具请求占比#偏
            return#已
        if 动作=='nudge-details':#键盘缩放
            方向=1 if 取字段(载荷,'direction')=='left' else -1#向
            分栏宽=取字段(载荷,'splitWidth',0) or 0#分栏
            当前=自身.详情宽 if 自身.详情宽 is not None else 取字段(载荷,'currentWidth',详情最小宽)#当前
            下一=钳制详情宽(当前+方向*详情缩放步长,分栏宽)#下一
            基偏=自身.工具请求偏移 if 自身.工具请求偏移 is not None else (分栏宽*工具请求占比-默认工具请求宽(分栏宽))#基偏
            自身.工具请求偏移=基偏+(下一-当前)*工具请求占比#偏
            自身.详情宽=下一#写
            return#已
        if 动作=='reset-details-width':#重置宽
            自身.详情宽=None#清
            自身.工具请求偏移=None#清
            return#已
        if 动作=='set-follow-tail':#贴底
            自身.跟随表尾=bool(取字段(载荷,'follow',False))#写
            return#已
        if 动作=='mark-scroll-ready':#首屏就绪
            自身.表滚动就绪=True#就绪
            自身.跟随表尾=True#跟随
            return#已
        if 动作=='toggle-unix-time':#时间戳切换（结构树消费方自持亦可）
            return 取字段(载荷,'showUnix',False)#透传
        return None#未识别

    def _助手计时面板(自身,指标):#助手计时
        """助手指标计时结构。"""
        return {#面板
            'type':'assistant-timing','class':'overview',#类型
            'rows':[#行
                {'dt':'Started','dd':格式化开始时刻(取字段(指标,'stepStartTime')),'toggleUnix':True,'timestamp':取字段(指标,'stepStartTime')},
                {'dt':'Total duration','dd':总耗时文案(指标)},
                {'dt':'TTFT','dd':首字耗时文案(指标)},
                {'dt':'Generation','dd':生成耗时文案(指标)},
                {'dt':'Throughput','dd':吞吐文案(指标)},
            ],#行结束
        }#结束

    def _用量行(自身,用量):#用量行
        """单次用量结构。"""
        if 用量 is None:#空
            return {'type':'no-payload','text':'Usage not reported'}#无
        总入=输入合计(用量)#入合计
        其它出=None#内容
        if 取字段(用量,'output') is not None and 取字段(用量,'reasoning') is not None:#可拆
            其它出=取字段(用量,'output')-取字段(用量,'reasoning')#内容
        行=[]#行
        if 总入 is not None:#入
            行.append({'dt':'Input','dd':f'{总入} tok'})#入
        if 取字段(用量,'cacheRead') is not None:#缓存读
            行.append({'dt':'Cached','dd':f'{取字段(用量,"cacheRead")} tok','detail':True})#缓存
        if 取字段(用量,'cacheWrite') is not None:#缓存写
            行.append({'dt':'Cache created','dd':f'{取字段(用量,"cacheWrite")} tok','detail':True})#写
        if 取字段(用量,'input') is not None:#其它入
            行.append({'dt':'Other','dd':f'{取字段(用量,"input")} tok','detail':True})#其它
        if 取字段(用量,'output') is not None:#出
            行.append({'dt':'Output','dd':f'{取字段(用量,"output")} tok'})#出
        if 取字段(用量,'reasoning') is not None:#思
            行.append({'dt':'Reasoning','dd':f'{取字段(用量,"reasoning")} tok','detail':True})#思
        if 其它出 is not None:#内容
            行.append({'dt':'Content','dd':f'{其它出} tok','detail':True})#内容
        return {'type':'usage-rows','class':'overview','rows':行}#行

    def _请求选项(自身,选项,预览=False):#请求选项
        """选项 JSON 树。"""
        if 选项 is None:#无
            return {'type':'no-payload','text':'Options not recorded'}#无
        return {'type':'json-tree','data':选项,'label':'Request options JSON','preview':预览}#树

    def _记录载荷(自身,记录,方向,预览=False):#入/出载荷
        """RecordPayload 结构。"""
        格=取字段(记录,'cell')#格
        值=取字段(格,'inputDetail') if 方向=='input' else 取字段(格,'outputDetail')#值
        缺='No payload captured' if 方向=='input' else 'No result captured'#缺
        if not 值:#无
            return {'type':'no-payload','text':缺}#缺
        错=方向=='output' and 取字段(格,'isError') is True#错
        块们=取字段(格,'outputBlocks') or []#块
        单文=方向=='output' and len(块们)==1 and 取字段(块们[0],'type')=='text'#单文
        容器=解析JSON容器(值)#JSON
        if 单文 and 容器 is not None:#单文 JSON
            return {'type':'json-tree','data':容器,'label':'Result JSON','preview':预览,'error':错}#树
        if 方向=='output' and any(取字段(块,'imageSrc') is not None or 取字段(块,'content')!='' for 块 in 块们):#结果块
            return {'type':'tool-output-blocks','blocks':块们,'error':错,'preview':预览}#块
        Markdown=(方向=='input' and 取字段(格,'kind') in ('user','context')) or (方向=='output' and 取字段(格,'kind')=='message')#MD
        if Markdown:#Markdown
            return {'type':'markdown','text':值,'preview':预览,'error':错}#MD
        if 容器 is not None:#JSON
            return {'type':'json-tree','data':容器,'label':('Payload' if 方向=='input' else 'Result')+' JSON','preview':预览,'error':错}#树
        return {'type':'pre','text':值,'preview':预览,'error':错,'noOutput':值=='No output'}#原文

    def _记录Schema(自身,记录,预览=False):#Schema
        """RecordSchema 结构。"""
        详=取字段(取字段(记录,'cell'),'schemaDetail')#详
        if not 详:#无
            return {'type':'no-payload','text':'Schema unavailable'}#无
        Schema=解析工具Schema(详)#解析
        if Schema is not None:#结构化
            return {'type':'schema','name':Schema['name'],'description':Schema['description'],'parameters':Schema['parameters'],'preview':预览}#结构
        return {'type':'pre','text':详,'preview':预览}#原文

    def _记录计时(自身,记录):#记录计时
        """RecordTiming 结构。"""
        格=取字段(记录,'cell')#格
        if 取字段(格,'kind')=='message' and 取字段(格,'assistantMetrics') is not None:#助手
            return 自身._助手计时面板(取字段(格,'assistantMetrics'))#助手
        秒=取字段(格,'timeSeconds')#秒
        return {#普通
            'type':'record-timing','class':'overview',#类型
            'rows':[#行
                {'dt':'Started','dd':格式化开始时刻(取字段(格,'startedAt')),'toggleUnix':True,'timestamp':取字段(格,'startedAt')},
                {'dt':'Duration','dd':格式化已用秒数(秒)},
                {'dt':'Timing source','dd':'Not available' if 秒 is None else 'Event timestamps'},
            ],#行结束
        }#结束

    def _请求计时(自身,助手,锚点,请求):#请求计时
        """RequestTiming 结构。"""
        if 助手 is not None:#有助手
            return 自身._记录计时(助手)#助手
        if 请求 is not None and 取字段(请求,'startedAt') is not None:#请求时戳
            完成=取字段(请求,'completedAt')#完成
            时长=None if 完成 is None else max(0,(完成-取字段(请求,'startedAt'))/1000)#秒
            return {#请求
                'type':'request-timing','class':'overview',#类型
                'rows':[#行
                    {'dt':'Started','dd':格式化开始时刻(取字段(请求,'startedAt')),'toggleUnix':True,'timestamp':取字段(请求,'startedAt')},
                    {'dt':'Duration','dd':格式化已用秒数(时长)},
                    {'dt':'Timing source','dd':'Event timestamps (running)' if 时长 is None else 'Event timestamps'},
                ],#行结束
            }#结束
        return {#回退锚点
            'type':'request-timing','class':'overview',#类型
            'rows':[#行
                {'dt':'Started','dd':格式化开始时刻(取字段(取字段(锚点,'cell'),'startedAt') if 锚点 else None),'toggleUnix':True,'timestamp':取字段(取字段(锚点,'cell'),'startedAt') if 锚点 else None},
                {'dt':'Duration','dd':格式化已用秒数(None)},
            ],#行结束
        }#结束

    def _Markdown记录内容(自身,记录,已渲染,预览=False):#Markdown 内容
        """MarkdownRecordContent 结构。"""
        格=取字段(记录,'cell')#格
        块们=取字段(格,'sourceBlocks') or []#块
        if not 已渲染 and 块们:#源块
            return {'type':'source-blocks','blocks':块们}#源块
        if 取字段(格,'thinkingDetail'):#有思考
            if not 已渲染:#原文
                源='\n\n'.join(x for x in (取字段(格,'thinkingDetail'),取字段(格,'outputDetail')) if x)#拼
                return {'type':'markdown-fragment','text':源,'rendered':False,'preview':预览}#片段
            return {#渲染思考+输出
                'type':'assistant-content','rendered':True,'preview':预览,#类型
                'thinking':{#思考
                    'expanded':自身.思考展开,#展开
                    'text':取字段(格,'thinkingDetail'),#文
                    'onlyPreview':预览 and not 取字段(格,'outputDetail'),#仅预览
                },#思考结束
                'output':取字段(格,'outputDetail'),#输出
                'toolCalls':[块 for 块 in 块们 if 取字段(块,'type')=='tool-call'],#工具
                'images':[块 for 块 in 块们 if 取字段(块,'imageSrc') is not None],#图
            }#结束
        源=Markdown源(记录)#源
        有图=any(取字段(块,'imageSrc') is not None for 块 in 块们)#图
        有工具=取字段(格,'kind')=='message' and any(取字段(块,'type')=='tool-call' for 块 in 块们)#工具
        if not 源 and not 有图 and not 有工具:#空
            空='Tool call only' if 是否仅工具调用(格) else (取字段(格,'text') or 'No content')#空标
            return {'type':'no-payload','text':空}#空
        if not 已渲染 or (not 有图 and not 有工具):#单片段
            return {'type':'markdown-fragment','text':源 or '','rendered':已渲染,'preview':预览}#片段
        return {#组合
            'type':'markdown-combo',#类型
            'source':源,#源
            'toolCalls':[块 for 块 in 块们 if 取字段(块,'type')=='tool-call'] if 取字段(格,'kind')=='message' else [],#工具
            'images':[块 for 块 in 块们 if 取字段(块,'imageSrc') is not None],#图
            'preview':预览,#预览
        }#结束

    def _系统提示差分(自身,之前,之后):#系统差分
        """SystemPromptDiff 结构。"""
        段=[]#段
        if 取字段(之前,'system')!=取字段(之后,'system'):#系统变
            段.append({'title':'System Prompt','lines':提示词差分行(取字段(之前,'system') or '',取字段(之后,'system') or '')})#系统
        工具前=json.dumps(取字段(之前,'tools') or [],indent=2,ensure_ascii=False)#工具前
        工具后=json.dumps(取字段(之后,'tools') or [],indent=2,ensure_ascii=False)#工具后
        if 工具前!=工具后:#工具变
            段.append({'title':'Tools','lines':提示词差分行(工具前,工具后)})#工具
        return {'type':'prompt-diff','sections':段}#差分

    def _工具目录(自身,工具们):#工具目录
        """ToolCatalog 结构。"""
        if not 工具们:#空
            return {'type':'no-payload','text':'No tools in this request'}#空
        return {'type':'tool-catalog','tools':[{'name':取字段(工,'name'),'description':取字段(工,'description'),'parameters':取字段(工,'parameters')} for 工 in 工具们]}#目录

    def _渲染行(自身,记录,位置,末端边界,全部,边界,编号,游程,会话编号,活动轮,活动段,选中下标,折轮):#单行
        """一条账本行结构。"""
        格=取字段(记录,'cell')#格
        呈现=记录呈现(格)#呈现
        折叠摘要=取字段(记录,'collapsedSummary')#摘要
        仅请求=取字段(格,'requestOnly') is True#仅请求
        初系统=取字段(格,'kind')=='system' and 取字段(格,'index')==取字段(取字段(全部[0],'cell'),'index') if 全部 else False#初系统
        键=请求键(取字段(记录,'turn'),取字段(记录,'group'))#键
        请求号=None#号
        if 边界.get(键)==取字段(格,'index') and 折叠摘要 is None and (取字段(记录,'turn') is None or 取字段(记录,'turn') not in 折轮):#边界
            请求号=编号.get(键)#号
        请求信息=None if 请求号 is None else next((候 for 候 in (会话编号 or []) if 取字段(候,'number')==请求号),None)#信息
        请求状态=取字段(请求信息,'status') if 请求信息 is not None else ('error' if 取字段(格,'isError') is True else None)#状态
        游=游程.get(取字段(格,'index'),0)#游程
        请求标=None if 请求号 is None else f'Request #{请求号}'+(' · Compaction' if 取字段(请求信息,'purpose')=='compaction' else '')#标
        请求选中=请求号 is not None and 自身.选中请求 is not None and 取字段(自身.选中请求,'turn')==取字段(记录,'turn') and 取字段(自身.选中请求,'group')==取字段(记录,'group')#选中
        段活=活动段==取字段(记录,'section') if 取字段(记录,'turn') is None else 活动轮==取字段(记录,'turn')#段活
        时间线焦点=取字段(自身.属性,'timelineFocusIndexes')#焦点
        焦点态=None#焦点
        if 折叠摘要 is None and 时间线焦点 is not None:#有焦点集
            焦点态='inside' if 取字段(格,'index') in 时间线焦点 else 'outside'#内/外
        return {#行
            'type':'trajectory-table-row',#类型
            'key':轨迹虚拟记录键(记录),#键
            'position':位置,#位
            'terminalRequestBoundary':末端边界,#末端
            'kind':取字段(格,'kind'),#种类
            'kindLabel':种类标签.get(取字段(格,'kind'),取字段(格,'kind')),#标签
            'kindClass':种类样式类.get(取字段(格,'kind')),#类
            'index':取字段(格,'index'),#下标
            'turn':取字段(记录,'turn'),#轮
            'section':取字段(记录,'section'),#段
            'group':取字段(记录,'group'),#组
            'groupStart':取字段(记录,'groupStart'),#组起
            'turnStart':取字段(记录,'turnStart'),#轮起
            'turnEnd':取字段(记录,'turnEnd'),#轮尾
            'isError':取字段(格,'isError'),#错
            'running':记录状态(记录)=='running',#跑
            'requestOnly':仅请求,#仅请求
            'collapsedSummary':折叠摘要,#摘要
            'collapsedSummaryKind':取字段(记录,'collapsedSummaryKind'),#摘要种
            'selected':折叠摘要 is None and 选中下标==取字段(格,'index'),#选中
            'timelineFocus':焦点态,#焦点
            'sectionActive':段活,#段活
            'isInitialSystem':初系统,#初系统
            'requestNumber':请求号,#请求号
            'requestLabel':请求标,#请求标
            'requestSelected':请求选中,#请求选
            'requestStatus':请求状态,#请求态
            'requestRunIndex':游,#游程
            'requestSeq':取字段(请求信息,'seq') if 请求信息 is not None else None,#序号
            'presentation':呈现,#呈现
            'recordId':轨迹记录身份(格),#身份
        }#结束

    def _详情体(自身,选中,选中状态,提示选中,选中提示,选中前提示,选中请求记录,选中请求助手,选中请求锚,选中请求信息,选中请求状态,选中请求号,选中请求用量,选中请求累计,选中请求选项,选中请求结果,选中请求工具数,选中请求子工具数,父消息,父工具,助手请求目标,助手请求号,有层级):#详情体
        """详情 tabpanel 内容结构。"""
        标签=自身.活动标签#活动
        if 自身.选中请求 is not None and 选中请求状态 is not None and 标签=='overview':#请求概览
            行=[#概览行
                {'dt':'Status','dd':状态标签(选中请求状态),'error':选中请求状态=='error'},
            ]#基
            if 取字段(选中请求信息,'purpose')=='compaction':#压缩
                行.append({'dt':'Purpose','dd':'Compaction'})#目的
            提供方=取字段(选中请求信息,'provider') if 选中请求信息 else None#提供方
            if 提供方 is None and 选中请求选项 is not None:#回退配置
                提供方=取字段(选中请求选项,'provider')#提供方
            if 提供方 is not None:#有
                行.append({'dt':'Provider','dd':提供方})#提供方
            模型=取字段(选中请求信息,'model') if 选中请求信息 else None#模型
            if 模型 is None and 选中请求选项 is not None:#回退
                模型=取字段(选中请求选项,'model')#模型
            if 模型 is not None:#有
                行.append({'dt':'Model','dd':模型})#模型
            行.append({'dt':'Tool calls','dd':选中请求工具数})#工具数
            if 选中请求子工具数>0:#子工具
                行.append({'dt':'Subtool calls','dd':选中请求子工具数})#子
            if 选中请求信息 is not None and 取字段(选中请求信息,'error') is not None:#错
                行.append({'dt':'Error','dd':取字段(选中请求信息,'error'),'error':True})#错
            if 选中请求信息 is not None and 取字段(选中请求信息,'retry') is not None:#重试
                最大=取字段(选中请求信息,'maxRetries')#最大
                行.append({'dt':'Retry','dd':f'Scheduled {取字段(选中请求信息,"retry")}'+(f' of {最大}' if 最大 is not None else '')})#重试
            if 选中请求信息 is not None and 取字段(选中请求信息,'retryDelayMs') is not None:#延迟
                行.append({'dt':'Retry delay','dd':格式化时长毫秒(取字段(选中请求信息,'retryDelayMs'))})#延迟
            if 选中请求结果 is not None:#结果链
                行.append({'dt':'Result','dd':{'type':'hierarchy-link','label':'Compacted' if 取字段(选中请求信息,'purpose')=='compaction' else 'Assistant Message','index':取字段(取字段(选中请求结果,'cell'),'index')}})#结果
            段=[]#概览段
            if 选中请求选项 is not None:#选项
                段.append({'label':'Options','tab':'options','body':自身._请求选项(选中请求选项,True)})#选项
            段.append({'label':'Usage','tab':'usage','body':自身._用量行(选中请求用量)})#用量
            段.append({'label':'Timing','tab':'timing','body':自身._请求计时(选中请求助手,选中请求锚,选中请求信息)})#计时
            return {'mode':'request-overview','rows':行,'sections':段}#请求概览
        if 自身.选中请求 is not None and 标签=='options':#请求选项
            return {'mode':'request-options','body':自身._请求选项(选中请求选项)}#选项
        if 自身.选中请求 is not None and 标签=='usage':#请求用量
            return {'mode':'request-usage','body':{'type':'usage-panel','thisRequest':自身._用量行(选中请求用量),'cumulative':自身._用量行(选中请求累计)}}#用量
        if 自身.选中请求 is not None and 标签=='timing':#请求计时
            return {'mode':'request-timing','body':自身._请求计时(选中请求助手,选中请求锚,选中请求信息)}#计时
        if 提示选中 and 选中前提示 is not None and 标签=='diff':#差分
            return {'mode':'prompt-diff','body':自身._系统提示差分(选中前提示,选中提示)}#差分
        if 提示选中 and 标签=='system-prompt':#系统提示
            文=取字段(选中提示,'system') or ''#文
            return {'mode':'system-prompt','body':{'type':'no-payload','text':'No system prompt in this request'} if 文=='' else {'type':'markdown','text':文,'systemPrompt':True}}#提示
        if 提示选中 and 标签=='tools':#工具目录
            return {'mode':'tools','body':自身._工具目录(取字段(选中提示,'tools') or [])}#目录
        if not 提示选中 and 选中 is not None and 取字段(取字段(选中,'cell'),'kind')=='compacted' and 选中状态 is not None and 标签=='overview':#压缩概览
            行=[#行
                {'dt':'Status','dd':状态标签(选中状态),'error':选中状态=='error'},
                {'dt':'Duration','dd':格式化已用秒数(取字段(取字段(选中,'cell'),'timeSeconds'))},
                {'dt':'Tokens','dd':'—'},
            ]#行结束
            体=None#摘要体
            if 取字段(取字段(选中,'cell'),'outputDetail') is not None:#有输出
                体=自身._Markdown记录内容(选中,True)#渲染
            return {'mode':'compacted-overview','rows':行,'summary':体}#压缩
        if not 提示选中 and 选中 is not None and 取字段(取字段(选中,'cell'),'kind')!='compacted' and 选中状态 is not None and 标签=='overview':#记录概览
            格=取字段(选中,'cell')#格
            行=[]#行
            if 取字段(格,'messageSource') is not None:#来源
                行.append({'dt':'Source','dd':{'type':'tab-link','label':消息来源标签(取字段(格,'messageSource')),'tab':'source'}})#来源
            if 有层级:#层级
                链=[]#链
                if 助手请求目标 is not None:#请求
                    链.append({'type':'select-request','label':f'Request #{助手请求号 if 助手请求号 is not None else "—"}','request':助手请求目标})#请求
                if 父消息 is not None:#父消息
                    链.append({'type':'open-record','label':'Assistant Message','index':取字段(取字段(父消息,'cell'),'index')})#消息
                if 父工具 is not None:#父工具
                    链.append({'type':'open-record','label':'Tool Call','index':取字段(取字段(父工具,'cell'),'index')})#工具
                行.append({'dt':'Source' if 助手请求目标 is not None else 'Hierarchy','dd':{'type':'hierarchy-links','links':链}})#层级
            行.append({'dt':'Status','dd':状态标签(选中状态),'error':选中状态=='error'})#状态
            if 取字段(格,'kind')=='message':#助手 token
                出=取字段(格,'output')#出
                思=取字段(格,'think')#思
                行.append({'dt':'Tokens','dd':'—' if 出 is None else f'{出} tok'})# token
                if 思 is not None:#思
                    行.append({'dt':'Reasoning','dd':f'{思} tok','detail':True})#思
                if 出 is not None and 思 is not None:#内容
                    行.append({'dt':'Content','dd':f'{max(0,出-思)} tok','detail':True})#内容
            if 取字段(格,'kind') in ('user','context'):#用户时长
                行.append({'dt':'Duration','dd':格式化已用秒数(取字段(格,'timeSeconds'))})#时长
            段=[]#段
            if 是否Markdown记录(选中):#Markdown
                段.append({'label':'Preview','tab':'rendered','body':自身._Markdown记录内容(选中,True,True)})#预览
            else:#工具类
                if 取字段(格,'inputDetail'):#载荷
                    段.append({'label':'Payload','tab':'input','body':自身._记录载荷(选中,'input',True)})#载荷
                if 取字段(格,'outputDetail'):#结果
                    段.append({'label':'Result','tab':'output','body':自身._记录载荷(选中,'output',True)})#结果
                段.append({'label':'Schema','tab':'schema','body':自身._记录Schema(选中,True)})#Schema
            if 助手请求目标 is not None:#请求计时入口
                段.append({'label':'Request Timing','selectRequest':助手请求目标,'tab':'timing','body':自身._记录计时(选中)})#请求计时
            if 取字段(格,'kind') in ('tool','subtool'):#工具计时
                段.append({'label':'Timing','tab':'timing','body':自身._记录计时(选中)})#计时
            return {'mode':'record-overview','rows':行,'sections':段}#记录概览
        if not 提示选中 and 选中 is not None and 标签=='rendered':#渲染
            return {'mode':'rendered','body':自身._Markdown记录内容(选中,True)}#渲染
        if not 提示选中 and 选中 is not None and 标签=='raw':#原文
            return {'mode':'raw','body':自身._Markdown记录内容(选中,False)}#原文
        if not 提示选中 and 选中 is not None and 标签=='source':#来源
            源=取字段(取字段(选中,'cell'),'messageSource')#源
            if 源 is None:#无
                return {'mode':'source','body':{'type':'no-payload','text':'Source not recorded'}}#无
            数据=源 if isinstance(源,dict) else {'value':源}#数据
            return {'mode':'source','body':{'type':'json-tree','data':数据,'label':'Message source JSON'}}#JSON
        if not 提示选中 and 选中 is not None and 标签=='input':#入
            return {'mode':'input','body':自身._记录载荷(选中,'input')}#入
        if not 提示选中 and 选中 is not None and 标签=='output':#出
            return {'mode':'output','body':自身._记录载荷(选中,'output')}#出
        if not 提示选中 and 选中 is not None and 标签=='schema':#Schema
            return {'mode':'schema','body':自身._记录Schema(选中)}#Schema
        if not 提示选中 and 选中 is not None and 标签=='timing':#计时
            return {'mode':'timing','body':自身._记录计时(选中)}#计时
        return {'mode':'empty'}#空

    def 渲染(自身):#结构树
        """产出分栏账本 + 可选详情结构树。"""
        属性=自身.属性#props
        全部=自身._全部记录()#全部
        边界=索引请求边界(全部)#边界
        会话编号=取字段(属性,'requestNumbers')#会话号
        编号=索引请求编号(全部,会话编号,边界)#编号
        记录们=自身._可见记录()#可见
        游程=索引请求边界游程(记录们)#游程
        虚拟行=编组轨迹虚拟行(记录们)#虚拟
        有更早=bool(取字段(属性,'hasOlderRecords',False))#更早
        虚拟化=有更早 or len(记录们)>虚拟化阈值#虚拟化
        历史加载=bool(取字段(属性,'historyLoading',False))#历史加载
        更早忙=bool(取字段(属性,'olderHistoryLoading',False)) or 自身.更早加载中#更早忙
        显示初载=历史加载 or not 自身.表滚动就绪#初载
        折轮=取字段(属性,'collapsedTurns') or set()#折轮
        模板=None if 自身.选中记录身份 is None else next((候 for 候 in 全部 if 轨迹记录身份(取字段(候,'cell'))==自身.选中记录身份),None)#模板
        选中=None if 模板 is None else 自身._当前记录(模板)#选中
        选中下标=取字段(取字段(选中,'cell'),'index') if 选中 is not None else None#下标
        选中状态=None if 选中 is None else 记录状态(选中)#状态
        选中提示=取字段(取字段(选中,'cell'),'promptDetail') if 选中 is not None and 取字段(取字段(选中,'cell'),'kind')=='system' else None#提示
        选中前提示=取字段(取字段(选中,'cell'),'previousPromptDetail') if 选中 is not None and 取字段(取字段(选中,'cell'),'kind')=='system' else None#前
        提示选中=选中提示 is not None#提示选中
        选中请求模板=[] if 自身.选中请求 is None else [候 for 候 in 全部 if 取字段(候,'turn')==取字段(自身.选中请求,'turn') and 取字段(候,'group')==取字段(自身.选中请求,'group')]#请求模板
        选中请求记录=[自身._当前记录(候) for 候 in 选中请求模板]#请求记录
        选中请求助手=next((候 for 候 in 选中请求记录 if 取字段(取字段(候,'cell'),'kind')=='message'),None)#助手
        选中请求锚=选中请求助手 or (选中请求记录[0] if 选中请求记录 else None)#锚
        选中请求号=None if 自身.选中请求 is None else 编号.get(请求键(取字段(自身.选中请求,'turn'),取字段(自身.选中请求,'group')))#号
        选中请求信息=None#信息
        if 自身.选中请求 is not None:#有请求
            if 取字段(自身.选中请求,'seq') is None:#无序号
                选中请求信息=next((候 for 候 in (会话编号 or []) if 取字段(候,'turn')==取字段(自身.选中请求,'turn') and 取字段(候,'group')==取字段(自身.选中请求,'group')),None)#按组
            else:#有序号
                选中请求信息=next((候 for 候 in (会话编号 or []) if 取字段(候,'seq')==取字段(自身.选中请求,'seq')),None)#按序
        选中请求状态=None#状态
        if 自身.选中请求 is not None:#有请求
            if 选中请求信息 is not None and 取字段(选中请求信息,'status') is not None:#显式
                选中请求状态=取字段(选中请求信息,'status')#态
            elif 选中请求助手 is not None and 取字段(取字段(选中请求助手,'cell'),'assistantMetrics') is not None and 取字段(取字段(取字段(选中请求助手,'cell'),'assistantMetrics'),'completedTime') is None:#跑
                选中请求状态='running'#跑
            elif 选中请求助手 is None and any(记录状态(候)=='running' for 候 in 选中请求记录):#子跑
                选中请求状态='running'#跑
            else:#完
                选中请求状态='complete'#完
        选中请求工具数=sum(1 for 候 in 选中请求记录 if 取字段(取字段(候,'cell'),'kind')=='tool')#工具
        选中请求子工具数=sum(1 for 候 in 选中请求记录 if 取字段(取字段(候,'cell'),'kind')=='subtool')#子工具
        结果序号=取字段(选中请求信息,'resultSeq') if 选中请求信息 is not None else None#结果序
        if 结果序号 is None:#回退助手
            选中请求结果模板=选中请求助手#助手
        else:#按序
            选中请求结果模板=next((候 for 候 in 全部 if 取字段(取字段(候,'cell'),'sourceSeq')==结果序号),None)#找
        选中请求结果=None if 选中请求结果模板 is None else 自身._当前记录(选中请求结果模板)#结果
        选中请求用量=取字段(选中请求信息,'usage') if 选中请求信息 is not None else None#用量
        if 选中请求用量 is None and 选中请求助手 is not None:#从助手推
            助格=取字段(选中请求助手,'cell')#格
            选中请求用量={键:取字段(助格,源) for 键,源 in (('input','input'),('cacheRead','cacheRead'),('cacheWrite','cacheWrite'),('output','output'),('reasoning','think')) if 取字段(助格,源) is not None} or None#推
        选中请求累计=取字段(选中请求信息,'cumulativeUsage') if 选中请求信息 is not None else 选中请求用量#累计
        选中请求选项=取字段(选中请求信息,'requestConfig') if 选中请求信息 is not None else None#选项
        活动轮=取字段(自身.选中请求,'turn') if 自身.选中请求 is not None else (取字段(选中,'turn') if 选中 is not None else None)#活动轮
        活动段=取字段(选中请求记录[0],'section') if 自身.选中请求 is not None and 选中请求记录 else (取字段(选中,'section') if 选中 is not None else None)#活动段
        if 自身.选中请求 is not None:#请求标签
            选中标签页=[页 for 页 in 请求标签页 if 页['id']!='options' or 选中请求选项 is not None]#过滤
        elif 选中 is None:#无选
            选中标签页=[]#空
        else:#记录标签
            选中标签页=详情标签页(选中)#页
        父级=父级记录(全部,选中) if 选中 is not None else {}#父级
        父消息=父级.get('message')#父消息
        父工具=父级.get('tool')#父工具
        助手请求号=编号.get(请求键(取字段(选中,'turn'),取字段(选中,'group'))) if 选中 is not None and 取字段(取字段(选中,'cell'),'kind')=='message' else None#助手请求号
        助手请求信息=None if 助手请求号 is None else next((候 for 候 in (会话编号 or []) if 取字段(候,'number')==助手请求号),None)#信息
        助手请求目标=None#目标
        if 选中 is not None and 助手请求号 is not None:#可跳请求
            助手请求目标={'turn':取字段(选中,'turn'),'group':取字段(选中,'group'),**({'seq':取字段(助手请求信息,'seq')} if 助手请求信息 is not None and 取字段(助手请求信息,'seq') is not None else {})}#目标
        有层级=助手请求目标 is not None or 父消息 is not None or 父工具 is not None#层级
        行们=[]#渲染行
        for 位置,记录 in enumerate(记录们):#逐条
            当前=自身._当前记录(记录)#当前
            末端=取字段(取字段(当前,'cell'),'requestOnly') is True and 位置==len(记录们)-1#末端
            行们.append(自身._渲染行(当前,位置,末端,全部,边界,编号,游程,会话编号,活动轮,活动段,选中下标,折轮))#行
        显示详情=自身.选中请求 is not None or 提示选中 or (选中 is not None and 选中状态 is not None)#显示详情
        详情标题=None#标题
        if 自身.选中请求 is not None:#请求头
            详情标题={#请求
                'mode':'request',#模式
                'number':选中请求号,#号
                'location':f'Compaction · {段落标签(取字段(自身.选中请求,"turn"))}' if 取字段(选中请求信息,'purpose')=='compaction' else 段落标签(取字段(自身.选中请求,'turn')),#位置
            }#结束
        elif 提示选中:#系统
            详情标题={'mode':'system','kindLabel':'SYSTEM','location':取字段(取字段(选中,'cell'),'text')}#系统
        elif 选中 is not None:#记录
            种类=取字段(取字段(选中,'cell'),'kind')#种类
            详情标题={#记录
                'mode':'record',#模式
                'kind':种类,#种类
                'kindLabel':种类标签.get(种类,种类),#标签
                'kindClass':种类样式类.get(种类),#类
                'location':段落标签(取字段(选中,'turn')) if 种类=='compacted' else f'{段落标签(取字段(选中,"turn"))} · {取字段(选中,"group")}',#位置
            }#结束
        分栏样式=None if 自身.工具请求偏移 is None else {'--trajectory-tool-request-width':f'calc(58cqw - {自身.工具请求偏移}px)'}#分栏
        return {#根
            'type':'trajectory-table',#类型
            'class':'split',#类
            'style':分栏样式,#样式变量
            'followTail':自身.跟随表尾,#贴底
            'scrollReady':自身.表滚动就绪,#就绪
            'virtualization':{#虚拟化描述
                'enabled':虚拟化,#开
                'threshold':虚拟化阈值,#阈
                'historyRowHeight':历史加载行高像素,#历史行
                'bottomFollowPx':底部跟随阈值像素,#贴底阈
                'olderLoadPx':更早加载阈值像素,#顶载阈
                'rows':虚拟行,#虚拟行
            },#虚拟化结束
            'tablePane':{#左栏
                'historyLoading':显示初载,#初载
                'hasOlderRecords':有更早,#更早
                'olderBusy':更早忙,#忙
                'ariaRowCount':len(记录们)+(1 if 有更早 else 0),#行数
                'rows':行们,#行
            },#左栏结束
            'details':None if not 显示详情 else {#右栏
                'width':自身.详情宽,#宽
                'title':详情标题,#标题
                'tabs':选中标签页,#标签
                'activeTab':自身.活动标签,#活动
                'summaryBody':自身.活动标签=='overview',#概览体类
                'body':自身._详情体(选中,选中状态,提示选中,选中提示,选中前提示,选中请求记录,选中请求助手,选中请求锚,选中请求信息,选中请求状态,选中请求号,选中请求用量,选中请求累计,选中请求选项,选中请求结果,选中请求工具数,选中请求子工具数,父消息,父工具,助手请求目标,助手请求号,有层级),#体
            },#右栏结束
            'pendingScrollRecordId':自身.待滚记录身份,#待滚
            'css':样式表,#拼装后的完整样式正文
            'cssChunks':样式分块,#分块映射（壳/行/详情/载荷/目录）
            'cssModule':样式文件,#入口文件名
        }#根结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有
            自身.更新(属性)#刷
        return 自身.渲染()#渲
