import weakref#按会话弱引用缓存单元
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ...模型后端.llm import 结构化克隆#深拷贝检查点行

class 会话投影错误(Exception):
    """会话投影包的异常基类。"""

class 会话投影注册表(服务):
    """订阅 session/event 一次，对每个已登记单元急切驱动 apply；变更引用通知变更馈送。"""
    def __init__(自身,上下文):
        """创建并安装注册表。"""
        super().__init__(上下文,'sessionProjections')#服务名
        自身._登记={}#键→登记记录
        自身._监听=set()#变更馈送监听器
        上下文.监听('session/created',自身._收到创建)#监听创建
        上下文.监听('session/event',自身._收到事件)#监听事件

    def _收到创建(自身,会话):
        """新会话 seq=0 时为每个已登记单元播种初始状态。"""
        if 会话.seq!=0:#只处理空日志创建
            return#跳过
        for 登记 in 自身._登记.values():#每个单元
            if 会话 in 登记['cells']:#已有单元
                continue#跳过
            登记['cells'][会话]={'state':登记['def']['init'](会话.header),'observedSeq':-1}#初始单元

    def _收到事件(自身,会话,事件):
        """每个提交事件驱动全部单元。"""
        自身._驱动(会话,事件)#急切驱动

    def 登记(自身,定义):
        """登记一个域投影单元；返回拆除器。"""
        键=定义['key']#单元键
        状态版本=定义['stateVersion']#状态版本
        if isinstance(状态版本,bool):#布尔不是整数
            raise 会话投影错误('会话投影 '+repr(键)+' 的 stateVersion 必须是非负整数，实际为 '+str(状态版本))#拒绝
        if isinstance(状态版本,int):#整数
            合法=abs(状态版本)<=9007199254740991#外来安全范围
        elif isinstance(状态版本,float) and 状态版本.is_integer():#整值浮点
            合法=abs(状态版本)<=9007199254740991#外来安全范围
        else:#其它
            合法=False#非法
        if (not 合法) or 状态版本<0:#非法版本
            raise 会话投影错误('会话投影 '+repr(键)+' 的 stateVersion 必须是非负整数，实际为 '+str(状态版本))#拒绝
        wire=定义['wire'] if 'wire' in 定义 else None#可选 wire 块
        擦除={
            'key':键,#键
            'stateSchema':定义['stateSchema'] if 'stateSchema' in 定义 else None,#状态校验
            'init':定义['init'],#init
            'apply':定义['apply'],#apply
            'wire':None if wire is None else {'viewSchema':wire['viewSchema'] if 'viewSchema' in wire else None,'view':wire['view']},#wire
            'stateVersion':状态版本,#版本
        }#擦除结束
        def 效果体():
            """登记或增加引用；拆除时减引用。"""
            if 键 not in 自身._登记:#首次
                自身._登记[键]={'def':擦除,'cells':weakref.WeakKeyDictionary(),'refs':1}#新登记
            else:#共享键
                已有=自身._登记[键]#已有登记
                if 已有['def']['stateVersion']!=状态版本:#版本冲突
                    raise 会话投影错误('会话投影键 '+repr(键)+' 已按 stateVersion '+str(已有['def']['stateVersion'])+' 登记；拒绝与 stateVersion '+str(状态版本)+' 共享')#拒绝
                已有['refs']+=1#加引用
            def 拆除():
                """最后一个引用离开时删除键。"""
                if 键 not in 自身._登记:#已删
                    return#结束
                活=自身._登记[键]#当前登记
                活['refs']-=1#减引用
                if 活['refs']==0:#无人引用
                    del 自身._登记[键]#删除
            return 拆除#拆除器
        拆除=自身.ctx.副作用(效果体,'sessionProjections.register()')#挂 effect
        def 调用拆除():
            """调用 effect 拆除器。"""
            拆除()#拆除
        return 调用拆除#返回拆除闭包

    def 变更时(自身,监听器):
        """订阅变更馈送；返回拆除器。"""
        def 效果体():
            """加入并拆除时移除监听器。"""
            自身._监听.add(监听器)#加入
            def 拆除():
                """移除监听器。"""
                自身._监听.discard(监听器)#移除
            return 拆除#拆除器
        拆除=自身.ctx.副作用(效果体,'sessionProjections.onChanged()')#挂 effect
        def 调用拆除():
            """调用 effect 拆除器。"""
            拆除()#拆除
        return 调用拆除#返回拆除闭包

    def 状态(自身,会话,键):
        """读取一个单元在会话游标处的主机状态。"""
        if 键 not in 自身._登记:#未登记
            return None#缺席
        登记=自身._登记[键]#查找登记
        自身._物化单元(会话)#物化全部单元
        return 自身._单元(登记,会话)['state']#返回状态

    def 快照(自身,会话,键列表=None):
        """读取每个已登记客户端可见单元在当前水位的一致切面。"""
        值表={}#wire 值
        选中=None if 键列表 is None else set(键列表)#可选过滤
        自身._物化单元(会话)#物化
        for 登记 in 自身._登记.values():#逐单元
            if 登记['def']['wire'] is None:#仅主机
                continue#跳过
            单元键=登记['def']['key']#键
            if 选中 is not None and 单元键 not in 选中:#过滤
                continue#跳过
            单元=自身._单元(登记,会话)#单元
            值表[单元键]=自身._视图单元(登记,单元)#校验视图
        return {'asOfSeq':会话.seq-1,'values':值表}#快照

    def 缓存快照(自身,会话,键列表=None):
        """只读已物化客户端可见单元，不折叠历史。"""
        值表={}#wire 值
        水位=None#最低水位
        选中=None if 键列表 is None else set(键列表)#可选过滤
        for 登记 in 自身._登记.values():#逐单元
            if 登记['def']['wire'] is None:#仅主机
                continue#跳过
            单元键=登记['def']['key']#键
            if 选中 is not None and 单元键 not in 选中:#过滤
                continue#跳过
            if 会话 not in 登记['cells']:#未物化
                continue#跳过
            单元=登记['cells'][会话]#已物化单元
            值表[单元键]=自身._视图单元(登记,单元)#视图
            水位=单元['observedSeq'] if 水位 is None else min(水位,单元['observedSeq'])#最低水位
        if 水位 is None:#无 wire 单元
            return None#缺席
        return {'asOfSeq':水位,'values':值表}#缓存快照

    def 检查点(自身,会话):
        """每个已登记单元在当前水位的可持久化行。"""
        行表={}#键→行
        for 登记 in 自身._登记.values():#逐单元
            单元=自身._单元(登记,会话)#物化单元
            行表[登记['def']['key']]={'ver':登记['def']['stateVersion'],'seq':单元['observedSeq'],'val':结构化克隆(单元['state'])}#分离克隆
        return 行表#检查点

    def 恢复地板(自身,检查点):
        """返回 persistence readFrom 应使用的 seq（比可用水位低 1）。"""
        地板=None#聚合地板
        for 登记 in 自身._登记.values():#逐单元
            键=登记['def']['key']#键
            行=检查点[键] if 键 in 检查点 else None#行
            需要=0 if 行 is None or 行['ver']!=登记['def']['stateVersion'] else max(行['seq']+1,0)#需从哪开始
            地板=需要 if 地板 is None else min(地板,需要)#取最小
        if 地板 is None:#无单元
            return None#无需读
        return max(地板-1,0)#一事件以下的锚点

    def 视图检查点(自身,检查点,键列表=None):
        """从持久化行直接视图化 wire 值。"""
        值表={}#wire 值
        选中=None if 键列表 is None else set(键列表)#过滤
        for 登记 in 自身._登记.values():#逐单元
            定义=登记['def']#擦除定义
            if 定义['wire'] is None:#仅主机
                continue#跳过
            单元键=定义['key']#键
            if 选中 is not None and 单元键 not in 选中:#过滤
                continue#跳过
            if 单元键 not in 检查点:#无行
                continue#跳过
            行=检查点[单元键]#行
            if 行['ver']!=定义['stateVersion']:#不可用
                continue#跳过
            状态=行['val']#状态
            校验=定义['stateSchema']#可选校验
            if 校验 is not None:#有校验器
                try:#校验
                    状态=校验(状态)#解析
                except (TypeError,ValueError,KeyError):#畸形
                    continue#跳过
            值表[单元键]=定义['wire']['view'](状态)#视图
        return 值表#部分映射

    def 恢复(自身,检查点,事件列表,基础序号,头):
        """从检查点与日志后缀恢复快照并刷新检查点。"""
        结束序号=事件列表[-1]['seq'] if len(事件列表)>0 else 基础序号-1#日志末端
        值表={}#wire 值
        刷新={}#刷新检查点
        for 登记 in 自身._登记.values():#逐单元
            定义=登记['def']#擦除定义
            行=检查点[定义['key']] if 定义['key'] in 检查点 else None#行
            可用=(行 is not None and 行['ver']==定义['stateVersion'] and 行['seq']>=基础序号-1 and 行['seq']<=结束序号)#可用行
            if (not 可用) and 基础序号>0:#中缀恢复不可行
                raise 会话投影错误('会话投影 '+repr(定义['key'])+' 无法从 seq '+str(基础序号)+' 恢复：检查点行缺失、版本不匹配或超出所给日志末端；请从 seq 0 重读')#拒绝
            状态=行['val'] if 可用 else 定义['init'](头)#种子状态
            校验=定义['stateSchema']#可选校验
            if 可用 and 校验 is not None:#校验种子
                状态=校验(状态)#解析
            起点=行['seq'] if 可用 else 基础序号-1#已折叠到的 seq
            起始索引=起点-基础序号+1#事件数组起点
            for 索引 in range(起始索引,len(事件列表)):#尾重放
                事件=事件列表[索引]#事件
                期望=基础序号+索引#期望 seq
                if 事件 is None or 事件['seq']!=期望:#缺口
                    raise 会话投影错误('会话投影 '+repr(定义['key'])+' 无法跨过缺失的 seq '+str(期望)+' 恢复')#拒绝
                状态=定义['apply'](状态,事件)#折叠
            if 定义['wire'] is not None:#有 wire
                值表[定义['key']]=定义['wire']['view'](状态)#视图
            刷新[定义['key']]={'ver':定义['stateVersion'],'seq':结束序号,'val':状态}#刷新行
        return {'snapshot':{'asOfSeq':结束序号,'values':值表},'checkpoint':刷新}#结果

    def 注水(自身,会话,检查点,事件列表,基础序号):
        """把恢复状态装进会话单元缓存。"""
        结束序号=事件列表[-1]['seq'] if len(事件列表)>0 else 基础序号-1#切面末端
        完整=True#是否已全部在水位
        for 登记 in 自身._登记.values():#检查水位
            if 会话 not in 登记['cells']:#无单元
                完整=False#需要恢复
                break#停扫
            当前=登记['cells'][会话]#当前单元
            if 当前['observedSeq']!=结束序号:#未齐
                完整=False#需要恢复
                break#停扫
        if 完整:#已齐
            值表={}#wire 值
            for 登记 in 自身._登记.values():#逐单元
                if 登记['def']['wire'] is None:#仅主机
                    continue#跳过
                单元=登记['cells'][会话]#单元
                值表[登记['def']['key']]=自身._视图单元(登记,单元)#视图
            return {'asOfSeq':结束序号,'values':值表}#快照
        已恢复=自身.恢复(检查点,事件列表,基础序号,会话.header)#冷恢复
        for 登记 in 自身._登记.values():#安装单元
            键=登记['def']['key']#键
            if 键 not in 已恢复['checkpoint']:#无行
                continue#跳过
            行=已恢复['checkpoint'][键]#行
            if 会话 in 登记['cells']:#已有
                当前=登记['cells'][会话]#当前
                if 当前['observedSeq']>行['seq']:#更新
                    continue#保留更新
            登记['cells'][会话]={'state':行['val'],'observedSeq':行['seq']}#安装
        return 已恢复['snapshot']#快照

    def _物化单元(自身,会话):
        """把每个登记单元物化到会话当前游标。"""
        for 登记 in 自身._登记.values():#逐单元
            自身._单元(登记,会话)#物化

    def _构建单元(自身,定义,头,事件列表):
        """从 init 折叠事件前缀。"""
        状态=定义['init'](头)#初始
        for 事件 in 事件列表:#逐事件
            状态=定义['apply'](状态,事件)#折叠
        末序号=事件列表[-1]['seq'] if len(事件列表)>0 else -1#末 seq
        return {'state':状态,'observedSeq':末序号}#单元

    def _单元(自身,登记,会话):
        """读取或懒构建单元并推进到会话游标。"""
        if 会话 not in 登记['cells']:#首次
            单元=自身._构建单元(登记['def'],会话.header,会话.events)#全日志
            登记['cells'][会话]=单元#缓存
        else:#已有
            单元=登记['cells'][会话]#已有
            自身._推进单元(登记['def'],单元,会话.events,会话.seq-1)#推进
        return 单元#单元

    def _推进单元(自身,定义,单元,事件列表,直到序号):
        """把已有单元推进到连续前缀末端。"""
        if 单元['observedSeq']>=直到序号:#已够
            return#结束
        for 序号 in range(单元['observedSeq']+1,直到序号+1):#逐 seq
            事件=事件列表[序号] if 序号<len(事件列表) else None#事件
            if 事件 is None or 事件['seq']!=序号:#缺口
                raise 会话投影错误('会话投影 '+repr(定义['key'])+' 无法跨过缺失的 seq '+str(序号)+' 推进')#拒绝
            下一=定义['apply'](单元['state'],事件)#折叠
            单元['state']=下一#写回
            单元['observedSeq']=序号#水位

    def _驱动(自身,会话,事件):
        """把一次提交事件过全部登记单元。"""
        for 登记 in 自身._登记.values():#逐单元
            单元=登记['cells'][会话] if 会话 in 登记['cells'] else None#单元
            if 单元 is not None and 单元['observedSeq']>=事件['seq']:#已见过
                continue#跳过
            if 单元 is None:#晚到构建
                前缀=会话.events[:事件['seq']]#前缀
                单元=自身._构建单元(登记['def'],会话.header,前缀)#构建
                登记['cells'][会话]=单元#缓存
            else:#推进到事件前
                自身._推进单元(登记['def'],单元,会话.events,事件['seq']-1)#推进
            先前=单元['state']#先前状态
            下一=登记['def']['apply'](先前,事件)#折叠
            变更=下一 is not 先前#引用变更
            单元['state']=下一#写回
            单元['observedSeq']=事件['seq']#水位
            if 变更 and 登记['def']['wire'] is not None and len(自身._监听)>0:#通知
                值=自身._视图单元(登记,单元)#视图
                for 监听器 in 自身._监听:#馈送
                    监听器(会话,登记['def']['key'],值,事件['seq'])#通知

    def _视图单元(自身,登记,单元):
        """返回 schema 校验后的 wire 视图。"""
        wire=登记['def']['wire']#wire
        if wire is None:#无 wire
            raise 会话投影错误('会话投影 '+repr(登记['def']['key'])+' 没有 wire 视图')#错误
        状态=单元['state']#状态
        校验=登记['def']['stateSchema']#可选
        if 校验 is not None:#校验状态
            状态=校验(状态)#解析
        视图=wire['view'](状态)#视图
        视图校验=wire['viewSchema'] if 'viewSchema' in wire else None#可选视图校验
        if 视图校验 is not None:#校验视图
            return 视图校验(视图)#解析
        return 视图#原样

    register=登记#英文别名
    stateOf=状态#英文别名
    onChanged=变更时#英文别名
    snapshot=快照#英文别名
    cachedSnapshot=缓存快照#英文别名

default=会话投影注册表#Cordis 默认导出槽
