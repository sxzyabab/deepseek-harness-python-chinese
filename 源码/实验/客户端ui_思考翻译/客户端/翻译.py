'一段展开思考的顺序段落翻译'
import re
from ....基础设施.js特性 import PromiseEX as 期约#片段翻译的异步结果
from ...机器翻译.类型 import 中止控制器,已中止,码元数

__all__=['思考片段','思考翻译']

def 码元切片(文本,起,止=None):
    '按 UTF-16 码元切片'
    原始=文本.encode('utf-16-le')
    if 止 is None:
        止=len(原始)//2
    return 原始[起*2:止*2].decode('utf-16-le')

def 思考片段(文本,进行中,最大字符):
    '把思考拆成已完成段落和请求长度内的片段，空白原样保留'
    结果=[]
    分隔=re.compile(r'\r?\n(?:[\t ]*\r?\n)+')
    起点=0
    总长=码元数(文本)
    while True:
        余下全文=码元切片(文本,起点)
        匹配=分隔.search(余下全文)
        if 匹配 is None:
            段尾=总长
            段落后缀=''
            命中=False
        else:
            段尾=起点+码元数(余下全文[:匹配.start()])
            段落后缀=匹配.group(0)
            命中=True
        剩余=码元切片(文本,起点,段尾)
        while 码元数(剩余)>最大字符:
            切=最大字符
            if 切>0:
                单元原始=剩余.encode('utf-16-le')
                单元=int.from_bytes(单元原始[(切-1)*2:(切-1)*2+2],'little')
                if 0xD800<=单元<=0xDBFF:
                    切-=1
            前=码元切片(剩余,0,切)
            空白=re.search(r'\s+\S*$',前)
            if 空白 is not None and 空白.start()>0:
                切=码元数(前[:空白.start()])
            来源=码元切片(剩余,0,切)
            剩余=码元切片(剩余,切)
            空白前缀=re.match(r'^\s+',剩余)
            后缀段='' if 空白前缀 is None else 空白前缀.group(0)
            if 后缀段!='':
                剩余=剩余[len(后缀段):]
            结果.append({'text':来源,'suffix':后缀段,'complete':True})
        结果.append({
            'text':剩余,
            'suffix':段落后缀,
            'complete':命中 or not 进行中,
        })
        if not 命中:
            return 结果
        起点=段尾+码元数(段落后缀)

class 思考翻译:
    '一个展开区的取消、请求顺序和过期结果'
    def __init__(自身,选择,最大字符,翻译,发布):
        '记下提供方、语言、上限和发布回调'
        自身.选择=选择
        自身.最大字符=最大字符
        自身.翻译=翻译
        自身.发布=发布
        自身.控制器=中止控制器()
        自身.缓存={}
        自身.片段表=[]
        自身.待定=False
        自身.失败=False

    def 更新(自身,文本,进行中):
        '采用当前原文，并排上新完成的片段'
        自身.片段表=思考片段(文本,进行中,自身.最大字符)
        自身.发出()
        自身.跑()

    def 重试(自身):
        '失败后重试尚未翻译的片段'
        自身.失败=False
        自身.跑()

    def 拆除(自身):
        '中止本展开区的请求，之后不再发布'
        自身.控制器.中止()

    def 已拆除(自身):
        '控制器已中止'
        return 已中止(自身.控制器.信号)

    def 下一段(自身):
        '下一个已完成、非空白、尚未缓存的片段'
        for 片段 in 自身.片段表:
            if 片段['complete'] and 片段['text'].strip()!='' and 片段['text'] not in 自身.缓存:
                return 片段
        return None

    def 发出(自身):
        '已完成片段用缓存译文，未完成片段保留原文'
        if 自身.已拆除():
            return
        段=[]
        for 片段 in 自身.片段表:
            if 片段['complete']:
                内容=自身.缓存.get(片段['text'],片段['text'])
            else:
                内容=片段['text']
            段.append(内容+片段['suffix'])
        自身.发布({'text':''.join(段),'pending':自身.待定,'failed':自身.失败})

    def 跑(自身):
        '串行翻译已完成且未缓存的片段。返回期约；已在途、已失败或已拆除则立刻兑现'
        if 自身.待定 or 自身.失败 or 自身.已拆除():
            空=期约()
            空.解决(None)
            return 空
        下一=自身.下一段()
        if 下一 is None:
            空=期约()
            空.解决(None)
            return 空
        自身.待定=True
        自身.发出()
        def 一步(当前):
            '翻译当前片段，成功后接下一段。返回期约'
            if 当前 is None:
                return None
            def 已译(译文):
                '已拆除则丢掉结果；否则写入缓存并继续'
                if 自身.已拆除():
                    return None
                自身.缓存[当前['text']]=译文
                自身.发出()
                return 一步(自身.下一段())
            请求={**自身.选择,'text':当前['text']}
            return 自身.翻译(请求,自身.控制器.信号).然后(已译)
        def 失败(错误):
            '未拆除才标失败'
            if not 自身.已拆除():
                自身.失败=True
            return None
        def 收尾(值=None):
            '无论成败都结束在途并再发布一次'
            自身.待定=False
            自身.发出()
        def 启动(值=None):
            '从第一段开始'
            return 一步(下一)
        起点=期约()
        结果=起点.然后(启动).捕获(失败).最终(收尾)
        起点.解决(None)
        return 结果
