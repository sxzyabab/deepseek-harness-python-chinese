"""面向模型的 `web_fetch` 工具。本模块负责 schema、校验与展示；`ctx.web` 负责检索。超时是部署策略，不是模型参数：配置写入 ToolDefinition.timeoutMs，由超时策略强制执行，本工具转发得到的 signal。提供方超时仍作为直接服务调用方的后盾。"""
import html#解码实体
import re#标签扫描
from html.parser import HTMLParser#构建转换用的简易 DOM
from tools import 定义工具#定义面向模型的工具
from cordis.工具 import 已兑现,是否thenable#立刻兑现与可等待判定
from llm import 断言永不#封闭联合穷尽检查

最大转换深度=512#超过该嵌套深度的 HTML 跳过转换、原样通过
空元素名=frozenset([#永不写闭合标签的元素，因此不会增高词法栈
    'area','base','br','col','embed','hr','img','input',#前一半空元素
    'link','meta','param','source','track','wbr',#后一半空元素
])#空元素结束
原始文本元素名=frozenset(['script','style','noscript'])#内容按文本解析、直到匹配结束标签的元素
截断页脚='\n\n(Content truncated. Fetch a more specific URL or section for the full text.)'#提供方或输出上限截断内容时追加的提示，字面量不改
渲染缓存={}#按结果身份→上限→渲染；对齐 WeakMap，使 render/presentationMeta 共用一次转换

def 取字段(对象,键,缺省=None):#从映射或对象读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空对象
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        if 键 in 对象:#自有键
            return 对象[键]#映射键
        return 缺省#缺席
    return getattr(对象,键,缺省)#对象属性

def 缺席(对象,键):#字段是否缺席
    """对齐字段 === undefined。"""
    if 对象 is None:#空对象
        return True#缺席
    if isinstance(对象,dict):#映射
        return 键 not in 对象#无键则缺席
    return not hasattr(对象,键)#无属性则缺席

def 解开(值):#承诺则等待否则原样
    """承诺则等待，否则原样返回。"""
    if 是否thenable(值):#可等待
        return 值.等待()#等待承诺
    return 值#同步值

def 解析抓取参数(参数):#把参数收成缝的请求字段
    """校验 schema DSL 表达不了的约束：`url` 不能是空白。否则抛普通 Error。没有超时参数——工具调用预算是部署策略。"""
    if len(取字段(参数,'url').strip())==0:#空白 url
        raise Exception('url must be a non-empty string')#空白 url 抛错
    return {'url':取字段(参数,'url')}#原样返回 url

def 是否标签边界(字符):#判断结束标签名边界
    """字符是否可以出现在原始文本结束标签名之后。"""
    return 字符 is None or 字符=='>' or 字符=='/' or (len(字符)==1 and 字符.isspace())#结尾、`>`、`/` 或空白都算边界

def 查找原始文本结束(小写html,名,起点):#从起点起找 `</name`
    """查找匹配的原始文本结束标签，不把正文里像标记的文字当标记。"""
    前缀='</'+名#结束标签前缀
    候选=小写html.find(前缀,起点)#第一处候选
    while 候选!=-1:#还有候选
        后位=候选+len(前缀)#前缀之后
        后字=小写html[后位] if 后位<len(小写html) else None#后一字符
        if 是否标签边界(后字):#前缀后面是标签边界
            return 候选#命中
        候选=小写html.find(前缀,候选+len(前缀))#从候选之后再找
    return -1#没有命中

def 越过转换深度(正文):#词法栈是否超过转换深度
    """保守地拒绝词法元素栈越过转换深度上限的 HTML。单次扫描忽略注释里的闭合标签、跳过原始文本正文、尊重引号内的 `>`，并且只接受当前元素的闭合标签；畸形输入因此会多计而不是藏起嵌套。"""
    小写=正文.lower()#小写副本，用来比标签名
    打开=[]#当前未闭合元素栈
    游标=0#扫描游标
    注释中=False#是否在 HTML 注释内
    while 游标<len(正文):#尚未扫完
        起点=正文.find('<',游标)#下一处 `<`
        if 注释中:#仍在注释里
            结束=正文.find('-->',游标)#注释结束
            if 结束!=-1 and (起点==-1 or 结束<起点):#结束在下一个 `<` 之前
                注释中=False#离开注释
                游标=结束+3#跳过 `-->`
                continue#继续扫描
        if 起点==-1:#没有更多 `<`
            break#离开扫描
        if (not 注释中) and 正文.startswith('<!--',起点):#注释开始
            注释中=True#进入注释
            游标=起点+4#跳过 `<!--`
            continue#继续扫描
        读=起点+1#从 `<` 后开始读
        闭合=读<len(正文) and 正文[读]=='/'#是否闭合标签
        if 闭合:#闭合标签
            读+=1#跳过 `/`
        名起=读#标签名起点
        while 读<len(正文) and re.match(r'[a-zA-Z0-9-]',正文[读]):#读完标签名
            读+=1#前进
        if 读==名起 or (not re.match(r'[a-zA-Z]',正文[名起])):
            游标=起点+1#把这个 `<` 当普通字符
            continue#继续扫描
        名=小写[名起:读]#小写标签名
        引号=None#当前属性引号
        while 读<len(正文):#扫到标签结束
            字=正文[读]#当前字符
            读+=1#前进
            if 引号 is not None:#在引号内
                if 字==引号:#碰到同引号则退出
                    引号=None#退出引号
            elif 字=='"' or 字=="'":#进入引号
                引号=字#记下引号种类
            elif 字=='>':#标签结束
                break#离开属性扫描
        if 读==0 or 正文[读-1]!='>':#没有完整 `>`
            break#停止以免误判
        if 闭合:#闭合标签
            if (not 注释中) and len(打开)>0 and 打开[-1]==名:#只弹出当前栈顶同名元素
                打开.pop()#弹出
        else:#开始标签
            末=读-2#`>` 前一个字符
            while 末>=0 and 正文[末].isspace():#跳过 `>` 前空白
                末-=1#后退
            if 名 not in 空元素名 and (末<0 or 正文[末]!='/'):#非空元素且非自闭合
                打开.append(名)#压栈
                if len(打开)>最大转换深度:#超过深度上限
                    return True#越过
                if (not 注释中) and 名 in 原始文本元素名:#原始文本元素
                    结束位=查找原始文本结束(小写,名,读)#找匹配结束标签
                    if 结束位==-1:#没有结束标签
                        break#停止
                    游标=结束位#跳到结束标签处，让后续循环按闭合标签处理
                    continue#不要把正文当标记
        游标=读#从本标签结束后继续
    return False#未越过深度上限

class _节点:#简易 DOM 节点
    """转换器用的元素或文本节点。"""
    def __init__(自身,种类,名=None,属性=None,文本=''):#构造
        自身.种类=种类#element 或 text
        自身.名=名#小写标签名
        自身.属性=属性 if 属性 is not None else {}#属性映射
        自身.文本=文本#文本内容
        自身.孩子们=[]#子节点

class _建树解析器(HTMLParser):#把 HTML 收成简易树
    """html.parser 建树；整段丢掉 script/style/noscript。"""
    def __init__(自身):#构造
        super().__init__(convert_charrefs=True)#实体转字符
        自身.根=_节点('element','root')#虚拟根
        自身.栈=[自身.根]#元素栈
        自身.丢弃深度=0#在 script/style/noscript 内时 >0
    def handle_starttag(自身,标签,属性们):#开始标签
        名=标签.lower()#小写
        if 自身.丢弃深度>0:#已在丢弃区内
            if 名 in 原始文本元素名:#嵌套同名也加深
                自身.丢弃深度+=1#加深
            return#丢掉
        if 名 in 原始文本元素名:#进入丢弃区
            自身.丢弃深度=1#开始丢弃
            return#不建节点
        属性={}#属性映射
        for 键,值 in 属性们:#逐个
            属性[键.lower()]=值 if 值 is not None else ''#收下
        节点=_节点('element',名,属性)#新元素
        自身.栈[-1].孩子们.append(节点)#挂到父下
        if 名 not in 空元素名:#非空元素
            自身.栈.append(节点)#压栈
    def handle_endtag(自身,标签):#结束标签
        名=标签.lower()#小写
        if 自身.丢弃深度>0:#在丢弃区
            if 名 in 原始文本元素名:#离开一层
                自身.丢弃深度-=1#减深
            return#丢掉
        while len(自身.栈)>1:#找到同名或退到根
            顶=自身.栈[-1].名#栈顶名
            自身.栈.pop()#弹出
            if 顶==名:#匹配
                break#停
    def handle_data(自身,数据):#文本
        if 自身.丢弃深度>0:#丢弃区
            return#丢掉
        if 数据=='':#空
            return#忽略
        自身.栈[-1].孩子们.append(_节点('text',文本=数据))#文本节点
    def handle_entityref(自身,名):#命名实体
        自身.handle_data(html.unescape('&'+名+';'))#解码后当文本
    def handle_charref(自身,名):#数字实体
        自身.handle_data(html.unescape('&#'+名+';'))#解码后当文本

def _取对齐(格子):#读 align 或 CSS text-align
    """把 HTML 单元格对齐映射成 GFM 分隔行标记。"""
    属性=格子.属性#属性
    对齐=(属性.get('align') or '')#align 属性
    样式=属性.get('style') or ''#style
    匹配=re.search(r'text-align\s*:\s*([a-z]+)',样式,flags=re.I)#CSS text-align
    if 匹配:#有 CSS
        对齐=匹配.group(1)#用 CSS
    对齐=对齐.lower()#小写
    if 对齐=='left':#左对齐
        return ':---'#左
    if 对齐=='right':#右对齐
        return '---:'#右
    if 对齐=='center':#居中
        return ':---:'#中
    return '---'#默认无对齐

def _渲染单元格(内容,下标):#按列下标拼单元格
    """渲染一个 GFM 表格单元格，不解释 HTML 的 span 计数。"""
    前缀='| ' if 下标==0 else ' '#首列前加竖线，其余只留空格
    逃=内容.strip().replace('\n\r','<br>').replace('\n','<br>')#去空白、换行改 br
    逃=re.sub(r'\|+','\\|',逃)#转义竖线
    if len(逃)<3:#补齐宽度
        逃=逃+' '*(3-len(逃))#右侧补空格
    return 前缀+逃+' |'#拼出 `| 内容 |` 片段

def _纯文本(节点):#只取后代文本，不做行内标记
    """pre/code 围栏内容：只要文本。"""
    if 节点.种类=='text':#文本
        return 节点.文本#原样
    return ''.join([_纯文本(孩) for 孩 in 节点.孩子们])#下钻

def _行内(节点们):#拼行内 markdown
    """把子节点收成行内文本。"""
    段=[]#片段
    for 孩 in 节点们:#逐子
        段.append(_转节点(孩,块级=False))#行内模式
    return ''.join(段)#拼接

def _转节点(节点,块级=True):#递归转 markdown
    """按标签名转成面向模型的 markdown；表格忽略 colspan/rowspan。"""
    if 节点.种类=='text':#文本
        return 节点.文本#原样
    名=节点.名#标签
    if 名 in ('script','style','noscript'):#防御：建树应已丢掉
        return ''#空
    if 名 in ('h1','h2','h3','h4','h5','h6'):#ATX 标题
        级=int(名[1])#级数
        内=_行内(节点.孩子们).strip()#标题文本
        return '\n'+('#'*级)+' '+内+'\n\n'#ATX
    if 名=='p':#段落
        return '\n'+_行内(节点.孩子们).strip()+'\n\n'#段
    if 名=='br':#换行
        return '\n'#换行
    if 名=='hr':#分隔
        return '\n---\n\n'#水平线
    if 名 in ('strong','b'):#粗体
        return '**'+_行内(节点.孩子们)+'**'#粗
    if 名 in ('em','i'):#斜体
        return '*'+_行内(节点.孩子们)+'*'#斜
    if 名=='code':#代码：块级外层走 pre，此处为行内
        return '`'+_纯文本(节点)+'`'#行内码
    if 名=='pre':#代码块
        码=_纯文本(节点).strip('\n')#只要文本
        return '\n```\n'+码+'\n```\n\n'#围栏
    if 名=='a':#链接
        址=节点.属性.get('href') or ''#href
        文=_行内(节点.孩子们) or 址#锚文本
        return '['+文+']('+址+')'#markdown 链接
    if 名 in ('ul','ol'):#列表
        行们=[]#列表行
        序=1#有序序号
        for 孩 in 节点.孩子们:#子项
            if 孩.种类!='element' or 孩.名!='li':#非 li
                continue#跳过
            内=_行内(孩.孩子们).strip()#项文本
            if 名=='ul':#无序
                行们.append('- '+内)#短横
            else:#有序
                行们.append(str(序)+'. '+内)#序号
                序+=1#下一号
        return '\n'+'\n'.join(行们)+'\n\n'#列表块
    if 名=='blockquote':#引用
        内=_行内(节点.孩子们).strip().split('\n')#行
        return '\n'+'\n'.join(['> '+行 for 行 in 内])+'\n\n'#引用
    if 名=='table':#表格：忽略 colspan/rowspan
        行项们=[]#({行,在头区})
        def 收集行(节,在头区):#递归收集 tr，保留 thead 语义
            if 节.种类!='element':#文本
                return#忽略
            if 节.名=='thead':#头区
                for 孙 in 节.孩子们:#头区子
                    收集行(孙,True)#标记在头区
                return#停
            if 节.名=='tr':#行
                行项们.append({'行':节,'在头区':在头区})#收下
                return#不再下钻
            for 孙 in 节.孩子们:#下钻 tbody/table
                收集行(孙,在头区)#递归
        收集行(节点,False)#从 table 收集
        if len(行项们)==0:#空表
            return ''#空
        出=[]#markdown 行
        for 行下标,项 in enumerate(行项们):#逐行
            行=项['行']#tr 节点
            格子=[孩 for 孩 in 行.孩子们 if 孩.种类=='element' and 孩.名 in ('th','td')]#单元格，不展开 span
            内容们=[_行内(格.孩子们) for 格 in 格子]#格文本
            出.append(''.join([_渲染单元格(内容们[i] if i<len(内容们) else '',i) for i in range(len(格子))]))#拼行
            是头=(项['在头区'] or 行下标==0) and len(格子)>0 and all(格.名=='th' for 格 in 格子)#对齐 TS：THEAD 或首行且全 TH
            if 是头:#表头行才需要分隔线
                出.append(''.join([_渲染单元格(_取对齐(格子[i]),i) for i in range(len(格子))]))#按对齐拼分隔行
        return '\n'+'\n'.join(出)+'\n\n'#表块
    if 名 in ('thead','tbody','tfoot','tr','th','td','li','root','div','span','section','article','main','header','footer','nav','figure','figcaption'):
        if 块级:#块容器
            return ''.join([_转节点(孩,块级=True) for 孩 in 节点.孩子们])#下钻
        return _行内(节点.孩子们)#行内
    if 块级:#未知块标签：下钻保留文本
        return ''.join([_转节点(孩,块级=True) for 孩 in 节点.孩子们])#下钻
    return _行内(节点.孩子们)#未知行内标签

def html转markdown(正文):#HTML→markdown，对齐 turndown+GFM 面向模型展示
    """共享的 HTML→markdown 转换：ATX 标题、围栏代码、短横列表；整段丢掉 script/style/noscript；表格忽略 colspan。"""
    解析=_建树解析器()#建树
    解析.feed(正文)#喂入
    解析.close()#结束
    文本=_转节点(解析.根,块级=True)#从根转
    文本=re.sub(r'\n{3,}','\n\n',文本)#压缩多余空行
    return 文本.strip()+('\n' if 文本.strip() else '')#去首尾空白

def 渲染正文(正文,最大输入字符):#按 kind 渲染正文
    """把抓取到的正文渲染成面向模型的 markdown 文本。"""
    内容=取字段(正文,'content')[:最大输入字符]#只取上限内的源前缀
    源截断=len(内容)!=len(取字段(正文,'content'))#源是否被切开
    种类=取字段(正文,'kind')#正文种类
    if 种类=='html':#HTML 需要转换
        if 越过转换深度(内容):#过深则原样返回
            return {'text':内容,'sourceTruncated':源截断}#原样
        try:#尝试转换
            return {'text':html转markdown(内容),'sourceTruncated':源截断}#转换成 markdown
        except Exception:#转换失败用原始 HTML（对齐 turndown 抛错降级）
            return {'text':内容,'sourceTruncated':源截断}#原始 HTML
    if 种类=='text':#纯文本
        return {'text':内容,'sourceTruncated':源截断}#原样返回
    return 断言永不(正文,'unhandled web fetch body kind')#未处理的 kind 在编译期/穷尽失败

def 计算抓取输出(结果,最大输出字符):#无缓存地拼完整输出
    """renderFetchOutput 背后的无缓存转换。"""
    页头='Fetched '+取字段(结果,'url')+' (HTTP '+str(取字段(结果,'statusCode'))+')\n\n'#页头：最终 URL 与状态码
    已渲染=渲染正文(取字段(结果,'body'),最大输出字符)#按上限渲染正文
    前缀=页头+取字段(已渲染,'text')#页头加正文
    截断=bool(取字段(结果,'truncated')) or bool(取字段(已渲染,'sourceTruncated')) or len(前缀)>最大输出字符#提供方、源切或超上限
    完整=前缀+(截断页脚 if 截断 else '')#需要时追加截断页脚
    if len(完整)<=最大输出字符:#整段未超上限
        return {'text':完整,'truncated':截断}#整段
    if 最大输出字符<len(截断页脚):#上限比页脚还短，硬切
        return {'text':完整[:最大输出字符],'truncated':截断}#硬切
    return {'text':前缀[:最大输出字符-len(截断页脚)]+截断页脚,'truncated':截断}#为页脚留位置后切开前缀

def 渲染抓取输出(结果,最大输出字符):#带缓存地渲染抓取输出
    """把抓取结果渲染成有界的面向模型文本和有效截断标记。按结果身份记忆化，使成对的 render/presentationMeta 只转换一次。"""
    键=id(结果)#结果对象身份
    上限表=渲染缓存.get(键)#按结果取上限表
    if 上限表 is None:#没有
        上限表={}#新建
        渲染缓存[键]=上限表#挂回
    缓存=上限表.get(最大输出字符)#同一上限的缓存
    if 缓存 is not None:#命中
        return 缓存#直接返回
    算出=计算抓取输出(结果,最大输出字符)#未命中则计算
    上限表[最大输出字符]=算出#写入该上限
    return 算出#返回刚算的结果

def 格式化抓取输出(结果,最大输出字符):#对外的文本渲染入口
    """把抓取结果格式化成一块面向模型的文本，整块有界。"""
    return 取字段(渲染抓取输出(结果,最大输出字符),'text')#只取文本

def 呈现抓取调用(参数):#进行中抓取卡片
    """进行中调用的展示：一张以 URL 为标题的抓取卡片。"""
    网址=取字段(参数,'url')#请求 URL
    return {'card':'generic','title':网址,'kind':'fetch','rawInput':网址}#标题与原始输入都是 url

def 抓取元自值(值,最大输出字符):#从结果值抽出展示 meta
    """把已校验的 `web_fetch` 输出值投影成可回放的展示 meta。truncated 是面向模型文本所反映的有效截断。"""
    return {#meta 对象
        'url':取字段(值,'url'),#最终 URL
        'statusCode':取字段(值,'statusCode'),#HTTP 状态码
        'truncated':取字段(渲染抓取输出(值,最大输出字符),'truncated'),#与渲染共用有效截断
    }#对象结束

def 抓取元自结果(元):#校验回放 meta
    """把不透明的现场或回放结果元数据收窄为 WebFetchMeta。畸形元数据返回 None，展示可回退到通用卡片。"""
    if not isinstance(元,dict) or 元 is None:#非普通对象
        return None#畸形
    网址=取字段(元,'url')#url
    状态码=取字段(元,'statusCode')#statusCode
    截断=取字段(元,'truncated')#truncated
    if not isinstance(网址,str) or not isinstance(状态码,(int,float)) or isinstance(状态码,bool) or not isinstance(截断,bool):
        return None#类型不对
    return {'url':网址,'statusCode':状态码,'truncated':截断}#收成 WebFetchMeta

def 呈现抓取结果(参数,结果):#完成态抓取卡片
    """已完成调用的展示：一张 `web` 抓取卡片，携带 `meta` 里的检索摘要。"""
    if 取字段(结果,'isError'):#错误结果不画专用卡
        return None#通用卡
    元=抓取元自结果(取字段(结果,'meta'))#校验 meta
    if 元 is None:#畸形则交给通用卡
        return None#通用卡
    return {#专用 web 抓取卡
        'card':'web',#走 web 卡片
        'kind':'fetch',#抓取种类
        'title':取字段(参数,'url'),#请求 URL 作标题
        'url':取字段(元,'url'),#最终 URL
        'statusCode':取字段(元,'statusCode'),#HTTP 状态码
        'truncated':取字段(元,'truncated'),#有效截断
    }#视图对象结束

def 应用网络抓取工具(上下文,超时毫秒,最大输出字符):#注册 web_fetch 与提示词
    """注册 `web_fetch` 工具及其系统提示词指引。"""
    上下文.systemPrompt.段落({#写入系统提示词段落
        'name':'tool:web_fetch',#段落名
        'order':111,#排序
        'text':'Use the web_fetch tool to retrieve the content of a specific HTTP(S) URL (for example a result from web_search). It returns the page content decoded to text. Cite the URL as a markdown link when you use its content.',#面向模型的英文指引，字面量不改
    })#提示词段落结束
    def 渲染(参数,值):#面向模型的文本块
        """把结构化结果渲染成文本块。"""
        return [{'type':'text','text':格式化抓取输出(值,最大输出字符)}]#单个文本块
    def 展示元(参数,值):#回放用 meta
        """投影可回放展示 meta。"""
        return 抓取元自值(值,最大输出字符)#展示 meta
    def 并发安全():#提供方读取不改变父 agent 状态
        """始终可并发。"""
        return True#安全
    def 执行(参数,执行上下文):#真正抓取
        """校验后交给 ctx.web.fetch。"""
        输入=解析抓取参数(参数)#校验 url 非空
        结果=解开(上下文.web.抓取(#交给能力缝
            {'url':取字段(输入,'url')},#请求字段
            取字段(执行上下文,'signal'),#工具调用取消信号
        ))#fetch 结束
        正文=取字段(结果,'body')#正文
        return 已兑现({#规范输出值
            'url':取字段(结果,'url'),#最终 URL
            'statusCode':取字段(结果,'statusCode'),#状态码
            'body':{'kind':取字段(正文,'kind'),'content':取字段(正文,'content')},#正文 kind 与内容
            'truncated':取字段(结果,'truncated'),#提供方截断
        })#兑现规范输出
    def 呈现结果(参数,结果):#完成态卡片
        """委托呈现抓取结果。"""
        return 呈现抓取结果(参数,结果)#完成态卡片
    上下文.tools.登记(定义工具({#注册 web_fetch 工具
        'name':'web_fetch',#工具名
        'description':'Fetch the content of a specific HTTP(S) URL and return it decoded to text.',#工具描述，字面量不改
        'parameters':{#入参 schema
            'url':{'type':'string','required':True,'description':'The HTTP(S) URL to fetch.'},#要抓的 URL
        },#parameters 结束
        'output':{#输出 schema 与渲染
            'schema':{#结果值 schema
                'type':'object',#对象
                'additionalProperties':False,#禁止多余字段
                'properties':{#字段
                    'url':{'type':'string','required':True},#最终 URL
                    'statusCode':{'type':'integer','required':True},#HTTP 状态码
                    'body':{#正文
                        'required':True,#必填
                        'oneOf':[#html 或 text
                            {#HTML 正文
                                'type':'object',#对象
                                'additionalProperties':False,#禁止多余字段
                                'properties':{#字段
                                    'kind':{'type':'string','required':True,'const':'html'},#种类固定为 html
                                    'content':{'type':'string','required':True},#HTML 字符串
                                },#html properties 结束
                            },#html 分支结束
                            {#纯文本正文
                                'type':'object',#对象
                                'additionalProperties':False,#禁止多余字段
                                'properties':{#字段
                                    'kind':{'type':'string','required':True,'const':'text'},#种类固定为 text
                                    'content':{'type':'string','required':True},#文本字符串
                                },#text properties 结束
                            },#text 分支结束
                        ],#oneOf 结束
                    },#body 结束
                    'truncated':{'type':'boolean','required':True},#提供方是否截断
                },#properties 结束
            },#schema 结束
            'render':渲染,#面向模型的文本块
            'presentationMeta':展示元,#回放用 meta
        },#output 结束
        'timeoutMs':超时毫秒,#协作超时预算
        'isConcurrencySafe':并发安全,#提供方读取不改变父 agent 状态
        'execute':执行,#真正抓取
        'presentCall':呈现抓取调用,#进行中卡片
        'presentResult':呈现结果,#完成态卡片
    }))#register 结束
