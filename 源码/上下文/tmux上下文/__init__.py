"""可选加入的请求准备 tmux 位置上下文。合格的 step 尝试会追加一条持久、带来源归属的上下文，点名本 agent 进程所在的 tmux 会话、窗口与窗格，以及该窗口的窗格树布局。插件每回合只拉一次状态，且仅针对第一次请求（step === 1）：经 ctx.shell 执行器服务跑一条 tmux display-message。它用窗格的 #{pane_tty} 对照本进程控制终端，确认本进程确实跑在 $TMUX_PANE 所指窗格里，因此只从 tmux 祖先继承了 $TMUX/$TMUX_PANE 的终端会读成「不在 tmux」。仅当渲染出的 tmux 状态相对上次注入有变化才再注入，并可选用 refreshIntervalMs 作为两次注入之间的下限。没有 tmux 环境、只有继承来的环境、没有 ctx.shell、或查询失败，都是空操作，从不报错：执行器拒绝会被收住并记成警告，回合继续。"""
import json,os,time#JSON引号、本进程pid与纪元毫秒
from ...依赖.schemastery import 数字字段#配置字段
from ...模型后端.llm import 创建用户消息#构造插件来源的用户消息

__all__=['名称','注入','应用','配置']#仅中文公开名

名称='tmux-context'#与事件来源 plugin 字段一致
注入=['agents']#依赖 agents 服务
配置={#每回合的 tmux 位置调度；非法值使插件加载失败
    'refreshIntervalMs':数字字段(),#同一会话内两次持久注入之间的最小毫秒数；省略或 0 则每次合格变化都注入
}#配置模式结束
取进程号=os.getpid#本 agent 进程 pid
tmux字段表=(#display-message -p 字段，按查询顺序；有意排除窗格/窗口像素尺寸
    '#{session_name}',#会话名
    '#{window_index}',#窗口序号
    '#{window_name}',#窗口名
    '#{pane_index}',#窗格序号
    '#{pane_id}',#窗格 id（如 %1）
    '#{window_active}',#窗口是否活动
    '#{pane_active}',#窗格是否活动
    '#{window_layout}',#窗格树布局串
)#字段元组结束
读数前缀='tmux location (turn '#标记渲染读数里易变的回合/步骤前导行的前缀
字段分隔='\\t'#传给 tmux 的字面 \t；tmux 不解释 C 转义，再在这里拆回
安全整数上限=9007199254740991#外来 JSON Number.MAX_SAFE_INTEGER

def 编码(值):
    """诊断用紧凑 JSON。"""
    return json.dumps(值,ensure_ascii=False,separators=(',',':'),allow_nan=False)#JSON

def 已中止(信号):
    """信号是否已中止。无信号视为未中止。"""
    if 信号 is None:#无信号
        return False#未中止
    return 信号._事件.is_set()#Event 置位即中止

def 查询tmux位置(外壳,日志器,进程号,信号):
    """经 bash seam 读本进程的 tmux 位置；本进程并非真正跑在 tmux 窗格里或查询失败时为 None。单凭 $TMUX_PANE 不够：继承环境会读成「不在 tmux」。执行器拒绝是查询失败，不是回合失败。"""
    格式=字段分隔.join(tmux字段表)#拼成 tmux -p 格式
    命令='\n'.join([#先确认真在窗格，再打字段
        '[ -n "$TMUX_PANE" ] || exit 1',#没有 pane 变量则退出
        'self_tty=$(ps -o tty= -p '+str(进程号)+" | tr -d ' ')",#读本进程控制终端
        '[ -n "$self_tty" ] || exit 1',#没有 tty 则退出
        'pane_tty=$(tmux display-message -t "$TMUX_PANE" -p \'#{pane_tty}\') || exit 1',#读窗格 tty
        '[ "$pane_tty" = "/dev/$self_tty" ] || exit 1',#必须是本进程的 tty
        "exec tmux display-message -t \"$TMUX_PANE\" -p '"+格式+"'",#打出位置字段
    ])#拼成一条 bash 脚本
    try:#执行器可能因政策拒绝
        结果=外壳.运行(外壳.解析({'command':命令,'signal':信号}))#解析并跑只读命令
    except Exception as 错误:#resolve/run 拒绝不得打断回合
        日志器.warn('tmux location query failed: '+str(错误)+'; injecting no location this turn')#警告后空操作
        return None#本回合不注入
    if 结果['exitCode']!=0:#非零：不在 tmux 或查询失败
        return None#不注入
    行=结果['stdout']['text'].split('\n',1)[0]#只取第一行
    部件列表=行.split(字段分隔)#按字面 \t 拆字段
    if len(部件列表)!=len(tmux字段表):#字段数不对则丢弃
        return None#无效
    会话名=部件列表[0]#会话名
    窗口序号=部件列表[1]#窗口序号
    窗口名=部件列表[2]#窗口名
    窗格序号=部件列表[3]#窗格序号
    窗格标识=部件列表[4]#窗格 id
    窗口活动=部件列表[5]#窗口是否活动
    窗格活动=部件列表[6]#窗格是否活动
    窗口布局=部件列表[7]#窗格树布局
    if len(窗格标识)==0:#空 pane id 视为无效
        return None#无效
    return {#结构化位置
        'sessionName':会话名,#会话名
        'windowIndex':窗口序号,#窗口序号
        'windowName':窗口名,#窗口名
        'paneIndex':窗格序号,#窗格序号
        'paneId':窗格标识,#窗格 id
        'windowActive':窗口活动,#窗口是否活动
        'paneActive':窗格活动,#窗格是否活动
        'windowLayout':窗口布局,#窗格树布局
    }#结束返回

def 渲染状态(位置):
    """渲染稳定的 tmux 状态块：读数里用来做变化抑制比较的那部分。排除回合前导，因此再注入只由 tmux 状态驱动。"""
    return ('session '+位置['sessionName']+', '#会话
        +'window '+位置['windowIndex']+' '+编码(位置['windowName'])+', '#窗口（名用 JSON 引号）
        +'pane '+位置['paneIndex']+' '+位置['paneId']+'\n'#窗格
        +'window active='+位置['windowActive']+', pane active='+位置['paneActive']+', '#活动标志
        +'layout '+位置['windowLayout'])#布局串

def 渲染读数(位置,回合):
    """渲染完整持久读数，含易变的回合前导。"""
    return 读数前缀+str(回合)+'):\n'+渲染状态(位置)#前导 + 稳定块

def 最近注入状态(智能体):
    """本插件最近一次持久注入的稳定状态块；会话里还没有则为 None。扫描原始持久事件，因此调度能在压缩和进程恢复后存活。"""
    事件列表=list(智能体.session.events)#原始事件拷贝
    for 事件 in reversed(事件列表):#从新到旧扫
        if 事件['type']!='user/message':#非用户消息
            continue#下一
        出处=事件['data']['source'] if 'source' in 事件['data'] else None#出处
        if not isinstance(出处,dict) or 出处['kind']!='plugin' or 出处['plugin']!=名称:#非本插件
            continue#下一
        内容=事件['data']['content']#内容块列表
        块=内容[0] if 内容 else None#第一块内容
        if 块 is None or 块['type']!='text':#非文本则无法拆状态
            return None#视为缺席
        正文=块['text']#读数全文
        换行=正文.find('\n')#前导与状态块的分界
        状态='' if 换行==-1 else 正文[换行+1:]#去掉前导行
        return {'state':状态,'time':事件['time']}#状态 + 注入时刻
    return None#从未注入

def 校验刷新间隔(刷新间隔毫秒):
    """拒绝无法表示精确已过毫秒数目的刷新间隔。"""
    if 刷新间隔毫秒 is None:#省略
        return#通过
    if isinstance(刷新间隔毫秒,bool):#布尔不是整数
        raise TypeError('tmux-context: refreshIntervalMs must be a non-negative safe integer, got '+str(刷新间隔毫秒))#加载失败
    if isinstance(刷新间隔毫秒,int):#整数
        合法=abs(刷新间隔毫秒)<=安全整数上限#外来安全范围
    elif isinstance(刷新间隔毫秒,float) and 刷新间隔毫秒.is_integer():#整值浮点
        合法=abs(刷新间隔毫秒)<=安全整数上限#外来安全范围
    else:#其它
        合法=False#非法
    if (not 合法) or 刷新间隔毫秒<0:#提供了间隔且非法
        raise TypeError('tmux-context: refreshIntervalMs must be a non-negative safe integer, got '+str(刷新间隔毫秒))#加载失败

def 应用(上下文,配置值=None):
    """在 ctx 生命周期内登记一条前置的 pre-step 监听器。刷新间隔非法时抛出。"""
    if 配置值 is None:#缺省空配置
        配置值={}#空配置
    刷新间隔毫秒=配置值['refreshIntervalMs'] if 'refreshIntervalMs' in 配置值 else None#调度下限
    校验刷新间隔(刷新间隔毫秒)#非法则加载失败
    def 预步骤监听(载荷,下一步,*剩余):
        """瀑布 pre-step：先跑后续，再在合格首步注入 tmux 位置。"""
        决策=下一步()#先跑后续监听器
        if 决策['kind']=='reject' or 已中止(载荷['signal'] if 'signal' in 载荷 else None) or 载荷['step']!=1:#拒绝/已取消/非首步则原样
            return 决策#原样返回
        外壳=上下文.获取服务('shell')#可选执行器
        if 外壳 is None:#没有 shell 则空操作
            return 决策#原样返回
        智能体=载荷['agent']#本步智能体
        先前=最近注入状态(智能体)#上次注入
        if 刷新间隔毫秒 is not None and 刷新间隔毫秒>0 and 先前 is not None:#有下限且已注入过
            现在=int(time.time()*1000)#当前时刻毫秒
            if 现在>=先前['time'] and 现在-先前['time']<刷新间隔毫秒:#未到下限则跳过
                return 决策#原样返回
        位置=查询tmux位置(外壳,上下文.日志,取进程号(),载荷['signal'] if 'signal' in 载荷 else None)#查询位置
        if 位置 is None:#不在 tmux 或失败
            return 决策#原样返回
        状态=渲染状态(位置)#稳定块
        if 先前 is not None and 先前['state']==状态:#状态未变则不重复注入
            return 决策#原样返回
        文本=渲染读数(位置,载荷['turn'])#含回合前导的全文
        下游消息=决策['messages'] if 'messages' in 决策 else []#后续监听器消息
        消息列表=[#插件快照插在已有消息前
            创建用户消息({#持久用户消息
                'content':[{'type':'text','text':文本}],#读数正文
                'source':{'kind':'plugin','plugin':名称,'form':'snapshot','sections':[{'name':名称,'text':文本}]},#来源归属
            }),#结束 createUserMessage
        ]+list(下游消息 or [])#保留后续监听器的消息
        return {'kind':'enter','messages':消息列表}#继续循环并前置位置消息
    上下文.监听('agent/pre-step',预步骤监听,{'前置':True})#插到链头

应用.name=名称#Cordis name 槽
应用.inject=注入#Cordis inject 槽
应用.Config=配置#Cordis Config 槽
apply=应用#Cordis插件入口
default=应用#Cordis 默认导出
