"""无依赖源码工人闭包用的无损JSON快照与扁平线路编解码。"""
import math#有限数判定

def 追加(目标,值):#安全追加
    """追加元素。"""
    目标.append(值)#追加

def 弹出末项(目标):#安全弹出末项
    """弹出末项。"""
    if len(目标)==0:#空
        return None#无
    return 目标.pop()#弹出

def 快照代码json值(值):#脱离为无损JSON
    """校验并脱离一个工人边界值；无效则为None。迭代遍历不增加调用栈深度上限。"""
    活跃=set()#环检测：当前路径上的容器
    根=None#根快照槽
    def 赋值(目的地,项):#把项写入目的地
        nonlocal 根#闭合根
        if 目的地['kind']=='root':#根
            根=项#记下根
        elif 目的地['kind']=='array':#数组槽
            目的地['target'][目的地['index']]=项#按下标写入
        else:#对象属性
            目的地['target'][目的地['key']]=项#按键写入
    任务们=[{'kind':'visit','value':值,'destination':{'kind':'root'}}]#从根访问开始
    while len(任务们)>0:#栈式迭代
        任务=弹出末项(任务们)#弹出
        if 任务['kind']=='leave':#离开容器
            活跃.discard(任务['source'])#解除环检测
            continue#下一任务
        if 任务['kind']=='array-item':#排队的数组元素
            追加(任务们,{'kind':'visit','value':任务['source'][任务['index']],'destination':{'kind':'array','target':任务['target'],'index':任务['index']}})#改成visit
            continue#下一任务
        if 任务['kind']=='object-property':#排队的对象属性
            追加(任务们,{'kind':'visit','value':任务['source'][任务['key']],'destination':{'kind':'object','target':任务['target'],'key':任务['key']}})#改成visit
            continue#下一任务
        候选=任务['value']#当前候选
        if 候选 is None:#null合法
            赋值(任务['destination'],None)#写入null
            continue#下一任务
        if isinstance(候选,bool) or isinstance(候选,str):#布尔或字符串
            赋值(任务['destination'],候选)#原样写入
            continue#下一任务
        if isinstance(候选,(int,float)) and not isinstance(候选,bool):#数字（排除bool）
            if isinstance(候选,float) and (math.isnan(候选) or math.isinf(候选)):#NaN/Inf非法
                return None#无效
            if isinstance(候选,float) and 候选==0.0 and math.copysign(1.0,候选)<0:#-0非法
                return None#无效
            赋值(任务['destination'],候选)#写入有限数字
            continue#下一任务
        if not isinstance(候选,(list,dict)):#非容器
            return None#函数等非法
        身份=id(候选)#容器身份
        if 身份 in 活跃:#环非法
            return None#无效
        if isinstance(候选,list):#数组
            目标=[None]*len(候选)#脱离后的数组占位
            赋值(任务['destination'],目标)#先挂上空数组
            活跃.add(身份)#进入环检测
            追加(任务们,{'kind':'leave','source':身份})#退出时解除
            for 下标 in range(len(候选)-1,-1,-1):#逆序入栈以正序写出
                追加(任务们,{'kind':'array-item','source':候选,'index':下标,'target':目标})#排队元素
            continue#下一任务
        键们=list(候选.keys())#JSON可见键
        for 键 in 键们:#逐键检查
            if not isinstance(键,str):#非字符串键
                return None#无效
        目标={}#脱离后的对象
        赋值(任务['destination'],目标)#先挂上空对象
        活跃.add(身份)#进入环检测
        追加(任务们,{'kind':'leave','source':身份})#退出时解除
        for 下标 in range(len(键们)-1,-1,-1):#逆序入栈
            键=键们[下标]#当前键
            追加(任务们,{'kind':'object-property','source':候选,'key':键,'target':目标})#排队属性
    return 根#返回根快照

def 编码工人json(值):#编码为扁平线路
    """把已校验的JSON值压平，供工人线程消息端口传输。"""
    线路=[]#输出token
    待办=[值]#待编码栈
    while len(待办)>0:#栈式迭代
        当前=弹出末项(待办)#弹出
        if 当前 is None or isinstance(当前,bool) or isinstance(当前,(int,float)) or isinstance(当前,str):#标量叶子
            if isinstance(当前,float) and (math.isnan(当前) or math.isinf(当前)):#非法数
                raise ValueError('cannot encode non-finite JSON number')#拒绝
            追加(线路,当前)#直接写入
            continue#下一值
        if isinstance(当前,list):#数组
            追加(线路,{'kind':'array','length':len(当前)})#先写容器标记
            for 下标 in range(len(当前)-1,-1,-1):#逆序入栈
                追加(待办,当前[下标])#排队元素
            continue#下一值
        if isinstance(当前,dict):#对象
            键们=list(当前.keys())#可枚举字符串键
            追加(线路,{'kind':'object','keys':键们})#先写容器标记
            for 下标 in range(len(键们)-1,-1,-1):#逆序入栈
                键=键们[下标]#当前键
                追加(待办,当前[键])#排队属性值
            continue#下一值
        raise ValueError('cannot encode non-JSON value')#非法
    return 线路#返回扁平流

def 解码工人json(输入):#解码扁平线路
    """从扁平工人线程线路格式重建一个无损JSON值；畸形或不完整返回None。"""
    try:#任何抛错都视为无效线路
        if not isinstance(输入,list) or len(输入)==0:#必须是非空列表
            return None#无效
        帧们=[]#打开的容器栈
        根=None#根值槽
        根已写=False#根是否已写入
        def 挂上(值):#把值挂到当前帧或根
            nonlocal 根,根已写#闭合
            if len(帧们)==0:#无打开容器
                if 根已写:#根只能写一次
                    return False#失败
                根=值#写入根
                根已写=True#标记
                return True#成功
            父=帧们[-1]#栈顶帧
            if 父['kind']=='array':#数组帧
                if 父['index']>=父['length']:#帧已满
                    return False#失败
                父['target'].append(值)#追加元素
            else:#对象帧
                if 父['index']>=len(父['keys']):#帧已满
                    return False#失败
                键=父['keys'][父['index']]#当前键
                父['target'][键]=值#按键写入
            父['index']+=1#推进已填槽
            return True#成功
        for 记号 in 输入:#逐token
            值=None#本token对应的值
            帧=None#若是非空容器则新开帧
            if 记号 is None or isinstance(记号,bool) or isinstance(记号,str):#简单标量
                值=记号#原样
            elif isinstance(记号,(int,float)) and not isinstance(记号,bool):#数字
                if isinstance(记号,float) and (math.isnan(记号) or math.isinf(记号)):#非法
                    return None#无效
                if isinstance(记号,float) and 记号==0.0 and math.copysign(1.0,记号)<0:#-0
                    return None#无效
                值=记号#有限数字
            elif isinstance(记号,dict):#容器标记
                种类=记号.get('kind')#标记类别
                if 种类=='array':#数组容器
                    长度=记号.get('length')#长度字段
                    if not isinstance(长度,int) or 长度<0:#非法长度
                        return None#无效
                    目标=[]#新数组
                    值=目标#本token的值是空数组
                    if 长度>0:#非空则开帧
                        帧={'kind':'array','target':目标,'length':长度,'index':0}#数组帧
                elif 种类=='object':#对象容器
                    对象键=记号.get('keys')#键列表
                    if not isinstance(对象键,list):#必须是列表
                        return None#无效
                    去重=set()#去重
                    规范键=[]#规范化键
                    for 键 in 对象键:#逐键
                        if not isinstance(键,str) or 键 in 去重:#非字符串或重复
                            return None#无效
                        去重.add(键)#记入
                        规范键.append(键)#追加
                    目标={}#新对象
                    值=目标#本token的值是空对象
                    if len(规范键)>0:#非空则开帧
                        帧={'kind':'object','target':目标,'keys':规范键,'index':0}#对象帧
                else:#未知kind
                    return None#无效
            else:#非法token
                return None#无效
            if not 挂上(值):#挂不上
                return None#无效
            if 帧 is not None:#非空容器
                帧们.append(帧)#压栈
            while len(帧们)>0:#弹出已填满的帧
                当前=帧们[-1]#栈顶
                上限=当前['length'] if 当前['kind']=='array' else len(当前['keys'])#容量
                if 当前['index']<上限:#尚未填满
                    break#停弹
                帧们.pop()#弹出完成帧
        return 根 if len(帧们)==0 else None#还有打开帧则不完整
    except Exception:#任何抛错
        return None#视为无效线路
