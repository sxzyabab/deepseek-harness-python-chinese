"""`@deepseek-ai/dsh-commands` 的包内不变量配套：命令生命周期事件在同一会话日志内按 commandId 配对。"""
包名='@deepseek-ai/dsh-commands'#本包名，用于登记所有权
名称='commands-invariant'#配套插件名
注入=['invariants']#依赖不变量服务

def 安装(上下文对象,失败):#安装配对校验
    """对已加载日志和新追加的生命周期事件安装配对校验。"""
    运行标识表={}#每会话已见的 run id；按会话身份弱关联用 id(session)
    def 校验事件(会话,事件):#校验单条生命周期事件
        """校验单条 command/run 或 command/done。事件是 dict。"""
        类型=事件['type']#事件类型
        数据=事件['data'] if 'data' in 事件 else None#事件载荷
        if 类型=='command/run':#开始事件
            会话键=id(会话)#会话身份
            if 会话键 not in 运行标识表:#尚未有
                运行标识表[会话键]=set()#新建
            标识集=运行标识表[会话键]#取出本会话集合
            配对=数据['commandId']#本次配对 id
            if 配对 in 标识集:#同一 id 重复 run
                失败('command/run repeats commandId '+repr(配对))#报告重复 run
            标识集.add(配对)#记下本次 run
            return#run 处理完毕
        if 类型!='command/done':#非 done 则忽略
            return#忽略
        配对=数据['commandId']#配对 id
        会话键=id(会话)#会话身份
        标识集=运行标识表[会话键] if 会话键 in 运行标识表 else None#本会话已见 run
        if 标识集 is None or 配对 not in 标识集:#没有先出现的 run
            失败('command/done '+repr(配对)+' pairs no prior command/run in this log')#报告孤立 done
            return#已失败
        源序号=数据['sourceEventSeq'] if 'sourceEventSeq' in 数据 else None#可选权威事件序号
        if 源序号 is None:#没有源序号
            return#合法
        事件列表=会话.events#会话日志
        if 事件列表 is None:#无日志
            源事件=None#无
        elif 源序号<0 or 源序号>=len(事件列表):#越界
            源事件=None#无
        else:#按序号取
            源事件=事件列表[源序号]#源事件
        种类=数据['kind']#结算种类
        事件序号=事件['seq']#本事件序号
        源事件序号=源事件['seq'] if 源事件 is not None else None#源事件自报序号
        源类型=源事件['type'] if 源事件 is not None else None#源事件类型
        if (种类!='success'#必须是成功
            or isinstance(源序号,bool) or not isinstance(源序号,int) or 源序号<0#必须非负整数
            or 源序号>=事件序号#必须早于本事件
            or 源事件序号!=源序号#日志位必须对上
            or 源类型=='command/run'#不得指向命令生命周期
            or 源类型=='command/done'):#不得指向命令生命周期
            失败('command/done '+repr(配对)+' has invalid sourceEventSeq '+str(源序号))#报告非法源序号
    for 会话 in 上下文对象.sessions.列出():#扫描已加载会话
        for 事件 in 会话.events:#回放历史事件
            校验事件(会话,事件)#校验
    def 内部派发(_模式,事件名,参数,*位置参数):#拦截新追加的会话事件
        """提交前/派发时校验 session/event。"""
        if 事件名!='session/event':#只关心会话事件
            return#放过
        会话=参数[0]#拆出会话
        事件=参数[1]#拆出事件
        校验事件(会话,事件)#校验新事件
    上下文对象.监听('internal/dispatch',内部派发,{'全局':True})#全局监听

安装.inject=['sessions']#安装器还依赖 sessions

def 应用(上下文对象):#对外导出配套入口
    """登记本包的不变量配套，返回安装成功后已登记项的拆除器。"""
    return 上下文对象.invariants.register(包名,安装)#向不变量服务登记安装器

__all__=['包名','名称','注入','安装','应用']#仅中文公开名
name=名称#Cordis插件名
inject=注入#Cordis依赖声明
apply=应用#Cordis插件入口
default=应用#Cordis默认导出
