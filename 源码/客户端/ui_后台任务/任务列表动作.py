"""会话头后台任务动作：渲染本会话的 jobsBySession 镜像。

对齐上游 `ui-jobs/src/client/JobListAction.tsx`。公开面仅中文名。
"""
import time#采样时钟

__all__=['任务列表动作','是否进行中','点状态','状态标签','格式时长','排序任务']#仅中文公开名

空任务列表=()#稳定空列表身份

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否进行中(任务):#登记表仍打开的任务
    """运行中或正在停止。"""
    状态=取字段(任务,'status')#状态
    return 状态=='running' or 状态=='stopping'#进行中

def 点状态(状态):#状态点语义
    """状态标记语义。"""
    if 状态=='running':#运行
        return 'ongoing'#进行
    if 状态=='stopping':#停止中
        return 'warning'#警告色
    if 状态=='completed':#完成
        return 'done'#完成
    if 状态=='killed':#取消
        return 'warning'#警告色
    if 状态=='failed':#失败
        return 'error'#错误
    raise Exception('unhandled job status: '+str(状态))#封闭联合托底

def 状态标签(状态,翻译):#人类状态词
    """行与无障碍名用的状态词。"""
    if 状态=='running':#运行
        return 翻译('status.running')#运行中
    if 状态=='stopping':#停止中
        return 翻译('status.stopping')#正在停止
    if 状态=='completed':#完成
        return 翻译('status.completed')#已完成
    if 状态=='killed':#取消
        return 翻译('status.killed')#已取消
    if 状态=='failed':#失败
        return 翻译('status.failed')#已失败
    raise Exception('unhandled job status: '+str(状态))#封闭联合托底

def 格式时长(经过毫秒,翻译):#至多两个相邻单位
    """格式化经过时长。"""
    总计=max(0,int(经过毫秒/1000))#总秒
    秒=总计%60#秒
    分=(总计//60)%60#分
    时=总计//3600#时
    if 时>0:#有小时
        return 翻译('duration.hours',{'hours':时,'minutes':分})#时分
    if 分>0:#有分钟
        return 翻译('duration.minutes',{'minutes':分,'seconds':秒})#分秒
    return 翻译('duration.seconds',{'seconds':秒})#仅秒

def 排序任务(任务们):#进行中在前
    """进行中按开始序，已结算按结束新到旧。"""
    def 键(任务):#排序键
        """排序键元组。"""
        活=是否进行中(任务)#是否进行中
        开始=取字段(任务,'startedAt',0)#开始
        结束=取字段(任务,'finishedAt')#结束
        if 结束 is None:#无结束
            结束=开始#回退开始
        return (0 if 活 else 1,开始 if 活 else -结束,开始)#活在前
    return sorted(任务们,key=键)#排序副本

class 任务列表动作:#会话头后台任务动作
    """会话头入口；无任务时渲染空。"""
    def __init__(自身,属性=None):#可选初始 props
        """记下 props 与弹出层状态。"""
        自身.属性=属性 or {}#合成 props
        自身.打开=False#弹出层
        自身.现在=int(time.time()*1000)#采样时钟

    def 更新(自身,属性):#刷新 props
        """刷新合成 props。"""
        自身.属性=属性#新 props
        任务们=自身.取任务()#当前任务
        if len(任务们)==0 and 自身.打开:#最后任务消失
            自身.打开=False#先关

    def 取任务(自身):#读本会话任务
        """从 jobsBySession 镜像取本会话任务。"""
        会话标识=取字段(自身.属性,'sessionId')#会话 id
        用会话=取字段(自身.属性,'useSessions')#选择器钩
        if 用会话 is None:#无钩
            return 空任务列表#空
        会话标识钉死=会话标识#闭包用
        def 选本会话(状态):#选本会话任务
            """从状态取本会话任务列表。"""
            return 取字段(取字段(状态,'jobsBySession'),会话标识钉死)#本会话
        列表=用会话(选本会话)#选本会话
        if 列表 is None:#无任务
            return 空任务列表#空
        return 列表#任务列表

    def 切换打开(自身):#切换弹出层
        """同一次提交采样时钟并切换打开。"""
        自身.现在=int(time.time()*1000)#采样
        自身.打开=not 自身.打开#翻转

    def 渲染(自身):#结构化视图
        """产出与上游 JSX 同构的结构化视图。"""
        翻译=取字段(自身.属性,'t')#翻译
        任务们=自身.取任务()#任务
        if len(任务们)==0:#无任务
            return None#不渲染控件
        行们=排序任务(任务们)#排序
        活数=0#进行中计数
        for 任务 in 任务们:#计数
            if 是否进行中(任务):#进行中
                活数+=1#加一
        if 活数>0:#有进行中
            计数键='count.live.one' if 活数==1 else 'count.live.other'#活计数键
            计数值=活数#显示数
        else:#全空闲
            计数键='count.idle.one' if len(任务们)==1 else 'count.idle.other'#闲计数键
            计数值=len(任务们)#显示数
        计数标签=翻译(计数键,{'count':计数值}) if 翻译 else str(计数值)#计数文案
        行视图=[]#行列表
        for 任务 in 行们:#逐行
            活=是否进行中(任务)#是否进行中
            开始=取字段(任务,'startedAt',0)#开始
            结束=取字段(任务,'finishedAt')#结束
            if 活:#进行中
                经过=自身.现在-开始#已运行
            else:#已结算
                经过=(结束 if 结束 is not None else 开始)-开始#耗时
            时长=格式时长(经过,翻译) if 翻译 else str(经过)#时长文案
            状态=取字段(任务,'status')#状态
            状态文=状态标签(状态,翻译) if 翻译 else str(状态)#状态词
            行视图.append({#一行
                'id':取字段(任务,'id'),#任务 id
                'live':活,#是否进行中
                'kind':取字段(任务,'kind'),#种类
                'label':取字段(任务,'label'),#标签
                'status':取字段(任务,'detail') or 状态文,#状态/细节
                'dot':点状态(状态),#状态点
                'duration':时长,#时长
                'durationTitle':翻译('duration.title.live' if 活 else 'duration.title.done',{'duration':时长}) if 翻译 else 时长,#时长标题
            })#行结束
        return {#结构化视图
            'type':'job-list-action',#类型
            'open':自身.打开,#是否打开
            'countLabel':计数标签,#计数标签
            'liveCount':活数,#进行中数
            'listAria':翻译('list.aria') if 翻译 else 'jobs',#列表无障碍名
            'rows':行视图 if 自身.打开 else None,#打开时的行
            'toggle':自身.切换打开,#切换
        }#视图结束

    def __call__(自身,属性=None):#组件调用形
        """对齐 React 组件调用。"""
        if 属性 is not None:#有新 props
            自身.更新(属性)#刷新
        return 自身.渲染()#渲染
