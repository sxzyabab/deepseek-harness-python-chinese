"""`ctx.sessionProjections` 注册表与驱动逻辑（对齐上游 session-projection/src/index.ts）。"""
import weakref#按会话弱引用缓存单元
from ...依赖 import cordis#外部依赖胶水
服务=cordis.服务#Cordis 服务基类
from ...模型后端.llm import 结构化克隆#深拷贝检查点行

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 是否安全整数(值):#对齐 JS Number.isSafeInteger
    """对齐 JS Number.isSafeInteger。"""
    if isinstance(值,bool):#布尔不是整数
        return False#不是
    if isinstance(值,int):#整数
        return abs(值)<=9007199254740991#安全范围
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return abs(值)<=9007199254740991#安全范围
    return False#其它

class 会话投影注册表(服务):#会话投影注册表服务
    """订阅 session/event 一次，对每个已登记单元急切驱动 apply；变更引用通知变更馈送。"""
    def __init__(自身,上下文):#安装为 ctx.sessionProjections
        """创建并安装注册表。"""
        super().__init__(上下文,'sessionProjections')#服务名
        自身._登记={}#键→登记记录
        自身._监听=set()#变更馈送监听器
        def 收到创建(会话):#新会话 seq=0 时播种单元
            """新会话 seq=0 时为每个已登记单元播种初始状态。"""
            if 取字段(会话,'seq')!=0:#只处理空日志创建
                return#跳过
            for 登记 in 自身._登记.values():#每个单元
                if 登记['cells'].get(会话) is not None:#已有单元
                    continue#跳过
                登记['cells'][会话]={'state':登记['def']['init'](取字段(会话,'header')),'observedSeq':-1}#初始单元
        上下文.on('session/created',收到创建)#监听创建
        def 收到事件(会话,事件):#每个提交事件驱动全部单元
            """每个提交事件驱动全部单元。"""
            自身._驱动(会话,事件)#急切驱动
        上下文.on('session/event',收到事件)#监听事件

    def 登记(自身,定义):#登记一个投影单元
        """登记一个域投影单元；返回拆除器。"""
        键=取字段(定义,'key')#单元键
        状态版本=取字段(定义,'stateVersion')#状态版本
        if (not 是否安全整数(状态版本)) or 状态版本<0:#非法版本
            raise Exception('session projection '+repr(键)+' stateVersion must be a non-negative integer, got '+str(状态版本))#拒绝
        wire=取字段(定义,'wire')#可选 wire 块
        擦除={#类型擦除后的单元
            'key':键,#键
            'stateSchema':取字段(定义,'stateSchema'),#状态校验（Python 侧可选）
            'init':取字段(定义,'init'),#init
            'apply':取字段(定义,'apply'),#apply
            'wire':None if wire is None else {'viewSchema':取字段(wire,'viewSchema'),'view':取字段(wire,'view')},#wire
            'stateVersion':状态版本,#版本
        }#擦除结束
        def 效果体():#effect 登记与引用计数
            """登记或增加引用；拆除时减引用。"""
            已有=自身._登记.get(键)#已有登记
            if 已有 is None:#首次
                自身._登记[键]={'def':擦除,'cells':weakref.WeakKeyDictionary(),'refs':1}#新登记
            else:#共享键
                if 已有['def']['stateVersion']!=状态版本:#版本冲突
                    raise Exception('session projection key '+repr(键)+' is already registered at stateVersion '+str(已有['def']['stateVersion'])+'; refusing to share it with stateVersion '+str(状态版本))#拒绝
                已有['refs']+=1#加引用
            def 拆除():#减少引用
                """最后一个引用离开时删除键。"""
                活=自身._登记.get(键)#当前登记
                if 活 is None:#已删
                    return#结束
                活['refs']-=1#减引用
                if 活['refs']==0:#无人引用
                    del 自身._登记[键]#删除
            return 拆除#拆除器
        拆除=自身.ctx.effect(效果体,'sessionProjections.register()')#挂 effect
        return lambda:拆除()#返回拆除闭包

    register=登记#Cordis 协议槽

    def 变更时(自身,监听器):#订阅变更馈送
        """订阅变更馈送；返回拆除器。"""
        def 效果体():#effect 订阅
            """加入并拆除时移除监听器。"""
            自身._监听.add(监听器)#加入
            def 拆除():#移除
                自身._监听.discard(监听器)#移除
            return 拆除#拆除器
        拆除=自身.ctx.effect(效果体,'sessionProjections.onChanged()')#挂 effect
        return lambda:拆除()#返回拆除闭包

    onChanged=变更时#Cordis 协议槽

    def 状态(自身,会话,键):#读取一个单元的主机状态
        """读取一个单元在会话游标处的主机状态。"""
        登记=自身._登记.get(键)#查找登记
        if 登记 is None:#未登记
            return None#缺席
        自身._物化单元(会话)#物化全部单元
        return 自身._单元(登记,会话)['state']#返回状态

    stateOf=状态#Cordis 协议槽

    def 快照(自身,会话,键们=None):#一致读取切面
        """读取每个已登记客户端可见单元在当前水位的一致切面。"""
        值们={}#wire 值
        选中=None if 键们 is None else set(键们)#可选过滤
        自身._物化单元(会话)#物化
        for 登记 in 自身._登记.values():#逐单元
            if 登记['def']['wire'] is None:#仅主机
                continue#跳过
            单元键=登记['def']['key']#键
            if 选中 is not None and 单元键 not in 选中:#过滤
                continue#跳过
            单元=自身._单元(登记,会话)#单元
            值们[单元键]=自身._视图单元(登记,单元)#校验视图
        return {'asOfSeq':取字段(会话,'seq')-1,'values':值们}#快照

    snapshot=快照#Cordis 协议槽

    def 缓存快照(自身,会话,键们=None):#只读已物化缓存
        """只读已物化客户端可见单元，不折叠历史。"""
        值们={}#wire 值
        水位=None#最低水位
        选中=None if 键们 is None else set(键们)#可选过滤
        for 登记 in 自身._登记.values():#逐单元
            if 登记['def']['wire'] is None:#仅主机
                continue#跳过
            单元键=登记['def']['key']#键
            if 选中 is not None and 单元键 not in 选中:#过滤
                continue#跳过
            单元=登记['cells'].get(会话)#已物化单元
            if 单元 is None:#未物化
                continue#跳过
            值们[单元键]=自身._视图单元(登记,单元)#视图
            水位=单元['observedSeq'] if 水位 is None else min(水位,单元['observedSeq'])#最低水位
        if 水位 is None:#无 wire 单元
            return None#缺席
        return {'asOfSeq':水位,'values':值们}#缓存快照

    cachedSnapshot=缓存快照#Cordis 协议槽

    def 检查点(自身,会话):#状态级检查点
        """每个已登记单元在当前水位的可持久化行。"""
        行们={}#键→行
        for 登记 in 自身._登记.values():#逐单元
            单元=自身._单元(登记,会话)#物化单元
            行们[登记['def']['key']]={'ver':登记['def']['stateVersion'],'seq':单元['observedSeq'],'val':结构化克隆(单元['state'])}#分离克隆
        return 行们#检查点

    checkpoint=检查点#Cordis 协议槽

    def 恢复地板(自身,检查点):#恢复尾部读取起点
        """返回 persistence readFrom 应使用的 seq（比可用水位低 1）。"""
        地板=None#聚合地板
        for 登记 in 自身._登记.values():#逐单元
            行=检查点.get(登记['def']['key'])#行
            需要=0 if 行 is None or 行['ver']!=登记['def']['stateVersion'] else max(行['seq']+1,0)#需从哪开始
            地板=需要 if 地板 is None else min(地板,需要)#取最小
        if 地板 is None:#无单元
            return None#无需读
        return max(地板-1,0)#一事件以下的锚点

    restoreFloor=恢复地板#Cordis 协议槽

    def 视图检查点(自身,检查点,键们=None):#零 IO 查看检查点
        """从持久化行直接视图化 wire 值。"""
        值们={}#wire 值
        选中=None if 键们 is None else set(键们)#过滤
        for 登记 in 自身._登记.values():#逐单元
            定义=登记['def']#擦除定义
            if 定义['wire'] is None:#仅主机
                continue#跳过
            单元键=定义['key']#键
            if 选中 is not None and 单元键 not in 选中:#过滤
                continue#跳过
            行=检查点.get(单元键)#行
            if 行 is None or 行['ver']!=定义['stateVersion']:#不可用
                continue#跳过
            状态=行['val']#状态
            校验=定义.get('stateSchema')#可选校验
            if 校验 is not None:#有校验器
                try:#校验
                    状态=校验(状态)#解析
                except Exception:#畸形
                    continue#跳过
            值们[单元键]=定义['wire']['view'](状态)#视图
        return 值们#部分映射

    viewCheckpoint=视图检查点#Cordis 协议槽

    def 恢复(自身,检查点,事件们,基础序号,头):#冷读折叠
        """从检查点与日志后缀恢复快照并刷新检查点。"""
        结束序号=事件们[-1]['seq'] if len(事件们)>0 else 基础序号-1#日志末端
        值们={}#wire 值
        刷新={}#刷新检查点
        for 登记 in 自身._登记.values():#逐单元
            定义=登记['def']#擦除定义
            行=检查点.get(定义['key'])#行
            可用=(行 is not None and 行['ver']==定义['stateVersion'] and 行['seq']>=基础序号-1 and 行['seq']<=结束序号)#可用行
            if (not 可用) and 基础序号>0:#中缀恢复不可行
                raise Exception('session projection '+repr(定义['key'])+' cannot restore from seq '+str(基础序号)+': its checkpoint row is missing, version-mismatched, or beyond the supplied log end; re-read from seq 0')#拒绝
            状态=行['val'] if 可用 else 定义['init'](头)#种子状态
            校验=定义.get('stateSchema')#可选校验
            if 可用 and 校验 is not None:#校验种子
                状态=校验(状态)#解析
            起点=行['seq'] if 可用 else 基础序号-1#已折叠到的 seq
            起始索引=起点-基础序号+1#事件数组起点
            for 索引 in range(起始索引,len(事件们)):#尾重放
                事件=事件们[索引]#事件
                期望=基础序号+索引#期望 seq
                if 事件 is None or 取字段(事件,'seq')!=期望:#缺口
                    raise Exception('session projection '+repr(定义['key'])+' cannot restore across missing seq '+str(期望))#拒绝
                状态=定义['apply'](状态,事件)#折叠
            if 定义['wire'] is not None:#有 wire
                值们[定义['key']]=定义['wire']['view'](状态)#视图
            刷新[定义['key']]={'ver':定义['stateVersion'],'seq':结束序号,'val':状态}#刷新行
        return {'snapshot':{'asOfSeq':结束序号,'values':值们},'checkpoint':刷新}#结果

    restore=恢复#Cordis 协议槽

    def 注水(自身,会话,检查点,事件们,基础序号):#为已预备会话安装恢复切面
        """把恢复状态装进会话单元缓存。"""
        结束序号=事件们[-1]['seq'] if len(事件们)>0 else 基础序号-1#切面末端
        完整=True#是否已全部在水位
        for 登记 in 自身._登记.values():#检查水位
            当前=登记['cells'].get(会话)#当前单元
            if 当前 is None or 当前['observedSeq']!=结束序号:#未齐
                完整=False#需要恢复
                break#停扫
        if 完整:#已齐
            值们={}#wire 值
            for 登记 in 自身._登记.values():#逐单元
                if 登记['def']['wire'] is None:#仅主机
                    continue#跳过
                单元=登记['cells'][会话]#单元
                值们[登记['def']['key']]=自身._视图单元(登记,单元)#视图
            return {'asOfSeq':结束序号,'values':值们}#快照
        已恢复=自身.恢复(检查点,事件们,基础序号,取字段(会话,'header'))#冷恢复
        for 登记 in 自身._登记.values():#安装单元
            行=已恢复['checkpoint'].get(登记['def']['key'])#行
            if 行 is None:#无行
                continue#跳过
            当前=登记['cells'].get(会话)#当前
            if 当前 is not None and 当前['observedSeq']>行['seq']:#更新
                continue#保留更新
            登记['cells'][会话]={'state':行['val'],'observedSeq':行['seq']}#安装
        return 已恢复['snapshot']#快照

    hydrate=注水#Cordis 协议槽

    def _物化单元(自身,会话):#物化全部登记单元
        """把每个登记单元物化到会话当前游标。"""
        for 登记 in 自身._登记.values():#逐单元
            自身._单元(登记,会话)#物化

    def _构建单元(自身,定义,头,事件们):#从 init 折叠前缀
        """从 init 折叠事件前缀。"""
        状态=定义['init'](头)#初始
        for 事件 in 事件们:#逐事件
            状态=定义['apply'](状态,事件)#折叠
        末序号=事件们[-1]['seq'] if len(事件们)>0 else -1#末 seq
        return {'state':状态,'observedSeq':末序号}#单元

    def _单元(自身,登记,会话):#读取或懒构建单元
        """读取或懒构建单元并推进到会话游标。"""
        单元=登记['cells'].get(会话)#已有
        if 单元 is None:#首次
            单元=自身._构建单元(登记['def'],取字段(会话,'header'),取字段(会话,'events'))#全日志
            登记['cells'][会话]=单元#缓存
        else:#已有
            自身._推进单元(登记['def'],单元,取字段(会话,'events'),取字段(会话,'seq')-1)#推进
        return 单元#单元

    def _推进单元(自身,定义,单元,事件们,直到序号):#推进已有单元
        """把已有单元推进到连续前缀末端。"""
        if 单元['observedSeq']>=直到序号:#已够
            return#结束
        for 序号 in range(单元['observedSeq']+1,直到序号+1):#逐 seq
            事件=事件们[序号] if 序号<len(事件们) else None#事件
            if 事件 is None or 取字段(事件,'seq')!=序号:#缺口
                raise Exception('session projection '+repr(定义['key'])+' cannot advance across missing seq '+str(序号))#拒绝
            下一=定义['apply'](单元['state'],事件)#折叠
            单元['state']=下一#写回
            单元['observedSeq']=序号#水位

    def _驱动(自身,会话,事件):#急切驱动一个事件
        """把一次提交事件过全部登记单元。"""
        for 登记 in 自身._登记.values():#逐单元
            单元=登记['cells'].get(会话)#单元
            if 单元 is not None and 单元['observedSeq']>=取字段(事件,'seq'):#已见过
                continue#跳过
            if 单元 is None:#晚到构建
                前缀=取字段(会话,'events')[:取字段(事件,'seq')]#前缀
                单元=自身._构建单元(登记['def'],取字段(会话,'header'),前缀)#构建
                登记['cells'][会话]=单元#缓存
            else:#推进到事件前
                自身._推进单元(登记['def'],单元,取字段(会话,'events'),取字段(事件,'seq')-1)#推进
            先前=单元['state']#先前状态
            下一=登记['def']['apply'](先前,事件)#折叠
            变更=下一 is not 先前#引用变更
            单元['state']=下一#写回
            单元['observedSeq']=取字段(事件,'seq')#水位
            if 变更 and 登记['def']['wire'] is not None and len(自身._监听)>0:#通知
                值=自身._视图单元(登记,单元)#视图
                for 监听器 in 自身._监听:#馈送
                    监听器(会话,登记['def']['key'],值,取字段(事件,'seq'))#通知

    def _视图单元(自身,登记,单元):#校验 wire 视图
        """返回 schema 校验后的 wire 视图。"""
        wire=登记['def']['wire']#wire
        if wire is None:#无 wire
            raise Exception('session projection '+repr(登记['def']['key'])+' has no wire view')#错误
        状态=单元['state']#状态
        校验=登记['def'].get('stateSchema')#可选
        if 校验 is not None:#校验状态
            状态=校验(状态)#解析
        视图=wire['view'](状态)#视图
        视图校验=wire.get('viewSchema')#可选视图校验
        if 视图校验 is not None:#校验视图
            return 视图校验(视图)#解析
        return 视图#原样

default=会话投影注册表#默认导出
默认=会话投影注册表#中文默认导出
