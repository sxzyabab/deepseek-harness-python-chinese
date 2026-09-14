import math#向零截断与 NaN
from ..智能体.类型 import 下一轮,下一步#两条待处理列表名

__all__=(#仅中文公开名
    '收件箱投影定义','循环收件箱','向零截断',
)#公开面结束

安全整数上限=9007199254740991#JSON 拼接入口安全整数上限

def 向零截断(值):#对齐 JS Math.trunc
    """对齐 JS Math.trunc，含 NaN 与无穷。"""
    if isinstance(值,bool):#布尔
        return int(值)#布尔当 0/1
    if isinstance(值,int):#整数
        return 值#整数原样
    if isinstance(值,float):#浮点
        if 值!=值:#NaN
            return float('nan')#NaN
        if 值==float('inf') or 值==float('-inf'):#无穷
            return 值#无穷原样
        return math.trunc(值)#向 0 截断
    try:#其它可截断
        return math.trunc(值)#其它可截断
    except (ValueError,OverflowError,TypeError):#不能截断
        return float('nan')#与 JS Math.trunc 的 NaN 对齐

def _空收件箱状态(头=None):#投影初值
    """标准 inbox 折叠初值。"""
    return {下一轮:[],下一步:[]}#两条空列表

def _应用收件箱投影(状态,事件):#投影折叠
    """重建待处理输入并拒绝无效耐久拼接历史。"""
    if 事件['type']!='agent/inbox/spliced':#非拼接
        return 状态#原样
    拼接=事件['data']#拼接载荷
    try:#校验并应用
        列表=状态[拼接['target']]#目标列表
        删除数=拼接['removedCount'] if 'removedCount' in 拼接 else 0#删除数
        起点=拼接['start']#起点
        起点是整数=(not isinstance(起点,bool)) and (isinstance(起点,int) or (isinstance(起点,float) and 起点.is_integer()))#排除布尔
        删除是整数=(not isinstance(删除数,bool)) and (isinstance(删除数,int) or (isinstance(删除数,float) and 删除数.is_integer()))#排除布尔
        起点合法=起点是整数 and abs(起点)<=安全整数上限 and 起点>=0 and 起点<=len(列表)#坐标
        删除合法=删除是整数 and abs(删除数)<=安全整数上限 and 删除数>=0#条数
        if not 起点合法 or not 删除合法 or 起点+删除数>len(列表):#越界
            raise ValueError('invalid inbox splice')#非法拼接
        起点=int(起点)#切片要整数
        删除数=int(删除数)#切片要整数
        下一批=list(列表)#拷贝
        下一批[起点:起点+删除数]=list(拼接['inserted'])#应用拼接
        if 拼接['target']==下一轮:#下一轮优先
            合在一起=下一批+list(状态[下一步])#合表
            下一状态={下一轮:下一批,下一步:状态[下一步]}#更新下轮
        else:#下一步优先
            合在一起=list(状态[下一轮])+下一批#合表
            下一状态={下一轮:状态[下一轮],下一步:下一批}#更新下步
        已见=set()#id 集
        for 消息 in 合在一起:#查重
            身份=消息['id']#消息 id
            if 身份 in 已见:#重复
                raise ValueError('message "'+str(身份)+'" is already pending')#重复
            已见.add(身份)#登记
        return 下一状态#新状态
    except Exception as 错误:#包装错误
        包装=ValueError('invalid persisted inbox splice at session seq '+str(事件['seq']))#带序号
        raise 包装 from 错误#带原因

def _收件箱视图(状态):#线视图
    """线值即折叠状态本身。"""
    return 状态#原样

收件箱投影定义={#标准 inbox 投影单元
    'key':'inbox',#键
    'stateSchema':None,#状态由折叠自检
    'init':_空收件箱状态,#初值
    'apply':_应用收件箱投影,#折叠
    'wire':{'viewSchema':None,'view':_收件箱视图},#线视图
    'stateVersion':1,#状态版本
}#定义结束

class 循环收件箱:#ReactLoopInbox
    """ReactLoopAgent 与聚焦提供者测试使用的驱动拥有耐久 Inbox 实现。"""

    def __init__(自身,投影,会话,派发):#登记投影
        """经投影登记表拥有标准 Inbox 投影。

        投影 - 拥有标准 Inbox 投影的登记表。
        会话 - 用耐久事件存储待处理输入的会话。
        派发 - Inbox 生命周期事件的智能体作用域通知（键 `发出`）。
        """
        自身.投影=投影#投影登记
        自身.会话=会话#会话
        自身.派发=派发#分发
        投影.登记(收件箱投影定义)#登记投影

    @property#下一轮队列
    def 下一轮队列(自身):#等待各自轮次的提示
        """等待各自轮次的提示。"""
        return 自身.当前()[下一轮]#读状态

    @property#下一步队列
    def 下一步队列(自身):#等待下一副作用边界的输入
        """等待下一个步骤边界的输入。"""
        return 自身.当前()[下一步]#读状态

    @property#是否有待处理
    def 有待处理(自身):#任一待处理列表是否含工作
        """任一待处理列表是否还有工作。"""
        状态=自身.当前()#当前状态
        return len(状态[下一轮])>0 or len(状态[下一步])>0#任一非空

    def 清空(自身):#清空
        """耐久取消全部待处理输入，先清下一步再清下一轮。"""
        自身.拼接(下一步,0,len(自身.下一步队列),[])#清下步
        自身.拼接(下一轮,0,len(自身.下一轮队列),[])#清下轮

    def 领取(自身,目标,轮次):#声明
        """取出并返回为一步提出的完整批次。"""
        已领=自身.变更(下一步,0,len(自身.下一步队列),[],False)#取下步
        if 目标==下一轮:#还要消费一条下一轮
            已领.extend(自身.变更(下一轮,0,1,[],False))#取下轮一条
        for 消息 in 已领:#通知声明
            自身.派发['发出']('agent/inbox/claimed',{'message':消息,'turn':轮次})#领取
        return 已领#返回批次

    def 追加(自身,目标,消息):#追加
        """向待处理列表追加一条消息。"""
        自身.拼接(目标,len(自身.当前()[目标]),0,[消息])#尾插

    def 前置(自身,目标,消息):#前置
        """向待处理列表前置一条消息。"""
        自身.拼接(目标,0,0,[消息])#头插

    def 替换(自身,消息身份,新消息):#替换
        """原地替换一条待处理消息。"""
        位置=自身.定位(消息身份)#定位
        if 位置 is None:#未找到
            return False#未找到
        自身.拼接(位置['target'],位置['index'],1,[新消息])#替换
        return True#成功

    def 移除(自身,消息身份):#移除
        """移除一条待处理消息。"""
        位置=自身.定位(消息身份)#定位
        if 位置 is None:#未找到
            return False#未找到
        自身.拼接(位置['target'],位置['index'],1,[])#删除
        return True#成功

    def 拼接(自身,目标,起点,删除数,插入):#公开拼接
        """应用标准拼接语义并耐久记录规范化结果。"""
        return 自身.变更(目标,起点,删除数,插入,True)#丢弃移除项

    def 定位(自身,消息身份):#定位
        """在两个拥有列表中定位一个待处理身份。"""
        状态=自身.当前()#当前
        for 目标 in (下一轮,下一步):#两列表
            下标=0#按插入序
            for 消息 in 状态[目标]:#查找
                if 消息['id']==消息身份:#命中
                    return {'target':目标,'index':下标}#命中
                下标+=1#前进
        return None#未找到

    def 当前(自身):#当前状态
        """读取当前耐久投影状态。"""
        状态=自身.投影.状态(自身.会话,'inbox')#读投影
        if 状态 is None:#未登记
            raise RuntimeError(#英文字符串
                'agent "'+str(自身.会话.id)+'" cannot read inbox state: its projection registration is not active',
            )#抛错
        return 状态#返回

    def 变更(自身,目标,起点,删除数,插入,丢弃移除):#内部变更
        """提交一次规范化变更并发布其存活事件。"""
        状态=自身.当前()#当前
        列表=状态[目标]#列表
        截断起点=向零截断(起点)#截断起点
        偏移=0 if 截断起点!=截断起点 else 截断起点#NaN 当 0
        if 偏移<0:#负索引
            实际起点=max(len(列表)+偏移,0)#自尾
        else:#夹紧
            实际起点=min(偏移,len(列表))#夹紧
        截断删除=向零截断(删除数)#截断删除
        原始删除=0 if 截断删除!=截断删除 else 截断删除#NaN 当 0
        实际删除=min(max(原始删除,0),len(列表)-实际起点)#实际删除
        实际起点=int(实际起点)#切片要整数（inf 已夹到长度）
        实际删除=int(实际删除)#切片要整数
        if 实际删除==0 and len(插入)==0:#无操作
            return []#无操作
        候选=list(列表)#候选
        候选[实际起点:实际起点+实际删除]=list(插入)#模拟
        if 目标==下一轮:#查重
            合在一起=候选+list(状态[下一步])#下轮优先
        else:#查重
            合在一起=list(状态[下一轮])+候选#下步优先
        已见=set()#id 集
        for 消息 in 合在一起:#查重
            身份=消息['id']#id
            if 身份 in 已见:#重复
                raise ValueError('message "'+str(身份)+'" is already pending')#重复
            已见.add(身份)#登记
        结果标记='canceled' if 丢弃移除 and 实际删除>0 else None#结果
        拼接={'target':目标,'start':实际起点,'inserted':插入}#事件载荷
        if 实际删除!=0:#有删除
            拼接['removedCount']=实际删除#删除数
        if 结果标记 is not None:#有结果
            拼接['outcome']=结果标记#结果
        移除=list(列表[实际起点:实际起点+实际删除])#移除副本
        事件=自身.会话.追加('agent/inbox/spliced',拼接)#追加事件（投影折叠）
        if 丢弃移除:#丢弃通知
            for 消息 in 移除:#逐条
                自身.派发['发出']('agent/inbox/discarded',{'message':消息})#丢弃
        for 消息 in 事件['data']['inserted']:#插入通知
            自身.派发['发出']('agent/inbox/inserted',{'message':消息})#插入
        return 移除#返回移除
