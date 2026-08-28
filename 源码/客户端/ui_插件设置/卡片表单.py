"""每张插件卡片共用的表单模型。

对齐上游 `ui-settings-plugins/src/client/card-form.ts`。公开面仅中文名。
卡片暂存用户键入，仅在保存时写入。
"""
from ...依赖 import cordis#外部依赖胶水
是否thenable=cordis.工具.是否thenable#可等待判定

__all__=['快照仓库','数字字段','文本字段','卡片表单']#仅中文公开名

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待
    return 值#同步

class 快照仓库:#简易快照仓库
    """投影快照 + 订阅。"""
    def __init__(自身,初值):#播种
        """记下初值。"""
        自身.状态=dict(初值) if isinstance(初值,dict) else 初值#状态
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
        自身.状态=dict(下一份) if isinstance(下一份,dict) else 下一份#覆盖
        for 回调 in list(自身.监听者):#通知
            回调()#触发

def 数字字段(字段):#整数字段规格
    """空草稿清除；非有限数字挡住保存。"""
    def 格式化(值):#存储→草稿
        """有数字则十进制草稿。"""
        return str(值) if isinstance(值,(int,float)) and not isinstance(值,bool) else ''#草稿
    def 解析(文本):#草稿→写入
        """空则 clear；有限数字则 set。"""
        去空白=文本.strip()#去空白
        if 去空白=='':#空
            return {'kind':'clear'}#清除
        try:#解析
            解析值=float(去空白) if '.' in 去空白 else int(去空白)#数字
        except Exception:#非法
            return None#挡住
        if 解析值!=解析值 or 解析值 in (float('inf'),float('-inf')):#非有限
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
    """经快照仓库发布；作用域与本地草稿一起重建投影。"""
    def __init__(自身,作用域,规格表,密钥规格表=None):#绑定作用域与字段
        """建规格图并订阅作用域。"""
        自身.作用域=作用域#设置作用域
        自身.规格图={项['field']:项 for 项 in 规格表}#分区规格
        自身.密钥规格图={项['field']:项 for 项 in (密钥规格表 or [])}#只写规格
        自身.暂存={}#字段→暂存编辑
        自身.监听者=set()#投影监听
        自身.保存中=False#是否过线
        自身.失败=False#上次是否未落地
        作用域.subscribe(lambda:自身.发布())#作用域变化重发

    def bind(自身,投影):#把投影接到快照仓库
        """返回卡片组件读取的仓库。"""
        仓库=快照仓库(投影())#播种
        自身.监听者.add(lambda:仓库.set(投影()))#发布时覆盖
        return 仓库#仓库

    def shell(自身):#卡片级状态
        """宿主所服务的内容，以及保存将做什么。"""
        快照=自身.作用域.getSnapshot()#作用域快照
        计划=自身.计划()#写入计划
        return {#外壳
            'available':取字段(快照,'status')=='ready',#可用
            'writable':bool(取字段(快照,'writable')),#可写
            'dirty':len(计划)>0,#有暂存
            'invalid':any(项['run'] is None for 项 in 计划),#非法草稿
            'saving':自身.保存中,#保存中
            'failed':自身.失败,#失败
        }#外壳结束

    def field(自身,字段):#一个控件的渲染状态
        """草稿、覆盖与是否非法。"""
        暂=自身.暂存.get(字段)#暂存
        if 字段 in 自身.密钥规格图:#只写控件
            return {'text':取字段(暂,'text','') if 暂 else '','overridden':False,'invalid':False}#空白直至键入
        规格=自身.取规格(字段)#分区规格
        if 暂 is None:#无暂存
            return {'text':规格['format'](自身.分区值(字段)),'overridden':自身.已存(字段),'invalid':False}#有效值
        写入={'kind':'clear'} if 取字段(暂,'clear') else 规格['parse'](取字段(暂,'text',''))#解析
        return {#暂存作答
            'text':取字段(暂,'text',''),#草稿
            'overridden':取字段(写入,'kind')=='set' if 写入 else False,#保存后覆盖
            'invalid':写入 is None,#非法
        }#字段结束

    def actions(自身):#槽位注入的写入动作
        """编辑、重置、保存、丢弃。"""
        return {#动作
            'edit':lambda 字段,文本:自身.记下(字段,{'text':文本,'clear':False}),#暂存草稿
            'resetField':lambda 字段:自身.记下(字段,{'text':自身.取规格(字段)['format'](自身.合成值(字段)),'clear':True}),#暂存清除
            'save':lambda:自身.save(),#保存
            'discard':自身.丢弃,#丢弃
        }#动作结束

    def save(自身):#写入全部暂存
        """宿主是值是否被接受的唯一权威。"""
        计划=自身.计划()#计划
        可写=[项['run'] for 项 in 计划 if 项['run'] is not None]#可执行
        if len(计划)==0 or 自身.保存中 or len(可写)!=len(计划):#拒绝
            return#结束
        自身.保存中=True#过线
        自身.失败=False#清失败
        自身.发布()#投影
        落地=True#默认落地
        for 写 in 可写:#逐条
            结果=解开(写())#执行
            落地=bool(结果) and 落地#任一条未落地则失败
        if 落地:#全部落地
            自身.暂存.clear()#清暂存
        自身.保存中=False#结束
        自身.失败=not 落地#失败标记
        自身.发布()#重投影

    def 丢弃(自身):#丢弃全部暂存
        """无暂存且未失败则无需发布。"""
        if len(自身.暂存)==0 and not 自身.失败:#无需
            return#结束
        自身.暂存.clear()#清
        自身.失败=False#清失败
        自身.发布()#重发

    def 计划(自身):#保存将执行的写入计划
        """按暂存顺序。"""
        计划=[]#收集
        for 字段,暂 in list(自身.暂存.items()):#按暂存
            密钥=自身.密钥规格图.get(字段)#只写
            if 密钥 is not None:#只写控件
                值=取字段(暂,'text','').strip()#去空白
                if 值!='':#非空才写
                    计划.append({'field':字段,'run':lambda 文=值,写=密钥['write']:写(文)})#写入
                continue#下一字段
            规格=自身.取规格(字段)#分区规格
            if 取字段(暂,'clear'):#清除手势
                if 自身.已存(字段):#用户层有
                    计划.append({'field':字段,'run':lambda 某=字段:自身.清除(某)})#清除
                continue#下一字段
            if 取字段(暂,'text')==规格['format'](自身.分区值(字段)):#与有效值相同
                continue#无需写
            写入=规格['parse'](取字段(暂,'text',''))#解析
            if 写入 is None:#非法
                计划.append({'field':字段,'run':None})#挡住
            elif 取字段(写入,'kind')=='clear':#解析为清除
                计划.append({'field':字段,'run':lambda 某=字段:自身.清除(某)})#清除
            else:#写入值
                计划.append({'field':字段,'run':lambda 某=字段,值=取字段(写入,'value'):自身.存储(某,值)})#set
        return 计划#计划

    def 清除(自身,字段):#从用户层清除
        """unset 后回读。"""
        解开(自身.作用域.unset(字段))#请求清除
        return not 自身.已存(字段)#是否落地

    def 存储(自身,字段,值):#写入用户层
        """set 后回读。"""
        解开(自身.作用域.set(字段,值))#请求写入
        用户=自身.用户层()#用户层
        return 用户 is not None and 用户.get(字段)==值#是否落地

    def 记下(自身,字段,编辑):#记下暂存并清失败
        """覆盖该字段暂存。"""
        自身.暂存[字段]=编辑#暂存
        自身.失败=False#清失败
        自身.发布()#重发

    def 取规格(自身,字段):#按字段名取分区规格
        """缺规格则抛。"""
        规格=自身.规格图.get(字段)#规格
        if 规格 is None:#缺
            raise Exception(f'plugin card has no field {字段}')#接线错误
        return 规格#规格

    def 分区值(自身,字段):#分区有效值
        """用户层盖合成层。"""
        值=取字段(自身.作用域.getSnapshot(),'value')#有效层
        return 值.get(字段) if isinstance(值,dict) else None#字段

    def 合成值(自身,字段):#合成层该字段
        """base 层。"""
        值=取字段(自身.作用域.getSnapshot(),'base')#合成层
        return 值.get(字段) if isinstance(值,dict) else None#字段

    def 用户层(自身):#用户层对象
        """user 层。"""
        值=取字段(自身.作用域.getSnapshot(),'user')#用户层
        return 值 if isinstance(值,dict) else None#对象

    def 已存(自身,字段):#用户层是否携带
        """存在标记覆盖。"""
        用户=自身.用户层()#用户层
        return 用户 is not None and 字段 in 用户#自有键

    def 发布(自身):#通知全部投影监听
        """每个绑定仓库用新投影覆盖。"""
        for 回调 in list(自身.监听者):#通知
            回调()#触发
