'已确认的类型筛选会留下匹配嵌套行所需的祖先'

class 检查器类型筛选:
    '大小写不敏感的包含匹配。查询两侧的星号与不写星号相同'
    def __init__(自身,查询):
        '去掉两端空白和两端星号。中间的星号保留，大小写也保留'
        文本=查询.strip()#先去空白
        while 文本.startswith('*'):#去掉左侧星号
            文本=文本[1:]#削一个
        while 文本.endswith('*') and 文本!='':#去掉右侧星号
            文本=文本[:-1]#削一个
        自身.查询=文本.strip()#再去空白
        自身.针=自身.查询.lower()#比较用小写

    @property
    def 生效(自身):
        '空查询或只有星号时不限制表格'
        return 自身.针!=''#有片段才生效

    def 匹配(自身,类型):
        '未生效时任何类型都算匹配。类型还没有时不算'
        if not 自身.生效:#没有限制
            return True#全部通过
        if not isinstance(类型,str):#记录还没到
            return False#不能匹配
        return 自身.针 in 类型.lower()#包含即中

    def 套用(自身,行列表,类型于):
        '留下匹配行和它们的祖先。匹配到的后代即使父块原来合着也先打开'
        if not 自身.生效:#没有限制
            return {'rows':行列表,'matches':set(行['key'] for 行 in 行列表)}#原顺序全算匹配
        匹配键=set()#真正命中的行
        for 行 in 行列表:#先标命中
            if 自身.匹配(类型于(行['key'])):#当前类型命中
                匹配键.add(行['key'])#记下
        按键={}#键到行
        for 行 in 行列表:#建索引
            按键[行['key']]=行#覆盖同键
        保留=set(匹配键)#命中行和祖先
        for 键 in 匹配键:#沿父链补祖先
            行=按键.get(键)#当前行
            父=None if 行 is None else 行.get('parent')#父键
            while 父 is not None and 父 not in 保留:#祖先还没留下
                保留.add(父)#留下祖先
                父行=按键.get(父)#父行
                父=None if 父行 is None else 父行.get('parent')#再往上
        分支=set()#有留下子行的父
        for 键 in 保留:#谁有子行
            行=按键.get(键)#这一行
            父=None if 行 is None else 行.get('parent')#它的父
            if 父 is not None:#不是根
                分支.add(父)#父要打开
        结果=[]#过滤后的顺序
        for 行 in 行列表:#保持原顺序
            if 行['key'] not in 保留:#没留下
                continue#跳过
            纯={}#去掉原来的展开状态
            for 字段,内容 in 行.items():#逐字段
                if 字段!='disclosure':#展开状态单独决定
                    纯[字段]=内容#原样
            if 行['key'] in 分支:#下面有留下的行
                纯['disclosure']='open'#先打开，好看见匹配后代
            结果.append(纯)#按原顺序
        return {'rows':结果,'matches':匹配键}#祖先在，命中集合不含纯祖先

    def 建议(自身,行列表,类型于):
        '从全部已加载行取不重复的匹配类型，不看已经滤掉的子集'
        类型集=set()#去重
        for 行 in 行列表:#全部行，不是当前过滤结果
            类型=类型于(行['key'])#当前原始类型
            if isinstance(类型,str) and 自身.匹配(类型):#有类型且命中
                类型集.add(类型)#留下原文
        结果=list(类型集)#变成列表
        结果.sort()#确定顺序
        return 结果#同步返回，不再让出一次微任务
