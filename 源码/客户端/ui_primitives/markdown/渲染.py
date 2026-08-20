"""直接 mdast→视图树 markdown 渲染器。

对齐上游 `ui-primitives/src/markdown/render.tsx`。公开面仅中文名。
替换 react-markdown / remark-rehype 管线：对解析节点做 switch，
流式可把已冻结块缓存为视图树；不可信输出策略不变：
链接/图片走协议白名单，图片额外要求绝对 HTTP(S)，
原始 HTML 当字面文本，KaTeX 不跑受信命令。
"""
import re#语言 id 截断
from urllib.parse import urlparse as 解析URL#协议检查
from .katex import 渲染TeX到树#TeX→树
from .代码块 import 代码块#围栏

__all__=[#仅中文公开名
    '净化链接','远端图片地址','建引用目标','收集引用目标',
    '渲染块们','包块子节点','渲染脚注区','行内代码Http地址',
]#公开面结束

def 取字段(对象,键,缺省=None):#读字段
    """从映射或对象读字段。"""
    if 对象 is None:#空
        return 缺省#缺席
    if isinstance(对象,dict):#映射
        return 对象[键] if 键 in 对象 else 缺省#键
    return getattr(对象,键,缺省)#属性

def 净化链接(网址):#协议白名单
    """http/https/mailto 放行；相对与其余方案空串。"""
    try:#解析
        方案=解析URL(网址).scheme.lower()#方案
    except Exception:#不可解析
        return ''#拒
    if 方案 in ('http','https','mailto'):#白名单
        return 网址#原样
    return ''#拒

def 远端图片地址(网址):#图片仅绝对 HTTP(S)
    """非绝对或非 http(s) 则 None。"""
    try:#解析
        方案=解析URL(网址).scheme.lower()#方案
    except Exception:#失败
        return None#拒
    return 网址 if 方案 in ('http','https') else None#放行或拒

def 归一化URI(网址):#对齐 micromark normalizeUri 的常用臂
    """空/空白原样；其余 strip。"""
    if 网址 is None:#缺
        return ''#空
    return str(网址).strip()#去空白

def 建引用目标():#空引用表
    """definitions / footnotes 两张映射。"""
    return {'definitions':{},'footnotes':{}}#空表

def 收集引用目标(节点们,目标):#深度优先收定义
    """同标识首个定义胜出（CommonMark）。"""
    for 节点 in 节点们 or []:#逐节点
        种=取字段(节点,'type')#类型
        if 种=='definition':#链接定义
            标识=str(取字段(节点,'identifier') or '').upper()#大写键
            if 标识 and 标识 not in 目标['definitions']:#首个
                目标['definitions'][标识]=节点#记下
        elif 种=='footnoteDefinition':#脚注定义
            标识=str(取字段(节点,'identifier') or '').upper()#大写键
            if 标识 and 标识 not in 目标['footnotes']:#首个
                目标['footnotes'][标识]=节点#记下
        子=取字段(节点,'children')#子树
        if 子:#有子
            收集引用目标(子,目标)#递归

def 渲染块们(块们,上下文):#顶层块→视图列表
    """空渲染丢弃，对齐原管线子列表。"""
    出=[]#结果
    for 块 in 块们 or []:#逐块
        节点=取字段(块,'node')#节点
        键=取字段(块,'key')#稳定 key
        元=渲染节点(节点,键,上下文)#渲染
        if 元 is not None:#非空
            出.append(元)#收下
    return 出#列表

def 包块子节点(元素们,边):#块间插入换行文本
    """edges 时两端也插换行（hast loose wrap）。"""
    包=[]#结果
    for 元 in 元素们 or []:#逐元素
        if 边 or len(包)>0:#需要前导换行
            包.append('\n')#换行
        包.append(元)#元素
    if 边 and len(元素们 or [])>0:#尾换行
        包.append('\n')#尾
    return 包#包好

def 渲染子节点(节点们,上下文):#子节点列表
    """带下标作 key。"""
    return [渲染节点(节点,下标,上下文) for 下标,节点 in enumerate(节点们 or [])]#映射

def 渲染节点(节点,键,上下文):#单节点→视图
    """merge-extensible 未映射类型返回 None。"""
    种=取字段(节点,'type')#类型
    if 种=='text':#文本
        return 取字段(节点,'value')#字面
    if 种=='paragraph':#段
        return {'type':'element','tag':'p','key':键,'children':渲染子节点(取字段(节点,'children'),上下文)}#段
    if 种=='heading':#标题
        深=取字段(节点,'depth') or 1#级
        return {'type':'element','tag':'h'+str(深),'key':键,'children':渲染子节点(取字段(节点,'children'),上下文)}#标题
    if 种=='blockquote':#引用
        子=包块子节点([c for c in 渲染子节点(取字段(节点,'children'),上下文) if c is not None],True)#包
        return {'type':'element','tag':'blockquote','key':键,'children':子}#引用
    if 种=='thematicBreak':#分隔
        return {'type':'element','tag':'hr','key':键}#hr
    if 种=='break':#硬换行
        return {'type':'fragment','key':键,'children':[{'type':'element','tag':'br'},'\n']}#br+换行
    if 种=='strong':#粗
        return {'type':'element','tag':'strong','key':键,'children':渲染子节点(取字段(节点,'children'),上下文)}#strong
    if 种=='emphasis':#斜
        return {'type':'element','tag':'em','key':键,'children':渲染子节点(取字段(节点,'children'),上下文)}#em
    if 种=='delete':#删
        return {'type':'element','tag':'del','key':键,'children':渲染子节点(取字段(节点,'children'),上下文)}#del
    if 种=='inlineCode':#行内码
        return 渲染行内码(节点,键,上下文)#行内
    if 种=='html':#原始 HTML 当字面
        return 取字段(节点,'value')#字面
    if 种=='code':#围栏
        return 渲染代码(节点,键,上下文)#代码
    if 种=='math':#块数学
        return {'type':'fragment','key':键,'children':渲染TeX到树(取字段(节点,'value') or '',True)}#展示
    if 种=='inlineMath':#行内数学
        return {'type':'fragment','key':键,'children':渲染TeX到树(取字段(节点,'value') or '',False)}#行内
    if 种=='list':#列表
        return 渲染列表(节点,键,上下文)#列表
    if 种=='listItem':#单项（手建树）
        return 渲染列表项(节点,列表项松散(节点),键,上下文)#项
    if 种=='table':#表
        return 渲染表(节点,键,上下文)#表
    if 种=='link':#链接
        return 渲染锚(取字段(节点,'url') or '',渲染子节点(取字段(节点,'children'),dict(上下文,inLink=True)),键)#锚
    if 种=='linkReference':#链接引用
        return 渲染链接引用(节点,键,上下文)#引用
    if 种=='image':#图
        return 渲染图(取字段(节点,'url') or '',取字段(节点,'alt') or '',键)#图
    if 种=='imageReference':#图引用
        return 渲染图引用(节点,键,上下文)#图引
    if 种=='footnoteReference':#脚注引用
        return 渲染脚注引用(节点,键,上下文)#脚注
    if 种 in ('definition','footnoteDefinition'):#定义别处渲染
        return None#丢
    return None#未映射

def 渲染行内码(节点,键,上下文):#行内 code
    """换行变空格；整段 HTTP(S) 可链；文件提及按钮。"""
    值=re.sub(r'\r?\n|\r',' ',取字段(节点,'value') or '')#换行→空格
    链=行内代码Http地址(值)#绝对 URL
    if 链 is not None:#URL 码
        return {'type':'element','tag':'code','key':键,'children':[渲染安全链(链,[值],'link')]}#带链
    提及=None#文件提及
    if not 上下文.get('inLink'):#不在锚内
        解析=取字段(上下文.get('fileMentions'),'resolve') if 上下文.get('fileMentions') else None#解析器
        if callable(解析):#有
            提及=解析(值)#解析
    if 提及 is not None:#命中文件
        return {'type':'element','tag':'code','key':键,'children':[{#按钮
            'type':'element','tag':'button','props':{#属性
                'type':'button','className':'fileMention',#类
                'title':取字段(提及,'title'),'aria-label':取字段(提及,'label'),#无障碍
                'onClick':取字段(提及,'open'),#打开
            },'children':[值],#正文
        }]}#结束
    return {'type':'element','tag':'code','key':键,'children':[值]}#惰性码

def 渲染代码(节点,键,上下文):#围栏代码
    """空围栏保留 pre/code；math 定稿走 TeX；其余 CodeBlock。"""
    语言=取字段(节点,'lang')#lang
    值=取字段(节点,'value') or ''#正文
    if 值=='':#空围栏
        类=None if 语言 is None else 'language-'+str(语言)#类
        return {'type':'element','tag':'pre','key':键,'children':[{'type':'element','tag':'code','props':{'className':类}}]}#pre
    语=None#语法 id
    if 语言 is not None:#有 lang
        命=re.match(r'^[\w-]+',str(语言))#截断
        语=命.group(0) if 命 else None#id
    if not 上下文.get('streaming') and 语=='math':#定稿 math 围栏
        return {'type':'fragment','key':键,'children':渲染TeX到树(值+'\n',True)}#展示 TeX
    文案=上下文.get('codeLabels') or {}#复制文案
    块=代码块({'code':值+'\n','lang':None if 上下文.get('streaming') else 语,'copyLabel':文案.get('copyLabel'),'copiedLabel':文案.get('copiedLabel')})#块
    视=块.渲染()#视图
    视['key']=键#稳定 key
    return 视#代码块

def 列表松散(列表):#列表是否 loose
    """自身或任一项 spread。"""
    if 取字段(列表,'spread'):#自身
        return True#松
    return any(列表项松散(项) for 项 in 取字段(列表,'children') or [])#任一项

def 列表项松散(项):#单项是否 loose
    """spread 或子多于一。"""
    扩=取字段(项,'spread')#spread
    if 扩 is not None:#显式
        return bool(扩)#值
    return len(取字段(项,'children') or [])>1#多子

def 渲染列表(节点,键,上下文):#ul/ol
    """任务列表加 contains-task-list。"""
    松=列表松散(节点)#松散
    属性={}#props
    起=取字段(节点,'start')#start
    if isinstance(起,(int,float)) and not isinstance(起,bool) and 起!=1:#非 1
        属性['start']=int(起)#起始
    if any(isinstance(取字段(项,'checked'),bool) for 项 in 取字段(节点,'children') or []):#任务
        属性['className']='contains-task-list'#类
    标签='ol' if 取字段(节点,'ordered') else 'ul'#有序/无序
    子=[渲染列表项(项,松,下标,上下文) for 下标,项 in enumerate(取字段(节点,'children') or [])]#项
    return {'type':'element','tag':标签,'key':键,'props':属性,'children':子}#列表

def 渲染块条目(块们,上下文):#区分段与其它块
    """供列表项/脚注体拆段。"""
    条=[]#条目
    for 下标,块 in enumerate(块们 or []):#逐块
        if 取字段(块,'type')=='paragraph':#段
            条.append({'paragraph':渲染子节点(取字段(块,'children'),上下文)})#段
        else:#其它
            元=渲染节点(块,下标,上下文)#渲
            if 元 is not None:#非空
                条.append({'element':元})#元素
    return 条#条目

def 渲染列表项(项,松散,键,上下文):#li
    """紧段解包；任务项前缀 checkbox。"""
    条=渲染块条目(取字段(项,'children'),上下文)#条目
    任务=isinstance(取字段(项,'checked'),bool)#任务
    if 任务:#勾选
        勾={'type':'element','tag':'input','key':'task-checkbox','props':{'type':'checkbox','checked':取字段(项,'checked') is True,'disabled':True}}#框
        if 条 and 'paragraph' in 条[0]:#首段
            段=条[0]['paragraph']#段子
            条[0]['paragraph']=([勾,' ']+段) if len(段)>0 else [勾]#前缀
        else:#无段
            条.insert(0,{'paragraph':[勾]})#插入
    片=[]#子片
    for 下标,入 in enumerate(条):#逐条
        是段='paragraph' in 入#段?
        if 松散 or 下标!=0 or not 是段:#前导换行
            片.append('\n')#换行
        if not 是段:#元素
            片.append(入['element'])#元素
        elif 松散:#松段
            片.append({'type':'element','tag':'p','key':'p-'+str(下标),'children':入['paragraph']})#p
        else:#紧段
            片.append({'type':'fragment','key':'p-'+str(下标),'children':入['paragraph']})#片
    尾=条[-1] if 条 else None#尾
    if 尾 is not None and (松散 or 'paragraph' not in 尾):#尾换行
        片.append('\n')#换行
    类='task-list-item' if 任务 else None#类
    return {'type':'element','tag':'li','key':键,'props':{'className':类} if 类 else {},'children':片}#li

def 渲染表(节点,键,上下文):#表滚动壳
    """首行 thead，其余 tbody。"""
    对齐=取字段(节点,'align')#对齐列
    行们=取字段(节点,'children') or []#行
    头=行们[0] if 行们 else None#头
    体=行们[1:] if len(行们)>1 else []#体
    子=[]#table 子
    if 头 is not None:#有头
        子.append({'type':'element','tag':'thead','children':[渲染表行(头,'th',对齐,0,上下文)]})#thead
    if 体:#有体
        子.append({'type':'element','tag':'tbody','children':[渲染表行(行,'td',对齐,下标+1,上下文) for 下标,行 in enumerate(体)]})#tbody
    return {'type':'element','tag':'div','key':键,'props':{'className':'tableScroll'},'children':[{'type':'element','tag':'table','children':子}]}#壳

def 渲染表行(行,格标,对齐,键,上下文):#tr
    """有对齐时按列数补/截。"""
    格们=取字段(行,'children') or []#单元格
    长=len(格们) if 对齐 is None else len(对齐)#列数
    胞=[]#cells
    for 下标 in range(长):#逐列
        格=格们[下标] if 下标<len(格们) else None#格
        齐=对齐[下标] if 对齐 is not None and 下标<len(对齐) else None#对齐
        样式={'textAlign':齐} if 齐 is not None else None#style
        子=渲染子节点(取字段(格,'children'),上下文) if 格 is not None else []#子
        胞.append({'type':'element','tag':格标,'key':下标,'props':{'style':样式} if 样式 else {},'children':子})#胞
    return {'type':'element','tag':'tr','key':键,'children':胞}#tr

def 渲染安全链(网址,子们,键):#白名单锚
    """不合法则解包为片。"""
    安=净化链接(网址)#净化
    if 安=='':#拒
        return {'type':'fragment','key':键,'children':子们}#解包
    外=解析URL(安).scheme.lower() in ('http','https')#外链
    属性={'href':安}#href
    if 外:#外链属性
        属性['target']='_blank'#新窗
        属性['rel']='noopener noreferrer'#安全
    return {'type':'element','tag':'a','key':键,'props':属性,'children':子们}#a

def 渲染锚(网址,子们,键):#markdown 目的地锚
    """先归一化再白名单。"""
    return 渲染安全链(归一化URI(网址),子们,键)#锚

def 行内代码Http地址(值):#整段是否绝对 HTTP(S)
    """有首尾空白则否。"""
    if 值.strip()!=值:#有空白
        return None#否
    try:#解析
        方案=解析URL(值).scheme.lower()#方案
    except Exception:#非 URL
        return None#否
    return 值 if 方案 in ('http','https') else None#放行

def 渲染图(网址,替代,键):#img 或 alt span
    """非远端则只画 alt。"""
    源=远端图片地址(净化链接(归一化URI(网址)))#源
    if 源 is None:#不可用
        return {'type':'element','tag':'span','key':键,'props':{'className':'imageAlt'},'children':[替代]}#alt
    return {'type':'element','tag':'img','key':键,'props':{#图
        'className':'image','src':源,'alt':替代,#属性
        'loading':'lazy','decoding':'async','referrerPolicy':'no-referrer',#策略
    }}#img

def 引用后缀(节点):#缺定义时回退括号文
    """collapsed/full/shortcut。"""
    形=取字段(节点,'referenceType')#形
    if 形=='collapsed':#空方
        return '][]'#后缀
    if 形=='full':#全
        return ']['+str(取字段(节点,'label') or 取字段(节点,'identifier') or '')+']'#后缀
    return ']'#短

def 渲染链接引用(节点,键,上下文):#linkReference
    """无定义回退括号源文。"""
    定义=上下文['targets']['definitions'].get(str(取字段(节点,'identifier') or '').upper())#定义
    if 定义 is None:#缺
        return {'type':'fragment','key':键,'children':['[']+渲染子节点(取字段(节点,'children'),上下文)+[引用后缀(节点)]}#回退
    return 渲染锚(取字段(定义,'url') or '',渲染子节点(取字段(节点,'children'),dict(上下文,inLink=True)),键)#锚

def 渲染图引用(节点,键,上下文):#imageReference
    """无定义回退 markdown 源文。"""
    定义=上下文['targets']['definitions'].get(str(取字段(节点,'identifier') or '').upper())#定义
    if 定义 is None:#缺
        return '!['+str(取字段(节点,'alt') or '')+引用后缀(节点)#字面
    return 渲染图(取字段(定义,'url') or '',取字段(节点,'alt') or '',键)#图

def 渲染脚注引用(节点,键,上下文):#footnoteReference
    """上标序号；页内锚不过白名单。"""
    标识=str(取字段(节点,'identifier') or '').upper()#键
    已见=上下文['footnoteCounts'].get(标识)#已见次数
    if 已见 is None:#首次
        上下文['footnoteOrder'].append(标识)#入序
    上下文['footnoteCounts'][标识]=(已见 or 0)+1#累计
    号=上下文['footnoteOrder'].index(标识)+1#1-based
    return {'type':'element','tag':'sup','key':键,'children':[str(号)]}#上标

def 渲染脚注区(上下文):#文末脚注 section
    """按首次引用序；无定义则跳过；全空则 None。"""
    项们=[]#li 列表
    for 标识 in 上下文.get('footnoteOrder') or []:#按序
        定义=上下文['targets']['footnotes'].get(标识)#定义
        if 定义 is None:#无
            continue#跳
        次=上下文['footnoteCounts'].get(标识) or 0#引用次数
        回=[]#↩ 标记
        for 参 in range(1,次+1):#每次
            if len(回)>0:#间隔
                回.append(' ')#空格
            回.append('↩')#回指
            if 参>1:#二次起带上标
                回.append({'type':'element','tag':'sup','key':'re-'+str(参),'children':[str(参)]})#上标
        条=渲染块条目(取字段(定义,'children'),上下文)#体条目
        尾=条[-1] if 条 else None#尾
        体=[]#body
        for 下标,入 in enumerate(条):#逐条
            if 'paragraph' in 入:#段
                子=list(入['paragraph'])#拷
                if 入 is 尾:#尾段挂回指
                    子.extend([' ']+回)#空格+回指
                体.append({'type':'element','tag':'p','key':'p-'+str(下标),'children':子})#p
            else:#元素
                体.append(入['element'])#元素
        if 尾 is None or 'paragraph' not in 尾:#无尾段
            体.extend(回)#回指挂块末
        项们.append({'type':'element','tag':'li','key':标识,'props':{'id':'user-content-fn-'+归一化URI(标识.lower())},'children':包块子节点(体,True)})#li
    if len(项们)==0:#无
        return None#空
    return {'type':'element','tag':'section','key':'footnotes','props':{'data-footnotes':True,'className':'footnotes'},'children':[#区
        {'type':'element','tag':'h2','props':{'id':'footnote-label','className':'sr-only'},'children':['Footnotes']},#隐藏标题
        {'type':'element','tag':'ol','children':项们},#有序列表
    ]}#section
