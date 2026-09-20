__all__=['插件设置错误','快照存储','数字字段','文本字段','卡片表单']#仅中文公开名

class 插件设置错误(Exception):
    """本包异常基类。"""
    def __init__(自身,消息):
        """记下英文消息。"""
        super().__init__(消息)#消息原样英文

class 快照存储:#简易快照存储
    """投影快照 + 订阅。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=dict(初值)#状态
        自身.监听者=set()#订阅者

    def getSnapshot(自身):#读快照
        """返回当前状态。"""
        return 自身.状态#状态

    def subscribe(自身,回调):#订阅
        """登记变更回调。"""
        自身.监听者.add(回调)#加入
        def 退订():#退订
            """取消。"""
            自身.监听者.discard(回调)#删除
        return 退订#退订器

    def set(自身,下一份):#整体替换
        """用新投影覆盖。"""
        自身.状态=dict(下一份)#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

def 数字字段(字段):#整数字段规格
    """空草稿清除；非整数挡住保存。"""
    def 格式化(值):#存储→草稿
        """有数字则十进制草稿。"""
        return str(值) if isinstance(值,int) and not isinstance(值,bool) else ''#草稿
    def 解析(文本):#草稿→写入
        """空则 clear；整数则 set。"""
        去空白=文本.strip()#去空白
        if 去空白=='':#空
            return {'kind':'clear'}#清除
        try:#解析整数
            解析值=int(去空白,10)#十进制
        except (ValueError,OverflowError):#非法
            return None#挡住
        return {'kind':'set','value':解析值}#写入
    return {'field':字段,'format':格式化,'parse':解析}#规格

def 文本字段(字段):#自由文本字段规格
    """空草稿清除。"""
    def 格式化(值):#存储→草稿
        """有字符串则原样。"""
        return 值 if isinstance(值,str) else ''#草稿
    def 解析(文本):#草稿→写入
        """空则 clear。"""
        去空白=文本.strip()#去空白
        return {'kind':'clear'} if 去空白=='' else {'kind':'set','value':去空白}#写入
    return {'field':字段,'format':格式化,'parse':解析}#规格

class 卡片表单:#一张卡片在一个命名空间上的暂存表单
    """经快照存储发布；作用域与本地草稿一起重建投影。"""
    def __init__(自身,作用域,规格表,密钥规格表=None):#绑定作用域与字段
        """建规格图并订阅作用域。"""
        自身.作用域=作用域#设置作用域
        自身.规格图={项['field']:项 for 项 in 规格表}#分区规格
        密钥表=密钥规格表 if 密钥规格表 is not None else []#只写规格
        自身.密钥规格图={项['field']:项 for 项 in 密钥表}#只写规格
        自身.暂存={}#字段→暂存编辑
        自身.监听者=set()#投影监听
        自身.保存中=False#是否过线
        自身.失败=False#上次是否未落地
        def 作用域变了():#作用域变化
            """重发投影。"""
            自身.发布()#重发
        作用域.subscribe(作用域变了)#作用域变化重发

    def bind(自身,投影):#把投影接到快照存储
        """返回卡片组件读取的仓库。"""
        仓库=快照存储(投影())#播种
        def 覆盖():#发布时覆盖
            """用新投影覆盖仓库。"""
            仓库.set(投影())#覆盖
        自身.监听者.add(覆盖)#登记
        return 仓库#仓库

    def shell(自身):#卡片级状态
        """宿主所服务的内容，以及保存将做什么。"""
        快照=自身.作用域.getSnapshot()#作用域快照
        计划=自身.计划()#写入计划
        态名=快照['status'] if 'status' in 快照 else None#状态
        可写=bool(快照['writable']) if 'writable' in 快照 else False#可写
        return {#外壳
            'available':态名=='ready',#可用
            'writable':可写,#可写
            'dirty':len(计划)>0,#有暂存
            'invalid':any(项['run'] is None for 项 in 计划),#非法草稿
            'saving':自身.保存中,#保存中
            'failed':自身.失败,#失败
        }#外壳结束

    def field(自身,字段):#一个控件的渲染状态
        """草稿、覆盖与是否非法。"""
        暂=自身.暂存[字段] if 字段 in 自身.暂存 else None#暂存
        if 字段 in 自身.密钥规格图:#只写控件
            文=暂['text'] if 暂 is not None and 'text' in 暂 else ''#草稿
            return {'text':文,'overridden':False,'invalid':False}#空白直至键入
        规格=自身.取规格(字段)#分区规格
        if 暂 is None:#无暂存
            return {'text':规格['format'](自身.分区值(字段)),'overridden':自身.已存(字段),'invalid':False}#有效值
        文=暂['text'] if 'text' in 暂 else ''#草稿
        清除='clear' in 暂 and 暂['clear']#清除手势
        写入={'kind':'clear'} if 清除 else 规格['parse'](文)#解析
        覆盖=写入 is not None and 'kind' in 写入 and 写入['kind']=='set'#保存后覆盖
        return {#暂存作答
            'text':文,#草稿
            'overridden':覆盖,#保存后覆盖
            'invalid':写入 is None,#非法
        }#字段结束

    def actions(自身):#槽位注入的写入动作
        """编辑、重置、保存、丢弃。"""
        def 编辑字段(字段,文本):#暂存草稿
            """记下键入。"""
            自身.记下(字段,{'text':文本,'clear':False})#暂存
        def 复位字段(字段):#暂存清除
            """记下清除手势。"""
            自身.记下(字段,{'text':自身.取规格(字段)['format'](自身.合成值(字段)),'clear':True})#暂存清除
        def 点保存():#保存
            """写入全部暂存。"""
            自身.保存()#保存
        return {#动作
            'edit':编辑字段,#暂存草稿
            'resetField':复位字段,#暂存清除
            'save':点保存,#保存
            'discard':自身.丢弃,#丢弃
        }#动作结束

    def 保存(自身):#写入全部暂存
        """宿主是值是否被接受的唯一权威。"""
        计划=自身.计划()#计划
        可写=[项['run'] for 项 in 计划 if 项['run'] is not None]#可执行
        if len(计划)==0 or 自身.保存中 or len(可写)!=len(计划):#拒绝
            return
        自身.保存中=True#过线
        自身.失败=False#清失败
        自身.发布()#投影
        落地=True#默认落地
        for 写 in 可写:#逐条
            结果=写()#执行
            落地=bool(结果) and 落地#任一条未落地则失败
        if 落地:#全部落地
            自身.暂存.clear()#清暂存
        自身.保存中=False
        自身.失败=not 落地#失败标记
        自身.发布()#重投影

    def 丢弃(自身):#丢弃全部暂存
        """无暂存且未失败则无需发布。"""
        if len(自身.暂存)==0 and not 自身.失败:
            return
        自身.暂存.clear()
        自身.失败=False#清失败
        自身.发布()#重发

    def 计划(自身):#保存将执行的写入计划
        """按暂存顺序。"""
        计划=[]#收集
        for 字段,暂 in list(自身.暂存.items()):#按暂存
            密钥=自身.密钥规格图[字段] if 字段 in 自身.密钥规格图 else None#只写
            if 密钥 is not None:#只写控件
                文=暂['text'] if 'text' in 暂 else ''#草稿
                值=文.strip()#去空白
                if 值!='':#非空才写
                    def 写密钥(文=值,写=密钥['write']):#写入密钥
                        """调用只写规格。"""
                        return 写(文)#写入
                    计划.append({'field':字段,'run':写密钥})#写入
                continue#下一字段
            规格=自身.取规格(字段)#分区规格
            清除='clear' in 暂 and 暂['clear']#清除手势
            if 清除:#清除手势
                if 自身.已存(字段):#用户层有
                    def 执行清除(某=字段):#清除
                        """从用户层清除。"""
                        return 自身.清除(某)#清除
                    计划.append({'field':字段,'run':执行清除})#清除
                continue#下一字段
            文=暂['text'] if 'text' in 暂 else None#草稿
            if 文==规格['format'](自身.分区值(字段)):#与有效值相同
                continue#无需写
            写入=规格['parse'](文 if 文 is not None else '')#解析
            if 写入 is None:#非法
                计划.append({'field':字段,'run':None})#挡住
            elif 'kind' in 写入 and 写入['kind']=='clear':#解析为清除
                def 执行解析清除(某=字段):#清除
                    """从用户层清除。"""
                    return 自身.清除(某)#清除
                计划.append({'field':字段,'run':执行解析清除})#清除
            else:#写入值
                写入值=写入['value'] if 'value' in 写入 else None#值
                def 执行存储(某=字段,值=写入值):#写入
                    """写入用户层。"""
                    return 自身.存储(某,值)#set
                计划.append({'field':字段,'run':执行存储})#set
        return 计划#计划

    def 清除(自身,字段):#从用户层清除
        """unset 后回读。"""
        自身.作用域.unset(字段)#请求清除
        return not 自身.已存(字段)#是否落地

    def 存储(自身,字段,值):#写入用户层
        """set 后回读。"""
        自身.作用域.set(字段,值)#请求写入
        用户=自身.用户层()#用户层
        return 用户 is not None and 字段 in 用户 and 用户[字段]==值#是否落地

    def 记下(自身,字段,编辑):#记下暂存并清失败
        """覆盖该字段暂存。"""
        自身.暂存[字段]=编辑#暂存
        自身.失败=False#清失败
        自身.发布()#重发

    def 取规格(自身,字段):#按字段名取分区规格
        """缺规格则抛。"""
        if 字段 not in 自身.规格图:#缺
            raise 插件设置错误(f'plugin card has no field {字段}')#接线错误
        return 自身.规格图[字段]#规格

    def 分区值(自身,字段):#分区有效值
        """用户层盖合成层。"""
        快照=自身.作用域.getSnapshot()#快照
        值=快照['value'] if 'value' in 快照 else None#有效层
        if 值 is None or 字段 not in 值:#无层或无键
            return None#无
        return 值[字段]#字段

    def 合成值(自身,字段):#合成层该字段
        """base 层。"""
        快照=自身.作用域.getSnapshot()#快照
        值=快照['base'] if 'base' in 快照 else None#合成层
        if 值 is None or 字段 not in 值:#无层或无键
            return None#无
        return 值[字段]#字段

    def 用户层(自身):#用户层对象
        """user 层。"""
        快照=自身.作用域.getSnapshot()#快照
        return 快照['user'] if 'user' in 快照 else None#用户层；缺键与显式 null 皆 None

    def 已存(自身,字段):#用户层是否携带
        """存在标记覆盖。"""
        用户=自身.用户层()#用户层
        return 用户 is not None and 字段 in 用户#自有键

    def 发布(自身):#通知全部投影监听
        """每个绑定仓库用新投影覆盖。"""
        for 回调 in list(自身.监听者):#通知
            回调()#触发
