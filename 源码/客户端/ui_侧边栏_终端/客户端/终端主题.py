import re

__all__=['终端主题']

ansi键=('black','red','green','yellow','blue','magenta','cyan','white','brightBlack','brightRed','brightGreen','brightYellow','brightBlue','brightMagenta','brightCyan','brightWhite')
特殊键=('foreground','background','cursor')
索引模式=re.compile(r'^[0-9]+\Z')
rgb模式=re.compile(r'^rgb:([0-9a-f]{1,4})/([0-9a-f]{1,4})/([0-9a-f]{1,4})\Z',re.I|re.ASCII)
井号模式=re.compile(r'^#(?:[0-9a-f]{3}){1,4}\Z',re.I|re.ASCII)

def 颜色索引(值):
    '0–255 的十进制索引，否则空'
    if 索引模式.match(值) is None:
        return None
    数字=int(值)
    if 数字<256:
        return 数字
    return None

def osc颜色(值):
    'XParseColor 与井号色收成六位井号。rgb: 各通道宽度必须相同，再缩放到 8 位'
    rgb=rgb模式.match(值)
    if rgb is not None:
        通道=list(rgb.groups())
        宽=len(通道[0])
        for 项 in 通道:
            if len(项)!=宽:
                return None
    else:
        if 井号模式.match(值) is None:
            return None
        宽=(len(值)-1)//3
        通道=[值[1:宽+1],值[宽+1:2*宽+1],值[2*宽+1:]]
    片段=[]
    for 项 in 通道:
        if rgb is None:
            数=int((项+'0')[:2],16)
        else:
            数=round(int(项,16)*255/(16**len(项)-1))
        片段.append(format(数,'02x'))
    return '#'+''.join(片段)

class 终端主题:
    '把程序色覆盖与 DSH 默认色分开'
    def __init__(自身,终端):
        '登记 OSC 4/104 与 10–12/110–112，处理器返回假表示不消费查询'
        自身.终端=终端
        自身.defaults={}
        自身.indexed={}
        自身.special={}
        自身.subscriptions=[]
        def 观察(码,变更):
            '处理 OSC 后交还 xterm'
            def 处理(数据):
                '调用变更并返回假，查询仍由 xterm 消费'
                变更(数据)
                return False
            return 终端.parser.registerOscHandler(码,处理)
        def 改索引(数据):
            '写入成对索引色'
            部分=数据.split(';')
            下标=0
            while 下标+1<len(部分):
                索引=颜色索引(部分[下标])
                颜色=osc颜色(部分[下标+1])
                if 索引 is not None and 颜色 is not None:
                    自身.indexed[索引]=颜色
                下标+=2
        def 重置索引(数据):
            '清空或删除指定索引后应用'
            if 数据=='':
                自身.indexed.clear()
            else:
                for 部分 in 数据.split(';'):
                    索引=颜色索引(部分)
                    if 索引 is not None and 索引 in 自身.indexed:
                        del 自身.indexed[索引]
            自身.应用()
        自身.subscriptions.append(观察(4,改索引))
        自身.subscriptions.append(观察(104,重置索引))
        偏移=0
        while 偏移<len(特殊键):
            键=特殊键[偏移]
            本偏移=偏移
            def 改特殊(数据,起点=本偏移):
                '按偏移写入特殊色'
                段表=数据.split(';')
                序号=0
                while 序号<len(段表):
                    目标下标=起点+序号
                    if 目标下标>=len(特殊键):
                        break
                    颜色=osc颜色(段表[序号])
                    if 颜色 is not None:
                        自身.special[特殊键[目标下标]]=颜色
                    序号+=1
            def 重置特殊(键名=键):
                '删除该特殊色后应用'
                if 键名 in 自身.special:
                    del 自身.special[键名]
                自身.应用()
            自身.subscriptions.append(观察(10+偏移,改特殊))
            自身.subscriptions.append(观察(110+偏移,重置特殊))
            偏移+=1

    def 更新(自身,背景,前景):
        '改 DSH 默认且不替换程序调色'
        if 自身.defaults.get('background')==背景 and 自身.defaults.get('foreground')==前景:
            return
        自身.defaults={
            'background':背景,
            'foreground':前景,
            'cursor':前景,
            'cursorAccent':背景,
            'selectionBackground':前景,
            'selectionForeground':背景,
            'selectionInactiveBackground':前景,
        }
        自身.应用()

    def 光标(自身):
        '含 OSC 12 覆盖的光标色'
        if 'cursor' in 自身.special:
            return 自身.special['cursor']
        return 自身.defaults['cursor']

    def 拆除(自身):
        '拆除 OSC 观察器'
        for 订阅 in 自身.subscriptions:
            订阅.dispose()

    def 应用(自身):
        '合并默认、特殊色与索引色。16 色以内写入 ANSI 名，其余写入 extendedAnsi'
        主题=dict(自身.defaults)
        主题.update(自身.special)
        for 索引,颜色 in 自身.indexed.items():
            if 索引<len(ansi键):
                主题[ansi键[索引]]=颜色
            else:
                扩展=主题['extendedAnsi'] if 'extendedAnsi' in 主题 else []
                需要=索引-len(ansi键)+1
                while len(扩展)<需要:
                    扩展.append(None)
                扩展[索引-len(ansi键)]=颜色
                主题['extendedAnsi']=扩展
        自身.终端.options.theme=主题
