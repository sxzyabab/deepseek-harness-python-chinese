"""确定性工具结果修剪的配置解析。"""
from ...模型后端.llm import 深冻结,结构化克隆#导入深冻结与拆离克隆

修剪标记='\n\n[... tool result middle pruned ...]\n\n'#替换每一段被删中间跨度的固定标记
默认预算=深冻结({#冻结的默认预算
    'thresholdChars':8192,#触发修剪的码点阈值
    'headChars':4096,#保留的开头码点数
    'tailChars':1024,#保留的结尾码点数
})#默认预算结束
配置键集合=frozenset(('thresholdChars','headChars','tailChars'))#允许的配置键

class 工具结果裁剪错误(Exception):
    """工具结果裁剪包的异常基类。"""

def 码点长度(文本):
    """统计 Unicode 码点，不拆开代理对。"""
    return len(文本)#Python3 字符串按码点计长

def 校验正整数(名称,值):
    """校验字段为正整数，否则抛错。"""
    是整数=(not isinstance(值,bool)) and (isinstance(值,int) or (isinstance(值,float) and 值.is_integer()))#排除布尔
    if (not 是整数) or 值<=0:#非整数或非正
        raise 工具结果裁剪错误('ToolResultPruneConfig: '+名称+' ('+str(值)+') must be a positive integer')#字段名进入错误文案

def 校验非负整数(名称,值):
    """校验字段为非负整数，否则抛错。"""
    是整数=(not isinstance(值,bool)) and (isinstance(值,int) or (isinstance(值,float) and 值.is_integer()))#排除布尔
    if (not 是整数) or 值<0:#非整数或为负
        raise 工具结果裁剪错误('ToolResultPruneConfig: '+名称+' ('+str(值)+') must be a non-negative integer')#字段名进入错误文案

def 解析配置(配置=None):
    """解析并校验修剪预算，返回分离的深不可变配置。"""
    if 配置 is None:#缺省空配置
        配置={}#空配置
    for 键 in 配置:#拒绝未知键，对齐 Object.keys
        if 键 not in 配置键集合:#键不在允许集
            raise 工具结果裁剪错误('ToolResultPruneConfig: unknown key "'+str(键)+'" (allowed: thresholdChars, headChars, tailChars)')#未知键错误
    阈值=配置['thresholdChars'] if 'thresholdChars' in 配置 else 默认预算['thresholdChars']#阈值
    开头=配置['headChars'] if 'headChars' in 配置 else 默认预算['headChars']#开头
    结尾=配置['tailChars'] if 'tailChars' in 配置 else 默认预算['tailChars']#结尾
    已解析={#套上默认值
        'thresholdChars':阈值,#阈值
        'headChars':开头,#开头
        'tailChars':结尾,#结尾
    }#已解析结束
    校验正整数('thresholdChars',已解析['thresholdChars'])#阈值须为正整数
    校验非负整数('headChars',已解析['headChars'])#开头须为非负整数
    校验非负整数('tailChars',已解析['tailChars'])#结尾须为非负整数
    发出码点=已解析['headChars']+码点长度(修剪标记)+已解析['tailChars']#发出的开头加标记加结尾
    if 发出码点>已解析['thresholdChars']:#发出的比阈值还大则永远触发
        raise 工具结果裁剪错误('ToolResultPruneConfig: headChars + marker + tailChars ('+str(发出码点)+') must be at most thresholdChars ('+str(已解析['thresholdChars'])+')')#预算自相矛盾
    return 深冻结(结构化克隆(已解析))#深拷贝后再冻结
