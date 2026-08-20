"""轨迹表投影纯函数：展平、折叠、请求边界、详情标签与展示文案。

对齐上游 `ui-trajectory/src/client/TrajectoryTable.tsx` 中非 DOM 的纯投影。公开面仅中文名。
"""
import difflib#系统提示词差分
import json#Schema / JSON 载荷解析
from .轨迹记录 import 轨迹记录身份,格式化已用秒数,取字段#记录面
from .轨迹预览 import 轨迹预览文本#有界预览

__all__=[#仅中文公开名
    '底部跟随阈值像素',
    '更早加载阈值像素',
    '历史加载行高像素',
    '虚拟化阈值',
    '虚拟过扫行数',
    '虚拟初始视口高像素',
    '种类标签',
    '详情最小宽',
    '详情最大宽',
    '表最小宽',
    '详情缩放步长',
    '工具请求占比',
    '工具请求最小宽',
    '工具请求最大宽',
    '默认工具请求占比',
    '默认工具请求偏移',
    '系统提示标签页',
    '系统更新标签页',
    '请求标签页',
    '钳制详情宽',
    '默认工具请求宽',
    '格式化时长毫秒',
    '格式化开始时刻',
    '总耗时文案',
    '首字耗时文案',
    '生成耗时文案',
    '吞吐文案',
    '展平记录',
    '过滤记录',
    '请求步号',
    '请求键',
    '索引请求边界',
    '段落标签',
    '索引请求编号',
    '索引请求边界游程',
    '摘要轮次',
    '折叠轮次记录',
    '助手工具调用',
    '摘要助手工具',
    '折叠助手记录',
    '记录状态',
    '状态标签',
    '输入合计',
    '消息来源标签',
    '父级记录',
    '是否Markdown记录',
    'Markdown源',
    '详情标签页',
    '记录展示文案',
    '记录结果文案',
    '工具调用文案部件',
    '是否仅工具调用',
    '记录呈现',
    '解析工具Schema',
    '解析JSON容器',
    '提示词差分行',
]#公开面结束

底部跟随阈值像素=2#贴底判定
更早加载阈值像素=48#顶边加载判定
历史加载行高像素=30#历史行高
虚拟化阈值=100#超过则虚拟化
虚拟过扫行数=12#过扫
虚拟初始视口高像素=600#初始视口

种类标签={#种类 → 设计标签
    'system':'SYSTEM','user':'USER','context':'CONTEXT','compacted':'COMPACTED',
    'message':'ASSISTANT','tool':'TOOL','subtool':'SUBTOOL',
}#结束

详情最小宽=320#详情最小
详情最大宽=720#详情最大
表最小宽=280#表最小
详情缩放步长=16#键盘缩放
工具请求占比=0.58#工具请求栏占比
工具请求最小宽=180#工具请求最小
工具请求最大宽=480#工具请求最大
默认工具请求占比=0.36#默认占比
默认工具请求偏移=56#默认偏移

系统提示标签页=(#系统提示
    {'id':'system-prompt','label':'System Prompt'},
    {'id':'tools','label':'Tools'},
)#结束
系统更新标签页=(#带差分
    {'id':'diff','label':'Diff'},
)+系统提示标签页#结束
请求标签页=(#请求检查器
    {'id':'overview','label':'Summary'},
    {'id':'options','label':'Options'},
    {'id':'usage','label':'Usage'},
    {'id':'timing','label':'Timing'},
)#结束

def 钳制详情宽(宽度,分栏宽):#钳制详情面板宽
    """把详情宽钳在分栏可用区间。"""
    最大=max(详情最小宽,min(详情最大宽,分栏宽-表最小宽))#可用上界
    return round(min(max(宽度,详情最小宽),最大))#钳制

def 默认工具请求宽(分栏宽):#默认工具请求栏宽
    """按默认占比推导工具请求栏宽。"""
    return min(max(分栏宽*默认工具请求占比-默认工具请求偏移,工具请求最小宽),工具请求最大宽)#钳制

def 格式化时长毫秒(毫秒):#时长标签
    """毫秒时长人类标签。"""
    if 毫秒<1000:#亚秒
        return f'{round(毫秒)} ms'#整毫秒
    return f'{(毫秒/1000):.{2 if 毫秒<10000 else 1}f} s'#秒

def 格式化开始时刻(时间戳):#本地时间标签
    """有限时间戳格式化为本地日时；否则不可用。"""
    if 时间戳 is None:#空
        return 'Not available'#不可用
    try:#有限判定
        数=float(时间戳)#数值
    except (TypeError,ValueError):#非数
        return 'Not available'#不可用
    if 数!=数 or 数 in (float('inf'),float('-inf')):#非有限
        return 'Not available'#不可用
    import datetime as 日期时间#本地格式
    时刻=日期时间.datetime.fromtimestamp(数/1000 if 数>1e12 else 数)#毫秒或秒
    return 时刻.strftime('%Y-%m-%d %H:%M:%S.')+f'{int(时刻.microsecond/1000):03d}'#日时.毫秒

def 总耗时文案(指标):#总耗时
    """助手指标总耗时。"""
    if not 取字段(指标,'timingRecorded'):#未记
        return 'Not recorded'#未记
    if 取字段(指标,'stepStartTime') is None:#无起点
        return 'Step start unavailable'#无起点
    if 取字段(指标,'completedTime') is None:#未完
        return 'Pending'#进行中
    return 格式化时长毫秒(max(0,取字段(指标,'completedTime')-取字段(指标,'stepStartTime')))#差

def 首字耗时文案(指标):#TTFT
    """首字耗时。"""
    if not 取字段(指标,'timingRecorded'):#未记
        return 'Not recorded'#未记
    if 取字段(指标,'stepStartTime') is None:#无起点
        return 'Step start unavailable'#无起点
    if 取字段(指标,'firstTokenTime') is None:#无首字
        return 'First token unavailable'#无首字
    return 格式化时长毫秒(max(0,取字段(指标,'firstTokenTime')-取字段(指标,'stepStartTime')))#差

def 生成耗时文案(指标):#生成段
    """首字到完成。"""
    if not 取字段(指标,'timingRecorded') or 取字段(指标,'firstTokenTime') is None:#无首字
        return 'First token unavailable'#无首字
    if 取字段(指标,'completedTime') is None:#未完
        return 'Pending'#进行中
    return 格式化时长毫秒(max(0,取字段(指标,'completedTime')-取字段(指标,'firstTokenTime')))#差

def 吞吐文案(指标):#吞吐
    """输出 token/s。"""
    if not 取字段(指标,'usageProvided'):#无用量
        return 'Usage unavailable'#无用量
    if 取字段(指标,'outputTokens') is None:#无输出
        return 'Output tokens unavailable'#无输出
    if not 取字段(指标,'timingRecorded') or 取字段(指标,'firstTokenTime') is None:#无首字
        return 'First token unavailable'#无首字
    if 取字段(指标,'completedTime') is None:#未完
        return 'Pending'#进行中
    生成秒=(取字段(指标,'completedTime')-取字段(指标,'firstTokenTime'))/1000#秒
    if 生成秒<=0:#过短
        return 'Duration too short'#过短
    return f'{取字段(指标,"outputTokens")/生成秒:.1f} tok/s'#吞吐

def 展平记录(轮次们):#轮次→表记录
    """按展示顺序展平轮次组为表记录。"""
    结果=[]#输出
    for 段下标,轮 in enumerate(轮次们 or []):#各轮
        段内首=True#段内首内容
        本轮=[]#本轮记录
        for 组 in 取字段(轮,'groups') or []:#各组
            格们=取字段(组,'cells') or []#格
            for 格下标,格 in enumerate(格们):#各格
                轮起始=段内首 and 取字段(格,'requestOnly') is not True and 取字段(格,'kind')!='system' and (取字段(格,'kind')!='compacted' or 取字段(轮,'turn') is None)#轮起始
                if 轮起始:#已标
                    段内首=False#消费
                本轮.append({#表记录
                    'turn':取字段(轮,'turn'),#轮号
                    'section':段下标,#段
                    'group':取字段(组,'title'),#组标题
                    'groupStart':格下标==0,#组起
                    'turnStart':轮起始,#轮起
                    'cell':格,#格
                    'turnEnd':False,#稍后补
                })#记录结束
        if 本轮:#有记录
            本轮[-1]['turnEnd']=True#末条轮尾
        结果.extend(本轮)#并入
    return 结果#全部

def 过滤记录(记录们,匹配集):#按搜索匹配过滤
    """只保留匹配下标，并重算组/轮边界。"""
    过滤=[dict(记录,groupStart=False,turnStart=False,turnEnd=False) for 记录 in 记录们 if 取字段(取字段(记录,'cell'),'requestOnly') is not True and 取字段(取字段(记录,'cell'),'index') in 匹配集]#过滤
    已起段=set()#已起段
    for 下标,记录 in enumerate(过滤):#重算
        前=过滤[下标-1] if 下标>0 else None#前
        后=过滤[下标+1] if 下标+1<len(过滤) else None#后
        记录['groupStart']=前 is None or 取字段(前,'section')!=取字段(记录,'section') or 取字段(前,'group')!=取字段(记录,'group')#组起
        格=取字段(记录,'cell')#格
        记录['turnStart']=取字段(记录,'section') not in 已起段 and 取字段(格,'kind')!='system' and (取字段(格,'kind')!='compacted' or 取字段(记录,'turn') is None)#轮起
        if 记录['turnStart']:#已起
            已起段.add(取字段(记录,'section'))#记
        记录['turnEnd']=后 is None or 取字段(后,'section')!=取字段(记录,'section')#轮尾
    return 过滤#结果

def 请求步号(组名):#Step N → 步号
    """解析 Step N 组名。"""
    if not isinstance(组名,str) or not 组名.startswith('Step '):#非步
        return None#无
    try:#整步
        值=int(组名[5:])#后缀
    except ValueError:#非整
        return None#无
    return 值 if 值>0 else None#正整

def 请求键(轮次,组名):#请求稳定键
    """轮次+组名复合键。"""
    return f'{轮次}\u0000{组名}'#复合

def 索引请求边界(记录们):#请求边界下标
    """每个请求组第一条可见边界记录下标。"""
    边界={}#键→下标
    for 记录 in 记录们:#逐条
        键=请求键(取字段(记录,'turn'),取字段(记录,'group'))#键
        if 键 in 边界:#已有
            continue#跳
        if 请求步号(取字段(记录,'group')) is None:#非步组
            if 取字段(记录,'groupStart'):#组起
                边界[键]=取字段(取字段(记录,'cell'),'index')#记下
            continue#下一条
        种类=取字段(取字段(记录,'cell'),'kind')#种类
        if 种类 in ('user','context'):#跳用户/上下文
            continue#跳
        边界[键]=取字段(取字段(记录,'cell'),'index')#记下
    return 边界#映射

def 段落标签(轮次):#段标签
    """轮次或轮间标签。"""
    return 'Between turns' if 轮次 is None else f'Turn {轮次}'#标签

def 索引请求编号(记录们,会话编号,边界):#请求编号表
    """会话编号优先，缺省按边界递增。"""
    编号={}#键→号
    for 请求 in 会话编号 or ():#会话号
        编号[请求键(取字段(请求,'turn'),取字段(请求,'group'))]=取字段(请求,'number')#写入
    下个=max([0,*编号.values()])+1#下一个
    边界记录=sorted(#边界记录
        [记录 for 记录 in 记录们 if 边界.get(请求键(取字段(记录,'turn'),取字段(记录,'group')))==取字段(取字段(记录,'cell'),'index') and 请求步号(取字段(记录,'group')) is not None],
        key=lambda 记录:取字段(取字段(记录,'cell'),'index'),
    )#排序
    for 记录 in 边界记录:#补号
        键=请求键(取字段(记录,'turn'),取字段(记录,'group'))#键
        if 键 not in 编号:#缺
            编号[键]=下个#赋
            下个+=1#递增
    return 编号#表

def 索引请求边界游程(记录们):#边界游程下标
    """仅请求分隔符的游程偏移。"""
    索引={}#下标→游程
    游程=0#当前
    for 记录 in 记录们:#逐条
        格=取字段(记录,'cell')#格
        if 取字段(格,'requestOnly') is True:#仅分隔
            索引[取字段(格,'index')]=游程#记下
            游程+=1#加
            continue#下
        if 游程>0 and 取字段(记录,'groupStart') and 请求步号(取字段(记录,'group')) is not None:#内容边界
            索引[取字段(格,'index')]=游程#记下
        游程=0#清
    return 索引#映射

def 摘要轮次(记录们):#折叠轮次摘要
    """步数与工具调用摘要。"""
    步数=len({取字段(记录,'group') for 记录 in 记录们 if isinstance(取字段(记录,'group'),str) and 取字段(记录,'group').startswith('Step ')})#步
    工具数=sum(1 for 记录 in 记录们 if 取字段(取字段(记录,'cell'),'kind') in ('tool','subtool'))#工具
    步文=f'{步数} {"step" if 步数==1 else "steps"}'#步文
    工具文=f'{工具数} tool {"call" if 工具数==1 else "calls"}'#工具文
    return f'{步文} · {工具文}'#合成

def 折叠轮次记录(记录们,折叠轮次):#折叠轮次
    """折叠轮次内容为摘要行。"""
    按轮={}#轮→记录
    for 记录 in 记录们:#分组
        轮=取字段(记录,'turn')#轮
        if 轮 is None:#轮间
            continue#跳
        按轮.setdefault(轮,[]).append(记录)#收
    输出=[]#结果
    for 记录 in 记录们:#投影
        轮=取字段(记录,'turn')#轮
        if 轮 is None or 轮 not in 折叠轮次:#未折
            输出.append(记录)#原样
            continue#下
        本轮=按轮.get(轮,[记录])#本轮
        格=取字段(记录,'cell')#格
        if 取字段(格,'requestOnly') is True or 取字段(格,'kind')=='system':#分隔/系统
            输出.append(记录)#保留
            continue#下
        内容=[候 for 候 in 本轮 if 取字段(取字段(候,'cell'),'requestOnly') is not True and 取字段(取字段(候,'cell'),'kind')!='system']#内容
        if len(内容)<=1:#不足折
            输出.append(记录)#原样
            continue#下
        if 取字段(格,'index')!=取字段(取字段(内容[0],'cell'),'index'):#非首
            continue#丢
        首=dict(记录,turnEnd=False)#首条
        输出.append(首)#压入
        输出.append(dict(记录,groupStart=False,turnStart=False,turnEnd=True,collapsedSummary=摘要轮次(内容[1:]),collapsedSummaryKind='turn'))#摘要
    return 输出#结果

def 助手工具调用(记录们,助手下标):#助手后工具链
    """助手消息后连续 tool/subtool。"""
    位=-1#位置
    for 下标,记录 in enumerate(记录们):#找
        if 取字段(取字段(记录,'cell'),'index')==助手下标:#命中
            位=下标#记
            break#停
    if 位==-1 or 取字段(取字段(记录们[位],'cell'),'kind')!='message':#非助手
        return []#空
    调用=[]#链
    for 记录 in 记录们[位+1:]:#后续
        种类=取字段(取字段(记录,'cell'),'kind')#种类
        if 种类 not in ('tool','subtool'):#断
            break#停
        调用.append(记录)#收
    return 调用#链

def 摘要助手工具(记录们):#助手工具摘要
    """工具调用数与名。"""
    名们=[]#去重名
    for 记录 in 记录们:#各调用
        文本=取字段(取字段(记录,'cell'),'text') or ''#文
        分隔=文本.find(' · ')#分隔
        名=文本 if 分隔==-1 else 文本[:分隔]#名
        if 名!='' and 名 not in 名们:#新
            名们.append(名)#收
    数=len(记录们)#数
    摘要=f'{数} tool {"call" if 数==1 else "calls"}'#摘要
    return f'{摘要} · {", ".join(名们)}' if 名们 else 摘要#带名

def 折叠助手记录(记录们,折叠助手):#折叠助手工具
    """折叠助手下工具调用为摘要。"""
    输出=[]#结果
    下标=0#游标
    while 下标<len(记录们):#扫描
        记录=记录们[下标]#当前
        输出.append(记录)#压
        格=取字段(记录,'cell')#格
        if 取字段(格,'kind')!='message' or 轨迹记录身份(格) not in 折叠助手:#不折
            下标+=1#前进
            continue#下
        调用=[]#工具链
        游=下标+1#探
        while 游<len(记录们):#探链
            候=记录们[游]#候
            if 取字段(候,'collapsedSummary') is not None:#已是摘要
                break#断
            种类=取字段(取字段(候,'cell'),'kind')#种类
            if 种类 not in ('tool','subtool'):#断
                break#停
            调用.append(候)#收
            游+=1#进
        if not 调用:#无链
            下标+=1#进
            continue#下
        末=调用[-1]#末
        输出[-1]=dict(记录,turnEnd=False)#改首
        输出.append(dict(记录,groupStart=False,turnStart=False,turnEnd=取字段(末,'turnEnd',False),collapsedSummary=摘要助手工具(调用),collapsedSummaryKind='assistant'))#摘要
        下标+=1+len(调用)#跳过链
    return 输出#结果

def 记录状态(记录):#complete/running/error
    """记录运行态。"""
    格=取字段(记录,'cell')#格
    if 取字段(格,'isError'):#错
        return 'error'#错
    if 取字段(格,'kind')=='compacted' and 取字段(格,'timeSeconds') is None:#压缩进行中
        return 'running'#跑
    if 取字段(格,'kind') in ('tool','subtool') and 取字段(格,'outputDetail') is None:#工具未果
        return 'running'#跑
    return 'complete'#完

def 状态标签(状态):#状态文案
    """状态人类标签。"""
    if 状态=='error':#错
        return 'Failed'#失败
    if 状态=='running':#跑
        return 'Pending'#挂起
    return 'Completed'#完成

def 输入合计(用量):#输入桶合计
    """input+cacheRead+cacheWrite。"""
    if 用量 is None:#空
        return None#无
    if 取字段(用量,'input') is None and 取字段(用量,'cacheRead') is None and 取字段(用量,'cacheWrite') is None:#全空
        return None#无
    return (取字段(用量,'input') or 0)+(取字段(用量,'cacheRead') or 0)+(取字段(用量,'cacheWrite') or 0)#和

def 消息来源标签(来源):#消息来源
    """messageSource 人类标签。"""
    if not isinstance(来源,dict):#非对象
        return 'Unknown'#未知
    种=来源.get('kind')#种
    if 种=='user':#用户
        return 'User'#用户
    if 种=='plugin':#插件
        插件=来源.get('plugin')#名
        return f'Plugin · {插件}' if isinstance(插件,str) and 插件!='' else 'Plugin'#插件
    if 种=='goal':#目标
        轮=来源.get('round')#轮
        return f'Goal · Round {轮}' if isinstance(轮,(int,float)) and 轮>0 else 'Goal'#目标
    if not isinstance(种,str) or 种=='':#空
        return 'Unknown'#未知
    return 种[:1].upper()+种[1:]#首字母大写

def 父级记录(记录们,记录):#工具父级
    """tool/subtool 的父消息与父工具。"""
    种类=取字段(取字段(记录,'cell'),'kind')#种类
    if 种类 not in ('tool','subtool'):#非工具
        return {}#空
    位=-1#位置
    for 下标,候 in enumerate(记录们):#找
        if 取字段(取字段(候,'cell'),'index')==取字段(取字段(记录,'cell'),'index'):#命中
            位=下标#记
            break#停
    if 位==-1:#无
        return {}#空
    工具=None#父工具
    if 种类=='subtool':#子工具
        for 候 in reversed(记录们[:位]):#向前
            if 取字段(候,'turn')!=取字段(记录,'turn') or 取字段(候,'group')!=取字段(记录,'group'):#出组
                break#停
            if 取字段(取字段(候,'cell'),'kind')=='tool':#父工具
                工具=候#记
                break#停
    父调用=取字段(取字段(工具,'cell') if 工具 is not None else 取字段(记录,'cell'),'callId')#调用 id
    消息=None#父消息
    if 父调用 is not None:#有调用
        for 候 in 记录们:#找消息
            if 取字段(候,'turn')!=取字段(记录,'turn'):#异轮
                continue#跳
            if 取字段(取字段(候,'cell'),'kind')!='message':#非消息
                continue#跳
            块们=取字段(取字段(候,'cell'),'sourceBlocks') or []#块
            if any(取字段(块,'callId')==父调用 for 块 in 块们):#含调用
                消息=候#记
                break#停
    结果={}#父级
    if 消息 is not None:#有消息
        结果['message']=消息#消息
    if 工具 is not None:#有工具
        结果['tool']=工具#工具
    return 结果#父级

def 是否Markdown记录(记录):#是否 Markdown 类
    """user/context/message。"""
    return 取字段(取字段(记录,'cell'),'kind') in ('user','context','message')#判定

def Markdown源(记录):#Markdown 源文本
    """详情 Markdown 源。"""
    格=取字段(记录,'cell')#格
    种类=取字段(格,'kind')#种类
    if 种类 in ('user','context'):#入
        return 取字段(格,'inputDetail')#入详
    if 种类 in ('message','compacted'):#出
        return 取字段(格,'outputDetail')#出详
    return None#无

def 详情标签页(记录):#详情标签页列表
    """按记录种类给出标签页。"""
    格=取字段(记录,'cell')#格
    种类=取字段(格,'kind')#种类
    if 种类=='system':#系统
        return list(系统提示标签页 if 取字段(格,'previousPromptDetail') is None else 系统更新标签页)#系统
    if 种类=='compacted':#压缩
        return [{'id':'overview','label':'Summary'},{'id':'raw','label':'Raw Output'}]#压缩
    if 是否Markdown记录(记录):#Markdown
        页=[{'id':'overview','label':'Summary'},{'id':'rendered','label':'Preview'},{'id':'raw','label':'Raw'}]#基
        if 取字段(格,'messageSource') is not None:#有来源
            页.append({'id':'source','label':'Source'})#来源
        return 页#页
    页=[{'id':'overview','label':'Summary'}]#概览
    if 取字段(格,'inputDetail'):#载荷
        页.append({'id':'input','label':'Payload'})#载荷
    if 取字段(格,'outputDetail'):#结果
        页.append({'id':'output','label':'Result'})#结果
    页.append({'id':'schema','label':'Schema'})#Schema
    页.append({'id':'timing','label':'Timing'})#计时
    return 页#页

def 是否仅工具调用(格):#Tool call only
    """助手仅工具调用占位。"""
    return 取字段(格,'kind')=='message' and not 取字段(格,'outputDetail') and not 取字段(格,'thinkingDetail') and 取字段(格,'text')=='Tool call only'#判定

def 记录展示文案(格):#行内展示
    """列表主文案。"""
    if 是否仅工具调用(格):#仅工具
        return ''#空
    预览Markdown=取字段(格,'previewMarkdown')#预览 MD
    if 预览Markdown is not None:#有预览
        预览=轨迹预览文本(预览Markdown)#抽
        文本=取字段(格,'text') or ''#文
        if 文本=='':#空文
            return 预览#预览
        return 文本 if 预览=='' else f'{文本} · {预览}'#合成
    文本=取字段(格,'text') or ''#文
    if 文本!='':#有文
        return 文本#文
    种类=取字段(格,'kind')#种类
    if 种类 in ('user','context'):#入
        Markdown=取字段(格,'inputDetail')#入
    elif 种类=='message':#助手
        Markdown=取字段(格,'outputDetail')
        if Markdown is None:#回退思考
            Markdown=取字段(格,'thinkingDetail')#思
    else:#其它
        Markdown=None#无
    return '' if Markdown is None else 轨迹预览文本(Markdown)#预览

def 记录结果文案(格):#行内结果
    """结果预览文案。"""
    预览=取字段(格,'resultPreviewMarkdown')#结果 MD
    return 取字段(格,'result') if 预览 is None else 轨迹预览文本(预览)#结果

def 工具调用文案部件(种类,文本):#工具名/参数
    """拆 tool/subtool 文案。"""
    if 种类 not in ('tool','subtool'):#非工具
        return None#无
    分隔=(文本 or '').find(' · ')#分隔
    if 分隔==-1:#无名参
        return {'name':文本 or ''}#仅名
    return {'name':文本[:分隔],'args':文本[分隔+3:]}#名参

def 记录呈现(格):#列表呈现值
    """displayText / listDisplayText / resultText / toolCall*。"""
    展示=记录展示文案(格)#展示
    结果=记录结果文案(格)#结果
    仅工具=是否仅工具调用(格)#仅工具
    部件=工具调用文案部件(取字段(格,'kind'),展示)#部件
    if 仅工具:#仅工具
        列表文='(tool call only)'#占位
    elif 部件 is None:#非工具拆分
        列表文=展示#展示
    else:#工具
        列表文=' '.join(x for x in (部件.get('name'),部件.get('args')) if x)#合成
    return {#呈现
        'displayText':展示,#展示
        'listDisplayText':列表文,#列表
        'resultText':结果,#结果
        'toolCallOnly':仅工具,#仅工具
        'toolCallText':部件,#部件
    }#结束

def 解析工具Schema(值):#解析工具 Schema
    """JSON Schema 容器。"""
    try:#解析
        解析=json.loads(值)#JSON
    except (TypeError,ValueError,json.JSONDecodeError):#失败
        return None#无
    if not isinstance(解析,dict):#非对象
        return None#无
    名=解析.get('name')#名
    描述=解析.get('description')#描述
    参数=解析.get('parameters')#参数
    if not isinstance(名,str) or not isinstance(描述,str) or not isinstance(参数,dict):#残
        return None#无
    return {'name':名,'description':描述,'parameters':参数}#Schema

def 解析JSON容器(值):#解析 JSON 对象/数组
    """成功则返回容器，否则 None。"""
    try:#解析
        解析=json.loads(值)#JSON
    except (TypeError,ValueError,json.JSONDecodeError):#失败
        return None#无
    return 解析 if isinstance(解析,(dict,list)) else None#容器

def 提示词差分行(之前,之后):#统一差分行
    """system/tools 文本差分行（meta/context/added/removed）。"""
    行们=[]#输出
    统一=list(difflib.unified_diff((之前 or '').splitlines(),(之后 or '').splitlines(),lineterm='',n=3))#差分
    for 行 in 统一:#逐行
        if 行.startswith('+++') or 行.startswith('---'):#文件头
            continue#跳
        if 行.startswith('@@'):#块头
            行们.append({'kind':'meta','text':行})#元
            continue#下
        if 行.startswith('+'):#增
            行们.append({'kind':'added','text':行})#增
            continue#下
        if 行.startswith('-'):#删
            行们.append({'kind':'removed','text':行})#删
            continue#下
        if 行.startswith(' '):#上下文
            行们.append({'kind':'context','text':行})#上下文
            continue#下
        if 行.startswith('\\'):#转义标记
            continue#跳
    return 行们#行
