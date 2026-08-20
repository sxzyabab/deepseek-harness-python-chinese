"""确定性工具结果修剪的配置解析。"""
from llm import 深冻结,结构化克隆#导入深冻结与拆离克隆

修剪标记='\n\n[... tool result middle pruned ...]\n\n'#替换每一段被删中间跨度的固定标记
默认预算=深冻结({#冻结的默认预算
    'thresholdChars':8192,#触发修剪的码点阈值
    'headChars':4096,#保留的开头码点数
    'tailChars':1024,#保留的结尾码点数
})#默认预算结束
配置键集合=frozenset(('thresholdChars','headChars','tailChars'))#允许的配置键
def 码点长度(文本):#按码点计长度
    """统计 Unicode 码点，不拆开代理对。"""
    return len(文本)#Python3 字符串按码点计长

def 是否整数(值):#对齐 JS Number.isInteger，排除布尔
    """对齐 JS Number.isInteger，排除布尔。"""
    if isinstance(值,bool):#布尔不是数字
        return False#布尔不是整数
    if isinstance(值,int):#整数
        return True#是整数
    if isinstance(值,float) and 值.is_integer():#整值浮点
        return True#是整数
    return False#其它类型

def 断言正整数(名称,值):#校验正整数
    """校验字段为正整数，否则抛错。"""
    if (not 是否整数(值)) or 值<=0:#非整数或非正
        raise Exception('ToolResultPruneConfig: '+名称+' ('+str(值)+') must be a positive integer')#字段名进入错误文案

def 断言非负整数(名称,值):#校验非负整数
    """校验字段为非负整数，否则抛错。"""
    if (not 是否整数(值)) or 值<0:#非整数或为负
        raise Exception('ToolResultPruneConfig: '+名称+' ('+str(值)+') must be a non-negative integer')#字段名进入错误文案

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段，缺席为缺省。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 解析配置(配置=None):#解析修剪预算
    """解析并校验修剪预算，返回分离的深不可变配置。"""
    if 配置 is None:#缺省空配置
        配置={}#空配置
    for 键 in 配置:#拒绝未知键，对齐 Object.keys
        if 键 not in 配置键集合:#键不在允许集
            raise Exception('ToolResultPruneConfig: unknown key "'+str(键)+'" (allowed: thresholdChars, headChars, tailChars)')#未知键错误
    阈值=取字段(配置,'thresholdChars')#原始阈值
    if 阈值 is None:#缺省
        阈值=默认预算['thresholdChars']#默认阈值
    开头=取字段(配置,'headChars')#原始开头
    if 开头 is None:#缺省
        开头=默认预算['headChars']#默认开头
    结尾=取字段(配置,'tailChars')#原始结尾
    if 结尾 is None:#缺省
        结尾=默认预算['tailChars']#默认结尾
    已解析={#套上默认值
        'thresholdChars':阈值,#阈值
        'headChars':开头,#开头
        'tailChars':结尾,#结尾
    }#已解析结束
    断言正整数('thresholdChars',已解析['thresholdChars'])#阈值须为正整数
    断言非负整数('headChars',已解析['headChars'])#开头须为非负整数
    断言非负整数('tailChars',已解析['tailChars'])#结尾须为非负整数
    发出码点=已解析['headChars']+码点长度(修剪标记)+已解析['tailChars']#发出的开头加标记加结尾
    if 发出码点>已解析['thresholdChars']:#发出的比阈值还大则永远触发
        raise Exception('ToolResultPruneConfig: headChars + marker + tailChars ('+str(发出码点)+') must be at most thresholdChars ('+str(已解析['thresholdChars'])+')')#预算自相矛盾
    return 深冻结(结构化克隆(已解析))#深拷贝后再冻结
