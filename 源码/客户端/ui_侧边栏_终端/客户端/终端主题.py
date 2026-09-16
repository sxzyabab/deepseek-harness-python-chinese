import re#OSC 颜色解析
__all__=['终端主题']#仅中文公开名

ansi键=('black','red','green','yellow','blue','magenta','cyan','white','brightBlack','brightRed','brightGreen','brightYellow','brightBlue','brightMagenta','brightCyan','brightWhite')#ANSI 调色键
特殊键=('foreground','background','cursor')#OSC 特殊色键
索引模式=re.compile(r'^[0-9]+\Z')#纯数字索引
rgb模式=re.compile(r'^rgb:([0-9a-f]{1,4})/([0-9a-f]{1,4})/([0-9a-f]{1,4})\Z',re.I|re.ASCII)#rgb: 通道
井号模式=re.compile(r'^#(?:[0-9a-f]{3}){1,4}\Z',re.I|re.ASCII)#CSS 井号色

def 颜色索引(值):#解析 OSC 4 索引
    """0–255 的十进制索引，否则空。"""
    if 索引模式.match(值) is None:#非数字
        return None#空
    数字=int(值)#索引
    if 数字<256:#范围内
        return 数字#索引
    return None#超界

def osc颜色(值):#规范化 OSC 颜色
    """XParseColor 与井号色收成六位井号。"""
    rgb=rgb模式.match(值)#rgb: 匹配
    if rgb is not None:#rgb: 通道
        通道=list(rgb.groups())#三通道
        宽=len(通道[0])#第一通道宽
        for 项 in 通道:#各通道
            if len(项)!=宽:#宽度不一致
                return None#拒绝
    else:#井号
        if 井号模式.match(值) is None:#非法
            return None#拒绝
        宽=(len(值)-1)//3#每通道宽
        通道=[值[1:宽+1],值[宽+1:2*宽+1],值[2*宽+1:]]#切开
    片段=[]#两位十六进制
    for 项 in 通道:#每通道
        if rgb is None:#井号截断
            数=int((项+'0')[:2],16)#前两字符
        else:#按宽度缩放
            数=round(int(项,16)*255/(16**len(项)-1))#缩放到 8 位
        片段.append(format(数,'02x'))#两位
    return '#'+''.join(片段)#六位井号

class 终端主题:#DSH 默认色与 OSC 覆盖
    """把程序色覆盖与 DSH 默认色分开。"""
    def __init__(自身,终端):#观察 OSC
        """登记 OSC 处理器且不消费查询。"""
        自身.终端=终端#仿真器
        自身.defaults={}#DSH 默认
        自身.indexed={}#索引色
        自身.special={}#特殊色
        自身.subscriptions=[]#拆除器
        def 观察(码,变更):#登记 OSC
            """处理 OSC 后交还 xterm。"""
            def 处理(数据):#解析数据
                """调用变更并返回假。"""
                变更(数据)#写入覆盖
                return False#不消费
            return 终端.parser.registerOscHandler(码,处理)#登记
        def 改索引(数据):#OSC 4
            """写入成对索引色。"""
            部分=数据.split(';')#分段
            下标=0#游标
            while 下标+1<len(部分):#成对
                索引=颜色索引(部分[下标])#索引
                颜色=osc颜色(部分[下标+1])#颜色
                if 索引 is not None and 颜色 is not None:#有效
                    自身.indexed[索引]=颜色#写入
                下标+=2#下一对
        def 重置索引(数据):#OSC 104
            """清空或删除指定索引后应用。"""
            if 数据=='':#全清
                自身.indexed.clear()#清空
            else:#指定
                for 部分 in 数据.split(';'):#逐段
                    索引=颜色索引(部分)#索引
                    if 索引 is not None and 索引 in 自身.indexed:#存在
                        del 自身.indexed[索引]#删除
            自身.应用()#写回
        自身.subscriptions.append(观察(4,改索引))#OSC 4
        自身.subscriptions.append(观察(104,重置索引))#OSC 104
        偏移=0#特殊色偏移
        while 偏移<len(特殊键):#10/110 系列
            键=特殊键[偏移]#本键
            本偏移=偏移#闭包偏移
            def 改特殊(数据,起点=本偏移):#OSC 10+
                """按偏移写入特殊色。"""
                段表=数据.split(';')#分段
                序号=0#段序号
                while 序号<len(段表):#逐段
                    目标下标=起点+序号#目标键下标
                    if 目标下标>=len(特殊键):#越界
                        break#停
                    颜色=osc颜色(段表[序号])#颜色
                    if 颜色 is not None:#有效
                        自身.special[特殊键[目标下标]]=颜色#写入
                    序号+=1#下一段
            def 重置特殊(键名=键):#OSC 110+
                """删除该特殊色后应用。"""
                if 键名 in 自身.special:#有覆盖
                    del 自身.special[键名]#删除
                自身.应用()#写回
            自身.subscriptions.append(观察(10+偏移,改特殊))#OSC 10+
            自身.subscriptions.append(观察(110+偏移,重置特殊))#OSC 110+
            偏移+=1#下一特殊键

    def 更新(自身,背景,前景):#应用 DSH 色
        """改 DSH 默认且不替换程序调色。"""
        if 自身.defaults.get('background')==背景 and 自身.defaults.get('foreground')==前景:#未变
            return#跳过
        自身.defaults={#默认主题
            'background':背景,#背景
            'foreground':前景,#前景
            'cursor':前景,#光标
            'cursorAccent':背景,#光标衬
            'selectionBackground':前景,#选区底
            'selectionForeground':背景,#选区字
            'selectionInactiveBackground':前景,#非活动选区
        }#默认结束
        自身.应用()#写回

    def 光标(自身):#优先光标色
        """含 OSC 12 覆盖的光标色。"""
        if 'cursor' in 自身.special:#有覆盖
            return 自身.special['cursor']#覆盖
        return 自身.defaults['cursor']#默认

    def 拆除(自身):#卸观察
        """拆除 OSC 观察器。"""
        for 订阅 in 自身.subscriptions:#逐个
            订阅.dispose()#拆除

    def 应用(自身):#写 xterm.theme
        """合并默认、特殊色与索引色。"""
        主题=dict(自身.defaults)#拷默认
        主题.update(自身.special)#特殊色覆盖
        for 索引,颜色 in 自身.indexed.items():#索引色
            if 索引<len(ansi键):#标准 ANSI
                主题[ansi键[索引]]=颜色#写入
            else:#扩展
                扩展=主题['extendedAnsi'] if 'extendedAnsi' in 主题 else []#列表
                需要=索引-len(ansi键)+1#长度
                while len(扩展)<需要:#补位
                    扩展.append(None)#占位
                扩展[索引-len(ansi键)]=颜色#写入
                主题['extendedAnsi']=扩展#挂回
        自身.终端.options.theme=主题#写仿真器
