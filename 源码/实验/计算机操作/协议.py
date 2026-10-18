'模型工具准入和原生对象门面共用的 JSON 校验。线上方法名保持英文'
import json,math,re
from ...基础设施.通用工具.序列化编码 import 严格解码base64

__all__=[
    '参数错误','协议错误','请求问题消息','尝试请求','请求','请求模式',
    '应用程序结果','运行应用程序结果','发现应用程序结果','窗口结果','状态结果',
    '原生截图结果','截图结果','能力结果','动作结果','悬停结果','显示结果','授权结果',
]

标识上限=2**32-1#窗口与像素标识的上界
进程上限=2**31-1#进程号上界
非空白=re.compile(r'\S')#查询至少要有一个非空白字符
摘要64=re.compile(r'^[a-f0-9]{64}$')#应用程序身份摘要
修饰键表=('command','control','option','shift','fn')#指针修饰键
按钮表=('left','right','middle')#鼠标按钮
悬停路线表=('accessibility','system-pointer')#悬停路线
选择种类表=('text','cursor_before','cursor_after')#文本选择放置
粘贴格式表=('text','html')#剪贴板格式
图像类型表=('image/png','image/jpeg','image/webp','image/gif')#模型请求图像类型

class 参数错误(Exception):
    '模型操作没通过准入'

    def __init__(自身,消息):
        '记下给调用方看的说明'
        super().__init__(消息)#异常文本
        自身.name='Error'#与普通 Error 同一身份
        自身.message=消息#消息正文

class 协议错误(Exception):
    '原生结果没通过校验'

    def __init__(自身,消息):
        '记下说明'
        super().__init__(消息)#异常文本
        自身.message=消息#消息正文

def 收到类型(值):
    '给校验说明用的输入类别名'
    if 值 is None:#空
        return 'null'#空
    if isinstance(值,bool):#布尔不是数字
        return 'boolean'#布尔
    if isinstance(值,str):#字符串
        return 'string'#字符串
    if isinstance(值,(int,float)):#数字
        if isinstance(值,float) and math.isnan(值):#非数
            return 'NaN'#非数
        return 'number'#数字
    if isinstance(值,list):#数组
        return 'array'#数组
    if isinstance(值,dict):#对象
        return 'object'#对象
    return type(值).__name__#其余类型名

def 问题(码,路径,消息,键=None,错误=None):
    '一条校验问题。路径从被校验值的根算起'
    项={'code':码,'path':list(路径),'message':消息}#问题
    if 键 is not None:#多余键
        项['keys']=list(键)#多余键
    if 错误 is not None:#联合各支
        项['errors']=错误#联合各支
    return 项#问题

def 请求问题消息(问题列表,父路径=None):
    '把问题收成字段说明。联合只保留问题最少的那些支'
    if 父路径 is None:#根
        父路径=[]#根路径
    文本=[]#说明片段
    for 项 in 问题列表:#逐条
        路径=list(父路径)+list(项['path'])#加上父路径
        if 项['code']=='invalid_union':#联合
            各组=项['errors']#各支
            最少=min(len(组) for 组 in 各组)#最少问题数
            片段=[]#并列说明
            for 组 in 各组:#问题最少的支
                if len(组)==最少:#命中最少
                    片段.append(请求问题消息(组,路径))#递归
            文本.append(' or '.join(dict.fromkeys(片段)))#去重后用 or 连接
            continue#下一条
        字段=路径[1:]#丢掉包裹字段，失败属于参数
        if 项['code']=='unrecognized_keys':#多余键
            键文本=', '.join('.'.join([str(段) for 段 in 字段]+[键]) for 键 in 项['keys'])#键路径
            文本.append(键文本+': not accepted for these arguments')#不接受
            continue#下一条
        前缀='.'.join(str(段) for 段 in 字段)#字段路径
        if 前缀=='':#没有字段
            文本.append(项['message'])#只留说明
        else:#有字段
            文本.append(前缀+': '+项['message'])#字段加说明
    return '; '.join(dict.fromkeys(文本))#相同说明只留一次

def 检查数(值,路径,最小=None,最大=None,整数=False,正=False,非负=False):
    '有限数字。整数不接受小数，布尔不是数字'
    if isinstance(值,float) and math.isnan(值):#非数
        return [问题('invalid_type',路径,'Invalid input: expected number, received NaN')]#非数
    if isinstance(值,bool) or not isinstance(值,(int,float)):#不是数字
        return [问题('invalid_type',路径,'Invalid input: expected number, received '+收到类型(值))]#类型不对
    if isinstance(值,float) and math.isinf(值):#无穷
        return [问题('invalid_type',路径,'Invalid input: expected number, received Infinity')]#无穷
    if 整数 and 值!=int(值):#小数
        return [问题('invalid_type',路径,'Invalid input: expected int, received number')]#不是整数
    if 正 and 值<=0:#必须大于 0
        return [问题('too_small',路径,'Too small: expected number to be >0')]#太小
    if 非负 and 值<0:#必须大于等于 0
        return [问题('too_small',路径,'Too small: expected number to be >=0')]#太小
    if 最小 is not None and 值<最小:#低于下界
        return [问题('too_small',路径,'Too small: expected number to be >='+str(最小))]#太小
    if 最大 is not None and 值>最大:#高于上界
        return [问题('too_big',路径,'Too big: expected number to be <='+str(最大))]#太大
    return []#通过

def 数检查器(最小=None,最大=None,整数=False,正=False,非负=False):
    '做成字段检查函数'
    def 检查(值,路径):
        '按约束检查一个数字'
        return 检查数(值,路径,最小=最小,最大=最大,整数=整数,正=正,非负=非负)
    return 检查#检查函数

标识检查=数检查器(整数=True,正=True,最大=标识上限)#窗口标识
进程检查=数检查器(整数=True,正=True,最大=进程上限)#进程号
点检查=数检查器(非负=True)#截图像素
相对点检查=数检查器(整数=True,最小=0,最大=1000)#千分比
非负整数检查=数检查器(整数=True,非负=True)#元素索引
滚动检查=数检查器(整数=True,最小=-10,最大=10)#滚动行数
任意数检查=数检查器()#任意有限数字
非负数检查=数检查器(非负=True)#宽度高度
正数检查=数检查器(正=True)#截图边长

def 检查字符串(值,路径,最小长=None,消息=None,正则=None):
    '字符串长度和模式'
    if not isinstance(值,str):#不是字符串
        return [问题('invalid_type',路径,'Invalid input: expected string, received '+收到类型(值))]#类型不对
    问题列表=[]#问题
    if 最小长 is not None and len(值)<最小长:#太短
        文案=消息 or ('Too small: expected string to have >='+str(最小长)+' characters')#说明
        问题列表.append(问题('too_small',路径,文案))#太短
    if 正则 is not None and 正则.search(值) is None:#模式不符
        问题列表.append(问题('invalid_string',路径,消息 or 'Invalid string'))#模式不符
    return 问题列表#问题

def 非空字符串(值,路径):
    '至少 1 个字符'
    return 检查字符串(值,路径,最小长=1)

def 任意字符串(值,路径):
    '任意字符串，允许空串'
    return 检查字符串(值,路径)

def 检查查询(值,路径):
    '搜索词不能为空，也不能只有空白'
    return 检查字符串(值,路径,最小长=1,消息='Expected a non-empty search string',正则=非空白)

def 检查布尔(值,路径):
    '只接受布尔'
    if not isinstance(值,bool):#不是布尔
        return [问题('invalid_type',路径,'Invalid input: expected boolean, received '+收到类型(值))]#类型不对
    return []#通过

def 检查可空布尔(值,路径):
    '布尔或空'
    if 值 is None:#空
        return []#通过
    return 检查布尔(值,路径)#布尔

def 检查字面(期望):
    '只接受这一个值'
    def 检查(值,路径):
        '比对字面量'
        if 值!=期望:#不是该值
            return [问题('invalid_value',路径,'Invalid input: expected '+json.dumps(期望,ensure_ascii=False))]#字面量不符
        return []#通过
    return 检查#检查函数

检查真=检查字面(True)#真
检查假=检查字面(False)#假

def 检查枚举(允许):
    '只接受列出的值'
    def 检查(值,路径):
        '比对枚举'
        if 值 not in 允许:#不在表内
            展示='|'.join(json.dumps(项,ensure_ascii=False) for 项 in 允许)#允许值
            return [问题('invalid_value',路径,'Invalid option: expected one of '+展示)]#不在表内
        return []#通过
    return 检查#检查函数

def 检查修饰键(值,路径):
    '修饰键数组，每一项都必须是已知键'
    if not isinstance(值,list):#不是数组
        return [问题('invalid_type',路径,'Invalid input: expected array, received '+收到类型(值))]#类型不对
    检查项=检查枚举(修饰键表)#单项
    问题列表=[]#问题
    下标=0#下标
    for 项 in 值:#逐项
        问题列表.extend(检查项(项,路径+[下标]))#单项
        下标+=1#前进
    return 问题列表#问题

def 检查点击次数(值,路径):
    '只接受 1 或 2'
    if 值==1 or 值==2:#合法次数
        return []#通过
    return 检查数(值,路径,整数=True,最小=1,最大=2)#说明沿用数字约束

def 检查字符串数组(值,路径):
    '字符串数组'
    if not isinstance(值,list):#不是数组
        return [问题('invalid_type',路径,'Invalid input: expected array, received '+收到类型(值))]#类型不对
    问题列表=[]#问题
    下标=0#下标
    for 项 in 值:#逐项
        问题列表.extend(任意字符串(项,路径+[下标]))#单项
        下标+=1#前进
    return 问题列表#问题

def 检查图像64(值,路径):
    '非空且再编码后与原文一致的 base64'
    问题列表=检查字符串(值,路径,最小长=1)#先是非空字符串
    if len(问题列表)>0:#已经不是字符串
        return 问题列表#返回
    try:#规范形式
        严格解码base64(值)#再编码必须一致
    except ValueError:#非规范
        return [问题('invalid_string',路径,'Expected canonical base64 image data')]#拒绝
    return []#通过

def 检查摘要(值,路径):
    '64 位小写十六进制'
    问题列表=检查字符串(值,路径,最小长=1)#先是字符串
    if len(问题列表)>0:#不是字符串
        return 问题列表#返回
    if 摘要64.fullmatch(值) is None:#不是摘要
        return [问题('invalid_string',路径,'Invalid application id')]#拒绝
    return []#通过

def 检查对象(值,路径,字段表,严格):
    '按字段表校验对象。字面量不符记为矛盾，供联合丢掉错误的支'
    if not isinstance(值,dict):#不是对象
        return [问题('invalid_type',路径,'Invalid input: expected object, received '+收到类型(值))],True,None#类型不对
    问题列表=[]#问题
    矛盾=False#字面量是否顶掉这一支
    结果={}#收下的字段
    for 名,规格 in 字段表.items():#逐字段
        if 名 not in 值:#缺席
            if 规格.get('required'):#必填
                问题列表.append(问题('invalid_type',路径+[名],'Invalid input: expected '+规格.get('expect','value')+', received undefined'))#缺字段
            continue#下一字段
        项=值[名]#取值
        if 项 is None and 规格.get('nullable'):#显式空
            结果[名]=None#收下空
            continue#下一字段
        if 'literal' in 规格 and 项!=规格['literal']:#字面量顶掉这一支
            矛盾=True#矛盾
        子=规格['check'](项,路径+[名])#检查
        问题列表.extend(子)#并入
        if len(子)==0:#通过才收下
            结果[名]=项#收下
    if 严格:#禁止多余键
        多余=[键 for 键 in 值 if 键 not in 字段表]#多余键
        if len(多余)>0:#有多余
            问题列表.append(问题('unrecognized_keys',路径,'',多余))#多余键
    return 问题列表,矛盾,结果#问题、矛盾、结果

def 对象结果(值,路径,字段表,严格=True):
    '单对象。有问题就没有结果'
    问题列表,_矛盾,结果=检查对象(值,路径,字段表,严格)#检查
    if len(问题列表)>0:#有问题
        return 问题列表,None#失败
    return [],结果#成功

def 检查联合(值,路径,分支列表):
    '对象联合。字面量对得上的支优先；仍并列时只留问题最少的支'
    记录=[]#全部支
    不矛盾=[]#字面量没顶掉的支
    for 字段表 in 分支列表:#逐支
        问题列表,矛盾,结果=检查对象(值,路径,字段表,True)#严格对象
        记录.append((问题列表,矛盾,结果))#记下
        if not 矛盾:#字面量相符
            不矛盾.append((问题列表,结果))#候选
            if len(问题列表)==0:#有一支完全通过
                return [],结果#采用它
    使用=不矛盾 if len(不矛盾)>0 else [(项[0],项[2]) for 项 in 记录]#有相符支就不用矛盾支
    最少=min(len(项[0]) for 项 in 使用)#最少问题数
    候选=[项 for 项 in 使用 if len(项[0])==最少]#最少的那些
    if len(候选)==1:#唯一一支
        return 候选[0][0],None#只报这一支
    相对=[]#嵌进联合时路径改成相对
    for 项 in 候选:#逐支
        相对.append(相对化(项[0],路径))#去掉共同前缀
    return [问题('invalid_union',路径,'',错误=相对)],None#并列

def 相对化(问题列表,前缀):
    '去掉联合节点自己的路径，格式化时再加回去'
    结果=[]#相对问题
    长度=len(前缀)#前缀长
    for 项 in 问题列表:#逐条
        副本=dict(项)#拷贝
        路径=list(项['path'])#原路径
        if 路径[:长度]==list(前缀):#以前缀开头
            副本['path']=路径[长度:]#去掉前缀
        结果.append(副本)#收下
    return 结果#相对问题

def 要求(问题列表,结果):
    '有问题就抛，否则返回收下的值'
    if len(问题列表)>0:#有问题
        raise 协议错误(请求问题消息(问题列表) or 'Invalid native result')#拒绝
    return 结果#通过

def 字段(检查,必填=True,期望='value',字面=None,可空=False):
    '字段规格'
    规格={'required':必填,'check':检查,'expect':期望}#规格
    if 字面 is not None:#字面量支
        规格['literal']=字面#期望字面量
    if 可空:#允许空
        规格['nullable']=True#允许空
    return 规格#规格

应用字段={#应用程序句柄
    'appHandle':字段(非空字符串,期望='string'),#句柄
}#应用字段结束
窗口字段={#窗口
    'appHandle':字段(非空字符串,期望='string'),#句柄
    'windowId':字段(标识检查,期望='number'),#窗口标识
}#窗口字段结束
快照字段={#元素索引
    'appHandle':字段(非空字符串,期望='string'),#句柄
    'snapshotId':字段(非空字符串,期望='string'),#快照
    'elementIndex':字段(非负整数检查,期望='number'),#元素索引
}#快照字段结束

def 坐标字段(相对):
    '绝对像素或千分比坐标'
    点=相对点检查 if 相对 else 点检查#坐标数
    规格={#坐标
        'appHandle':字段(非空字符串,期望='string'),#句柄
        'windowId':字段(标识检查,期望='number'),#窗口
        'snapshotId':字段(非空字符串,必填=False,期望='string'),#可选快照
        'x':字段(点,期望='number'),#横坐标
        'y':字段(点,期望='number'),#纵坐标
    }#坐标结束
    if 相对:#千分比必须显式打开
        规格['relative']=字段(检查真,期望='boolean',字面=True)#必须为真
    else:#省略或假表示像素
        规格['relative']=字段(检查假,必填=False,期望='boolean',字面=False)#可省略的假
    return 规格#坐标字段

def 拖拽字段(相对):
    '同一窗口内的拖拽端点'
    点=相对点检查 if 相对 else 点检查#坐标数
    规格={#拖拽
        'appHandle':字段(非空字符串,期望='string'),#句柄
        'windowId':字段(标识检查,期望='number'),#窗口
        'snapshotId':字段(非空字符串,必填=False,期望='string'),#可选快照
        'fromX':字段(点,期望='number'),#起点横坐标
        'fromY':字段(点,期望='number'),#起点纵坐标
        'toX':字段(点,期望='number'),#终点横坐标
        'toY':字段(点,期望='number'),#终点纵坐标
        'mouseButton':字段(检查枚举(按钮表),必填=False,期望='string'),#可选按钮
        'modifiers':字段(检查修饰键,必填=False,期望='array'),#可选修饰键
    }#拖拽结束
    if 相对:#千分比
        规格['relative']=字段(检查真,期望='boolean',字面=True)#必须为真
    else:#像素
        规格['relative']=字段(检查假,必填=False,期望='boolean',字面=False)#可省略的假
    return 规格#拖拽字段

def 指针字段(基础):
    '在一份目标上加上可选按钮、次数和修饰键'
    规格=dict(基础)#拷贝目标
    规格['mouseButton']=字段(检查枚举(按钮表),必填=False,期望='string')#按钮
    规格['clickCount']=字段(检查点击次数,必填=False,期望='number')#次数
    规格['modifiers']=字段(检查修饰键,必填=False,期望='array')#修饰键
    return 规格#指针字段

def 滚动字段(相对):
    '坐标加上两个轴向的行增量'
    规格=坐标字段(相对)#坐标
    规格['deltaLinesX']=字段(滚动检查,期望='number')#横向行数
    规格['deltaLinesY']=字段(滚动检查,期望='number')#纵向行数
    return 规格#滚动字段

操作表={}#方法到参数检查

def 登记操作(方法,检查):
    '登记一种模型操作的参数检查'
    操作表[方法]=检查#登记

def 空参数(参数,路径):
    '没有参数'
    return 对象结果(参数,路径,{})

def 参数检查(字段表):
    '固定对象参数'
    def 检查(参数,路径):
        '检查这一组字段'
        return 对象结果(参数,路径,字段表)
    return 检查#检查函数

def 联合检查(分支列表):
    '参数是若干对象支之一'
    def 检查(参数,路径):
        '检查联合'
        return 检查联合(参数,路径,分支列表)
    return 检查#检查函数

登记操作('getCapabilities',空参数)#能力
登记操作('listApps',空参数)#运行中的应用程序
登记操作('findApps',参数检查({'query':字段(检查查询,期望='string')}))#搜索
登记操作('getApp',参数检查({'selector':字段(非空字符串,期望='string')}))#选择
登记操作('activate',参数检查(应用字段))#激活
登记操作('show',参数检查({#显示
    'appHandle':字段(非空字符串,期望='string'),#句柄
    'windowId':字段(标识检查,必填=False,期望='number'),#可选窗口
}))#显示结束
登记操作('listWindows',参数检查(应用字段))#窗口列表
登记操作('getState',参数检查({#状态
    'appHandle':字段(非空字符串,期望='string'),#句柄
    'windowId':字段(标识检查,必填=False,期望='number'),#可选窗口
    'includeMenus':字段(检查布尔,必填=False,期望='boolean'),#展开菜单
    'details':字段(检查布尔,必填=False,期望='boolean'),#细节
}))#状态结束
登记操作('hover',联合检查([快照字段,坐标字段(False),坐标字段(True)]))#悬停
登记操作('click',联合检查([指针字段(快照字段),指针字段(坐标字段(False)),指针字段(坐标字段(True))]))#点击
登记操作('setValue',参数检查({#设值
    **快照字段,#元素
    'value':字段(任意字符串,期望='string'),#新值
}))#设值结束
登记操作('selectText',参数检查({#选文本
    **快照字段,#元素
    'text':字段(非空字符串,期望='string'),#要找的文本
    'prefix':字段(任意字符串,必填=False,期望='string'),#紧邻前缀
    'suffix':字段(任意字符串,必填=False,期望='string'),#紧邻后缀
    'selectionType':字段(检查枚举(选择种类表),必填=False,期望='string'),#放置方式
}))#选文本结束
登记操作('performSecondaryAction',参数检查({#次要动作
    **快照字段,#元素
    'action':字段(非空字符串,期望='string'),#动作名
}))#次要动作结束
登记操作('typeText',参数检查({#输入文本
    **应用字段,#应用程序
    'text':字段(任意字符串,期望='string'),#文本
}))#输入文本结束
登记操作('paste',参数检查({#粘贴
    **应用字段,#应用程序
    'text':字段(任意字符串,期望='string'),#剪贴板内容
    'format':字段(检查枚举(粘贴格式表),必填=False,期望='string'),#格式
}))#粘贴结束
登记操作('pressKey',参数检查({#按键
    **应用字段,#应用程序
    'key':字段(非空字符串,期望='string'),#键名
    'modifiers':字段(检查修饰键,必填=False,期望='array'),#修饰键
}))#按键结束
登记操作('scroll',联合检查([滚动字段(False),滚动字段(True)]))#滚动
登记操作('drag',联合检查([拖拽字段(False),拖拽字段(True)]))#拖拽
登记操作('screenshot',参数检查(窗口字段))#截图

def 尝试请求(值):
    '校验模型操作。成功时返回收下的对象，失败时返回问题'
    if not isinstance(值,dict):#不是对象
        return False,None,[问题('invalid_type',[],'Invalid input: expected object, received '+收到类型(值))]#类型不对
    问题列表=[]#根问题
    多余=[键 for 键 in 值 if 键 not in ('method','params')]#根上的多余键
    if len(多余)>0:#宿主字段不能从模型参数进来
        问题列表.append(问题('unrecognized_keys',[],'',多余))#多余键
    if 'method' not in 值:#缺方法
        问题列表.append(问题('invalid_type',['method'],'Invalid input: expected string, received undefined'))#缺方法
        方法=None#没有方法
    else:#有方法
        方法=值['method']#方法
        if not isinstance(方法,str) or 方法 not in 操作表:#未知方法
            问题列表.append(问题('invalid_value',['method'],'Invalid discriminator value'))#未知方法
            方法=None#不能继续按该方法检查
    if 'params' not in 值:#缺参数
        问题列表.append(问题('invalid_type',['params'],'Invalid input: expected object, received undefined'))#缺参数
    elif 方法 is not None:#已知方法
        子问题,结果=操作表[方法](值['params'],['params'])#只检查这一方法
        if len(问题列表)==0 and len(子问题)==0:#全部通过
            return True,{'method':方法,'params':结果},[]#收下
        return False,None,问题列表+子问题#合并问题
    return False,None,问题列表#根上就失败

def 请求(值):
    '校验并返回模型操作'
    成功,数据,问题列表=尝试请求(值)#校验
    if not 成功:#失败
        raise 参数错误(请求问题消息(问题列表) or 'Invalid request')#拒绝
    return 数据#操作

边界字段={#全局点边界
    'x':字段(任意数检查,期望='number'),#横坐标
    'y':字段(任意数检查,期望='number'),#纵坐标
    'width':字段(非负数检查,期望='number'),#宽
    'height':字段(非负数检查,期望='number'),#高
}#边界结束
正边界字段={#截图当时的窗口尺寸必须非零
    'x':字段(任意数检查,期望='number'),#横坐标
    'y':字段(任意数检查,期望='number'),#纵坐标
    'width':字段(正数检查,期望='number'),#宽
    'height':字段(正数检查,期望='number'),#高
}#正边界结束

def 检查边界(正尺寸):
    '普通边界或截图用的正尺寸边界'
    字段表=正边界字段 if 正尺寸 else 边界字段#选表
    def 检查(值,路径):
        '检查边界对象'
        问题列表,结果=对象结果(值,路径,字段表,False)#允许随后被结果模式剥掉未知键
        if len(问题列表)>0:#失败
            return 问题列表#问题
        return []#通过时由外层收下原对象里已验证的值
    return 检查#检查函数

窗口项字段={#一个窗口记录
    'windowId':字段(标识检查,期望='number'),#窗口标识
    'pid':字段(进程检查,期望='number'),#进程号
    'appName':字段(任意字符串,期望='string'),#应用程序名
    'title':字段(任意字符串,期望='string'),#标题
    'bounds':字段(检查边界(False),期望='object'),#边界
    'isOnScreen':字段(检查布尔,期望='boolean'),#是否在屏上
    'onCurrentSpace':字段(检查可空布尔,期望='boolean',可空=True),#当前空间，空表示未知
}#窗口项结束

def 检查窗口项(值,路径):
    '一个窗口记录'
    问题列表,_矛盾,结果=检查对象(值,路径,窗口项字段,False)#剥掉未知键
    if 'bounds' in 结果 if 结果 is not None else False:#边界已通过字段检查
        边界问题,边界=对象结果(值['bounds'],路径+['bounds'],边界字段,False)#再取边界对象
        if len(边界问题)==0:#边界有效
            结果['bounds']=边界#换成只含已知键的边界
    if len(问题列表)>0:#失败
        return 问题列表,None#失败
    return [],结果#窗口

def 检查窗口数组(值,路径):
    '窗口数组'
    if not isinstance(值,list):#不是数组
        return [问题('invalid_type',路径,'Invalid input: expected array, received '+收到类型(值))],None#类型不对
    问题列表=[]#问题
    结果=[]#窗口
    下标=0#下标
    for 项 in 值:#逐个
        子,窗口=检查窗口项(项,路径+[下标])#一项
        问题列表.extend(子)#并入
        if len(子)==0:#通过
            结果.append(窗口)#收下
        下标+=1#前进
    if len(问题列表)>0:#有问题
        return 问题列表,None#失败
    return [],结果#窗口数组

def 窗口结果(值):
    '校验当前窗口和它们的全局点边界'
    问题列表,结果=检查窗口数组(值,[])#数组
    return 要求(问题列表,结果)#窗口列表

def 应用程序结果(值,允许空进程=False):
    '选择成功后的进程身份。允许空进程时，尚未启动的选择可以没有 pid'
    字段表={#应用程序
        'appHandle':字段(非空字符串,期望='string'),#句柄
        'pid':字段(进程检查,期望='number',可空=允许空进程),#进程号
        'name':字段(任意字符串,期望='string'),#名称
        'bundleId':字段(任意字符串,必填=False,期望='string'),#可选包标识
    }#字段结束
    问题列表,结果=对象结果(值,[],字段表,False)#剥掉授权等旁路字段
    return 要求(问题列表,结果)#应用程序

def 运行应用程序结果(值):
    '辅助进程返回的正在运行的应用程序'
    if not isinstance(值,list):#不是数组
        raise 协议错误('Invalid native result')#拒绝
    字段表={#一项
        'pid':字段(进程检查,期望='number'),#进程号
        'name':字段(任意字符串,期望='string'),#名称
        'bundleId':字段(任意字符串,必填=False,期望='string'),#可选包标识
    }#字段结束
    结果=[]#列表
    下标=0#下标
    for 项 in 值:#逐个
        问题列表,收下=对象结果(项,[下标],字段表,False)#一项
        if len(问题列表)>0:#失败
            raise 协议错误(请求问题消息(问题列表) or 'Invalid native result')#拒绝
        结果.append(收下)#收下
        下标+=1#前进
    return 结果#列表

def 发现应用程序结果(值):
    '已安装应用程序。正在运行和已停止的记录必须能区分'
    if not isinstance(值,list):#不是数组
        raise 协议错误('Invalid native result')#拒绝
    身份={#共同身份
        'id':字段(非空字符串,期望='string'),#标识
        'displayName':字段(任意字符串,期望='string'),#显示名
        'path':字段(非空字符串,期望='string'),#路径
    }#身份结束
    运行中=dict(身份)#正在运行
    运行中['isRunning']=字段(检查真,期望='boolean',字面=True)#正在运行
    运行中['pid']=字段(进程检查,期望='number')#进程号
    已停止=dict(身份)#已停止
    已停止['isRunning']=字段(检查假,期望='boolean',字面=False)#已停止
    结果=[]#匹配
    下标=0#下标
    for 项 in 值:#逐个
        问题列表,收下=检查联合(项,[下标],[运行中,已停止])#二选一
        if len(问题列表)>0 or 收下 is None:#失败
            raise 协议错误(请求问题消息(问题列表) or 'Invalid native result')#拒绝
        结果.append(收下)#收下
        下标+=1#前进
    return 结果#匹配

def 检查状态窗口(值,路径):
    '状态里的窗口数组只贡献问题，对象由状态结果另行收下'
    问题列表,_窗口=检查窗口数组(值,路径)#数组
    return 问题列表#问题

def 状态结果(值):
    '带窗口和进程身份的观察，用来拒绝过期目标'
    字段表={#状态
        'appHandle':字段(非空字符串,期望='string'),#句柄
        'pid':字段(进程检查,期望='number'),#进程号
        'windowId':字段(标识检查,期望='number',可空=True),#窗口，空表示没有选定
        'focusedWindowId':字段(标识检查,必填=False,期望='number',可空=True),#焦点窗口
        'snapshotId':字段(非空字符串,期望='string'),#快照
        'tree':字段(任意字符串,期望='string'),#辅助功能文本
        'windows':字段(检查状态窗口,期望='array'),#窗口
        'truncated':字段(检查布尔,期望='boolean'),#是否截断
    }#字段结束
    问题列表,_矛盾,结果=检查对象(值,[],字段表,False)#剥掉未知键
    if 结果 is not None and isinstance(值,dict) and 'windows' in 值 and len([项 for 项 in 问题列表 if 'windows' in 项['path']])==0:#窗口通过
        _窗口问题,窗口=检查窗口数组(值['windows'],['windows'])#取窗口对象
        if _窗口问题 is not None and len(_窗口问题)==0:#有效
            结果['windows']=窗口#换成校验后的窗口
    return 要求(问题列表,结果)#状态

def 截图字段(图像类型检查,坐标空间):
    '原生 PNG 或模型请求图像'
    return {#截图
        'mimeType':字段(图像类型检查,期望='string'),#媒体类型
        'data':字段(检查图像64,期望='string'),#规范 base64
        'pixelWidth':字段(标识检查,期望='number'),#像素宽
        'pixelHeight':字段(标识检查,期望='number'),#像素高
        'windowId':字段(标识检查,期望='number'),#窗口
        'bounds':字段(检查边界(True),期望='object'),#正尺寸边界
        'coordinateSpace':字段(检查字面(坐标空间),期望='string',字面=坐标空间),#坐标空间
    }#截图结束

def 收下截图(值,字段表):
    '校验截图并替换边界为已知字段'
    问题列表,_矛盾,结果=检查对象(值,[],字段表,False)#剥掉未知键
    if 结果 is not None and isinstance(值,dict) and 'bounds' in 值:#有边界
        边界问题,边界=对象结果(值['bounds'],['bounds'],正边界字段,False)#正尺寸
        if len(边界问题)==0 and len([项 for 项 in 问题列表 if len(项['path'])>0 and 项['path'][0]=='bounds'])==0:#边界有效
            结果['bounds']=边界#换成边界
    return 要求(问题列表,结果)#截图

def 原生截图结果(值):
    '宿主准备图像之前的原始 PNG 和窗口点几何'
    return 收下截图(值,截图字段(检查字面('image/png'),'window-points'))#原生截图

def 截图结果(值):
    '编码后的模型请求图像。缺省输入坐标用这里的像素尺寸'
    return 收下截图(值,截图字段(检查枚举(图像类型表),'screenshot-pixels'))#模型截图

def 能力结果(值):
    '报告权限，不打开系统权限对话框'
    权限字段={#权限
        'accessibility':字段(检查布尔,期望='boolean'),#辅助功能
        'screenRecording':字段(检查布尔,期望='boolean'),#屏幕录制
    }#权限结束
    def 检查权限(项,路径):
        '权限对象'
        问题列表,_矛盾,结果=检查对象(项,路径,权限字段,False)#权限
        if len(问题列表)>0:#失败
            return 问题列表#问题
        return []#通过
    字段表={#能力
        'platform':字段(任意字符串,期望='string'),#平台
        'permissions':字段(检查权限,期望='object'),#权限
        'sessionLocked':字段(检查可空布尔,期望='boolean',可空=True),#会话锁，空表示没核实到控制台会话
        'methods':字段(检查字符串数组,期望='array'),#方法
        'coordinateSpace':字段(检查字面('screenshot-pixels'),期望='string',字面='screenshot-pixels'),#坐标空间
        'browser':字段(检查假,期望='boolean',字面=False),#没有浏览器列表
    }#字段结束
    问题列表,_矛盾,结果=检查对象(值,[],字段表,False)#能力
    if 结果 is not None and isinstance(值,dict) and 'permissions' in 值:#有权限
        权限问题,权限=对象结果(值['permissions'],['permissions'],权限字段,False)#权限对象
        if len(权限问题)==0:#有效
            结果['permissions']=权限#换成权限
    return 要求(问题列表,结果)#能力

def 动作结果(值):
    '动作已经送到原生调度，应用程序状态尚未核实'
    字段表={#动作
        'dispatched':字段(检查真,期望='boolean',字面=True),#已调度
        'verified':字段(检查假,期望='boolean',字面=False),#未核实
    }#字段结束
    问题列表,结果=对象结果(值,[],字段表,False)#动作
    return 要求(问题列表,结果)#动作

def 悬停结果(值):
    '悬停是否移动了用户的系统指针'
    字段表={#悬停
        'dispatched':字段(检查真,期望='boolean',字面=True),#已调度
        'verified':字段(检查假,期望='boolean',字面=False),#未核实
        'hoverRoute':字段(检查枚举(悬停路线表),期望='string'),#路线
        'systemPointerMoved':字段(检查布尔,期望='boolean'),#系统指针是否移动
    }#字段结束
    问题列表,结果=对象结果(值,[],字段表,False)#悬停
    return 要求(问题列表,结果)#悬停

def 显示结果(值):
    '后台恢复调度和采样到的前台变化。空表示当时观察不到'
    字段表={#显示
        'dispatched':字段(检查真,期望='boolean',字面=True),#已调度
        'verified':字段(检查假,期望='boolean',字面=False),#未核实
        'windowId':字段(标识检查,期望='number',可空=True),#被选中的窗口
        'foregroundChanged':字段(检查可空布尔,期望='boolean',可空=True),#前台是否变化
    }#字段结束
    问题列表,结果=对象结果(值,[],字段表,False)#显示
    return 要求(问题列表,结果)#显示

def 授权结果(值):
    '原生身份。观察和输入之前就要准入'
    if not isinstance(值,dict) or 'authorization' not in 值:#没有授权对象
        raise 协议错误('Invalid application authorization')#拒绝
    字段表={#授权
        'id':字段(检查摘要,期望='string'),#摘要
        'name':字段(任意字符串,期望='string'),#名称
        'executablePath':字段(非空字符串,期望='string'),#可执行路径
        'persistable':字段(检查布尔,期望='boolean'),#能否写入长期许可
    }#字段结束
    问题列表,结果=对象结果(值['authorization'],['authorization'],字段表,False)#授权
    return 要求(问题列表,结果)#授权

def 对象模式(属性,必填=None):
    '受支持的对象模式'
    节点={'type':'object','additionalProperties':False,'properties':属性}#对象
    if 必填:#有必填
        节点['required']=必填#必填
    return 节点#模式

def 操作模式(方法,参数模式):
    '一种方法的模型模式'
    return 对象模式({#操作
        'method':{'type':'string','const':方法},#方法
        'params':参数模式,#参数
    },['method','params'])#必填方法与参数

字符串模式={'type':'string'}#字符串
整数模式={'type':'integer'}#整数
数字模式={'type':'number'}#数字
布尔模式={'type':'boolean'}#布尔
修饰模式={'type':'array','items':{'type':'string','enum':list(修饰键表)}}#修饰键
按钮模式={'type':'string','enum':list(按钮表)}#按钮
应用模式=对象模式({'appHandle':字符串模式},['appHandle'])#句柄
窗口模式=对象模式({'appHandle':字符串模式,'windowId':整数模式},['appHandle','windowId'])#窗口
快照模式=对象模式({#快照
    'appHandle':字符串模式,#句柄
    'snapshotId':字符串模式,#快照
    'elementIndex':整数模式,#索引
},['appHandle','snapshotId','elementIndex'])#快照必填

def 坐标模式(相对,说明):
    '像素或千分比坐标模式'
    点=整数模式 if 相对 else 数字模式#千分比是整数
    属性={#坐标
        'appHandle':字符串模式,#句柄
        'windowId':整数模式,#窗口
        'snapshotId':字符串模式,#可选快照
        'x':点,#横坐标
        'y':点,#纵坐标
        'relative':{'type':'boolean','const':相对,'description':说明},#坐标模式
    }#属性结束
    必填=['appHandle','windowId','x','y']#必填
    if 相对:#千分比必须写出
        必填.append('relative')#必须为真
    return 对象模式(属性,必填)#坐标模式

像素说明='Omitted or false uses pixels in the latest screenshot returned by this tool.'#像素说明
千分说明='Use integer thousandths of the window width and height, from 0 to 1000.'#千分比说明

def 带指针(基础):
    '给目标模式加上可选指针字段'
    属性=dict(基础['properties'])#拷贝
    属性['mouseButton']=按钮模式#按钮
    属性['clickCount']={'type':'integer','enum':[1,2]}#次数
    属性['modifiers']=修饰模式#修饰键
    return 对象模式(属性,基础.get('required'))#指针模式

def 带滚动(基础):
    '给坐标模式加上行增量'
    属性=dict(基础['properties'])#拷贝
    属性['deltaLinesX']=整数模式#横向
    属性['deltaLinesY']=整数模式#纵向
    必填=list(基础.get('required') or [])+['deltaLinesX','deltaLinesY']#加上增量
    return 对象模式(属性,必填)#滚动模式

def 拖拽模式(相对,说明):
    '拖拽模式'
    点=整数模式 if 相对 else 数字模式#端点
    属性={#拖拽
        'appHandle':字符串模式,#句柄
        'windowId':整数模式,#窗口
        'snapshotId':字符串模式,#可选快照
        'relative':{'type':'boolean','const':相对,'description':说明},#坐标模式
        'mouseButton':按钮模式,#按钮
        'modifiers':修饰模式,#修饰键
        'fromX':点,'fromY':点,'toX':点,'toY':点,#端点
    }#属性结束
    必填=['appHandle','windowId','fromX','fromY','toX','toY']#必填
    if 相对:#千分比
        必填.append('relative')#必须写出
    return 对象模式(属性,必填)#拖拽模式

绝对坐标模式=坐标模式(False,像素说明)#像素
相对坐标模式=坐标模式(True,千分说明)#千分比
状态模式=对象模式({#状态
    'appHandle':字符串模式,#句柄
    'windowId':整数模式,#可选窗口
    'includeMenus':{'type':'boolean','description':'Expand menu contents; omitted or false shows menu-bar entries only.'},#菜单
    'details':{'type':'boolean','description':'Include identifiers, global-point bounds and complete action names.'},#细节
},['appHandle'])#状态模式
请求模式={#模型可见操作
    'oneOf':[#按方法分支
        操作模式('getCapabilities',对象模式({})),#能力
        操作模式('listApps',对象模式({})),#运行中的应用程序
        操作模式('findApps',对象模式({'query':{'type':'string','description':'Nonempty name, bundle identifier or absolute application path.'}},['query'])),#搜索
        操作模式('getApp',对象模式({'selector':字符串模式},['selector'])),#选择
        操作模式('activate',应用模式),#激活
        操作模式('show',对象模式({'appHandle':字符串模式,'windowId':整数模式},['appHandle'])),#显示
        操作模式('listWindows',应用模式),#窗口
        操作模式('getState',状态模式),#状态
        操作模式('hover',{'oneOf':[快照模式,绝对坐标模式,相对坐标模式]}),#悬停
        操作模式('click',{'oneOf':[带指针(快照模式),带指针(绝对坐标模式),带指针(相对坐标模式)]}),#点击
        操作模式('setValue',对象模式({'appHandle':字符串模式,'snapshotId':字符串模式,'elementIndex':整数模式,'value':字符串模式},['appHandle','snapshotId','elementIndex','value'])),#设值
        操作模式('selectText',对象模式({#选文本
            'appHandle':字符串模式,'snapshotId':字符串模式,'elementIndex':整数模式,'text':字符串模式,#目标
            'prefix':字符串模式,'suffix':字符串模式,#紧邻上下文
            'selectionType':{'type':'string','enum':list(选择种类表)},#放置
        },['appHandle','snapshotId','elementIndex','text'])),#选文本
        操作模式('performSecondaryAction',对象模式({'appHandle':字符串模式,'snapshotId':字符串模式,'elementIndex':整数模式,'action':字符串模式},['appHandle','snapshotId','elementIndex','action'])),#次要动作
        操作模式('typeText',对象模式({'appHandle':字符串模式,'text':字符串模式},['appHandle','text'])),#输入
        操作模式('paste',对象模式({'appHandle':字符串模式,'text':字符串模式,'format':{'type':'string','enum':list(粘贴格式表)}},['appHandle','text'])),#粘贴
        操作模式('pressKey',对象模式({'appHandle':字符串模式,'key':字符串模式,'modifiers':修饰模式},['appHandle','key'])),#按键
        操作模式('scroll',{'oneOf':[带滚动(绝对坐标模式),带滚动(相对坐标模式)]}),#滚动
        操作模式('drag',{'oneOf':[拖拽模式(False,像素说明),拖拽模式(True,千分说明)]}),#拖拽
        操作模式('screenshot',窗口模式),#截图
    ],#分支结束
}#请求模式结束
