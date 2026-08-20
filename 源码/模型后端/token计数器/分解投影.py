"""启发式上下文构成投影的纯折叠。对齐上游 `token-meter/src/breakdown-projection.ts`。公开面仅中文名。"""
from session import 归一请求头#规范请求头
from .类型 import 取#读取字段
from .计价 import 计价系统令牌,计价工具令牌#系统与工具计价
from .表面投影 import 折叠表面投影#O(1)表面折叠

__all__=['分解投影定义']#仅中文公开名

def 是否非负整数(值):#值为非负整数（含 1.0）时为真
    """值为非负整数（含 1.0）时为真。"""
    if isinstance(值,bool) or not isinstance(值,(int,float)):#不是数字
        return False#拒绝
    return 值==int(值) and 值>=0#整数且非负

class 分解视图模式:
    """上下文分解线路载荷模式。"""
    @staticmethod
    def parse(值):
        """校验三个非负整数。"""
        if not isinstance(值,dict):#必须是对象
            raise Exception('contextBreakdown view must be an object')#拒绝
        需要=('systemTokens','toolsTokens','messageTokens')#三个数字
        for 键 in 值:#自有键
            if 键 not in 需要:#未知键
                raise Exception(f'contextBreakdown view unknown key "{键}"')#严格
        结果={}#输出
        for 键 in 需要:#逐项
            if 键 not in 值:#缺键
                raise Exception(f'contextBreakdown view missing key "{键}"')#必填
            数字=值[键]#字段值
            if not 是否非负整数(数字):#非法
                raise Exception(f'contextBreakdown view {键} must be a nonnegative integer')#非负整数
            结果[键]=int(数字)#收成int
        return 结果#校验后的视图

def 分解初态():
    """初始全零。"""
    return {'systemTokens':0,'toolsTokens':0,'messageTokens':0}#初态

def 分解转移(状态,事件):
    """折一条分解事件。"""
    折叠=折叠表面投影(状态.get('claim'),事件)#折叠表面
    系统=状态['systemTokens']#沿用系统
    工具=状态['toolsTokens']#沿用工具
    if 取(事件,'type')=='request/header':#新请求头
        头=归一请求头(取(取(事件,'data'),'header'))#规范信封
        系统=计价系统令牌(头)#重计价系统
        工具=计价工具令牌(头)#重计价工具
    if (
        系统==状态['systemTokens']#系统未变
        and 工具==状态['toolsTokens']#工具未变
        and 折叠['deltaTokens']==0#表面未动
        and 折叠['claim'] is None#没有新声明
        and 状态.get('claim') is None#声明也没有
    ):
        return 状态#原状态
    结果={'systemTokens':系统,'toolsTokens':工具,'messageTokens':状态['messageTokens']+折叠['deltaTokens']}#新状态
    if 折叠['claim'] is not None:#有声明才带上
        结果['claim']=折叠['claim']#下一声明
    return 结果#返回

def 分解视图(状态):
    """去掉内部声明。"""
    return {'systemTokens':状态['systemTokens'],'toolsTokens':状态['toolsTokens'],'messageTokens':状态['messageTokens']}#对外三数

分解投影定义={
    'key':'contextBreakdown',#投影键
    'schema':分解视图模式,#视图模式
    'init':分解初态,#初始全零
    'apply':分解转移,#折一条事件
    'view':分解视图,#去掉内部声明
    'stateVersion':2,#状态版本
}#分解投影定义结束
