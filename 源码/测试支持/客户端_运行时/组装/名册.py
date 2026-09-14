from ....客户端.web.平台 import 平台模块#壳播种的平台模块说明符

__all__=['客户端测试运行时错误','客户端名册行','客户端名册','组装计划','名册转启动图','断言计划']#仅中文公开名

本地修订='local'#盖在合成行与批次上的修订

class 客户端测试运行时错误(Exception):#本包组装失败
    """客户端测试运行时失败。"""

    def __init__(自身,消息,cause=None):#构造
        """记下英文消息并可选挂上原因。"""
        super().__init__(消息)#消息原样英文
        if cause is not None:#有原因
            自身.__cause__=cause#链式

class 客户端名册行:#名册一行
    """一行浏览器插件，按 dsh.client 声明、以包名为键。"""

    def __init__(自身,包名,注入,立即):#构造
        """记下包名、注入边与立即预取。"""
        自身.包名=包名#包名
        自身.注入=list(注入)#注入边
        自身.立即=立即#是否立即预取

def 名册转启动图(行表):#名册转启动图
    """为行表合成原始网页启动图：一个 application 批次装着全部行。"""
    入口列表=[]#图行
    for 行 in 行表:#逐行
        入口={'id':行.包名,'url':'/plugins/'+行.包名+'/client.js','rev':本地修订}#占位入口
        if len(行.注入)>0:#有注入才写键
            入口['inject']=list(行.注入)#注入边
        if 行.立即:#立即预取才写键
            入口['immediately']=True#标记
        入口列表.append(入口)#收下
    return {'rev':本地修订,'entries':入口列表,'batches':[{#单一应用批次
        'phase':'application',#应用阶段
        'url':'/plugins/local.js',#占位批次 URL
        'rev':本地修订,#批次修订
        'entries':[入口['id'] for 入口 in 入口列表],#行 id
    }]}#返回图

平台种子=set(平台模块)#平台种子

class 客户端名册:#客户端名册
    """不可变、按名寻址的名册。"""

    @staticmethod
    def 从行表(行表):#从行表建造
        """从行建造名册；重复名抛错。"""
        已见=set()#已见名
        重复=set()#重复名
        for 行 in 行表:#逐行
            if 行.包名 in 已见:#重复
                重复.add(行.包名)#记下
            已见.add(行.包名)#记下
        if len(重复)>0:#有重复
            raise 客户端测试运行时错误('client-test-runtime: duplicate roster rows: '+', '.join(重复))#英文诊断
        return 客户端名册(tuple(行表))#冻结行表

    def __init__(自身,行表):#私有构造经 从行表
        """记下冻结行表。"""
        自身.行表=行表#行表

    def 挑选(自身,包名表):#挑选
        """只保留包名表，保持名册顺序；未知名抛错并列出整份名册。"""
        保留=自身._已知(包名表,'pick')#校验并收成集合
        return 客户端名册(tuple(行 for 行 in 自身.行表 if 行.包名 in 保留))#过滤

    def 依赖闭包(自身,包名表):#依赖闭包
        """具名行加上它们注入的每一行（传递），按名册顺序。"""
        自身._已知(包名表,'closure')#校验起点
        按名={行.包名:行 for 行 in 自身.行表}#按名索引
        保留=set()#保留集
        def 访问(包名,来自):#访问
            """收下该包及其注入边。"""
            if 包名 in 保留 or 包名 in 平台种子:#已留或平台种子
                return#结束
            if 包名 not in 按名:#名册外
                raise 客户端测试运行时错误('client-test-runtime: '+str(来自)+' injects '+包名+', which is outside the roster')#英文诊断
            行=按名[包名]#取行
            保留.add(包名)#收下
            for 依赖 in 行.注入:#走依赖
                访问(依赖,包名)#递归
        for 包名 in 包名表:#从起点走
            访问(包名,None)#访问
        return 客户端名册(tuple(行 for 行 in 自身.行表 if 行.包名 in 保留))#按原序过滤

    def 去掉(自身,包名表):#去掉
        """丢掉包名表；未知名抛错并列出整份名册。"""
        丢弃=自身._已知(包名表,'without')#校验
        return 客户端名册(tuple(行 for 行 in 自身.行表 if 行.包名 not in 丢弃))#过滤

    def _已知(自身,包名表,操作):#已知名校验
        """未知名抛错并列出整份名册。"""
        名册名=[行.包名 for 行 in 自身.行表]#名册上的名
        未知=[名 for 名 in 包名表 if 名 not in 名册名]#未知
        if len(未知)>0:#有未知
            raise 客户端测试运行时错误('client-test-runtime: '+操作+'() names outside the roster: '+', '.join(未知)+'; roster: '+', '.join(名册名))#英文诊断
        return set(包名表)#收下

class 组装计划:#组装计划
    """启动什么、测试自己供给什么。"""

    def __init__(自身,名册,提供=None):#构造
        """记下名册与可选行替换。"""
        自身.名册=名册#名册
        自身.提供=提供#行替换

def 断言计划(计划):#断言计划
    """对照名册校验计划。"""
    名册名=[行.包名 for 行 in 计划.名册.行表]#名册上的名
    提供表=计划.提供 if 计划.提供 is not None else {}#行替换
    未知=[名 for 名 in 提供表 if 名 not in 名册名]#未知提供
    if len(未知)>0:#有未知
        raise 客户端测试运行时错误('client-test-runtime: provide names rows outside the roster: '+', '.join(未知)+'; roster: '+', '.join(名册名))#英文诊断
