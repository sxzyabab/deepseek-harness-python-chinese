'插件市场索引格式 1：JSON 校验、相对图标解析和安装参数。格式由插件市场索引格式笔记定义；读取方和生成器共用这份校验'
import json#标识写入错误文本
import math#有限数
import re#模块层编译一次
from urllib.parse import urljoin,urlparse#相对图标与规范网址
from .类型 import (#再导出校验后的记录
    市场声明,市场排序键声明,市场索引元数据,市场插件元数据,市场仓库,
    市场npm来源,市场git来源,市场来源,市场引擎,市场版本,市场插件,市场索引,市场安装目标,
)#类型结束
from . import 类型#导入本目录全部子模块

__all__=[#仅中文公开名
    '市场索引错误','最大内联图标字节','解析市场索引','市场安装目标',
    '市场声明','市场排序键声明','市场索引元数据','市场插件元数据','市场仓库',
    '市场npm来源','市场git来源','市场来源','市场引擎','市场版本','市场插件','市场索引','市场安装目标',
]#公开面结束

语言标识=re.compile(r'^[a-z]{2,8}(?:-[a-z0-9]{1,8})*\Z',re.ASCII)#小写语言 id
包名=re.compile(r'^(?:@[a-z0-9][a-z0-9._~-]*/)?[a-z0-9][a-z0-9._~-]*\Z',re.ASCII)#npm 包名
包名最大长度=214#npm 包名上限
数字='(?:0|[1-9]\\d*)'#SemVer 数字段
预发布段=f'(?:{数字}|\\d*[a-zA-Z-][0-9a-zA-Z-]*)'#预发布的一段
语义版本=re.compile(
    f'^{数字}\\.{数字}\\.{数字}(?:-{预发布段}(?:\\.{预发布段})*)?(?:\\+[0-9a-zA-Z-]+(?:\\.[0-9a-zA-Z-]+)*)?\\Z',
    re.ASCII,
)#一个精确版本的 SemVer 2.0.0
提交哈希=re.compile(r'^[0-9a-f]{40}\Z',re.ASCII)#小写 40 位提交
路径段=re.compile(r'^[A-Za-z0-9._@+-]+\Z',re.ASCII)#目录段
数据图标=re.compile(r'^data:(?:image/svg\+xml|image/png|image/jpeg|image/webp);base64,([A-Za-z0-9+/]*={0,2})\Z',re.ASCII)#内联图标
基64=re.compile(r'^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?\Z',re.ASCII)#标准 base64
最大内联图标字节=32*1024#内联 data 图标解码后载荷的上限
最大发布时间戳=10**11#发布秒须小于 10^11
仓库段=re.compile(r'^(?:/[^/]+){2,}\Z',re.ASCII)#至少两段、无空段
压缩包=re.compile(r'\.(?:tgz|tar\.gz)\Z',re.ASCII|re.IGNORECASE)#不是仓库
比较运算符=re.compile(r'^(?:<=|>=|<|>|=)\s*',re.ASCII)#范围比较符
部分版本=re.compile(
    r'v?(?:(?:0|[1-9]\d*)|[xX*])(?:\.(?:(?:0|[1-9]\d*)|[xX*])){0,2}'
    r'(?:-(?:(?:0|[1-9]\d*)|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:(?:0|[1-9]\d*)|\d*[a-zA-Z-][0-9a-zA-Z-]*))*)?'
    r'(?:\+[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*)?',
    re.ASCII,
)#范围里的部分或完整版本
连字符范围=re.compile(r'\s+-\s+',re.ASCII)#1.2.3 - 2.3.4
未提供=object()#键缺席，区别于 null

class 市场索引错误(Exception):#索引违反格式 1
    '索引违反格式 1；path 是违规值的 JSON 路径，例如 $.plugins[0].versions[1].version'
    def __init__(自身,路径,原因):#记下路径和规则
        '记下违规值的 JSON 路径和被违反的规则。规则文本按机器比对原样保留'
        super().__init__(路径+' '+原因)#消息是路径加规则
        自身.name='MarketIndexError'#错误名原样
        自身.path=路径#JSON 路径
        自身.reason=原因#规则原文

def 失败(路径,原因):#抛出第一条被违反的规则
    '抛出第一条被违反的规则'
    raise 市场索引错误(路径,原因)#不再继续校验

def 取对象(值,路径):#要求普通对象
    '要求普通 dict。数组、null 和其他类型都不是对象'
    if type(值) is not dict:#不是普通对象
        失败(路径,'must be an object')#规则原文
    return 值#原对象

def 取字符串(值,路径):#要求含非空白的字符串
    '要求含非空白字符的字符串，原文字不裁剪'
    if not isinstance(值,str) or 值.strip()=='':#不是字符串或只有空白
        失败(路径,'must be a string with a non-whitespace character')#规则原文
    return 值#原文

def 可选(对象,键,路径,读取):#缺席的键
    '键缺席时返回未提供，否则用读取函数解析'
    if 键 not in 对象:#没写这个键
        return 未提供#与 null 区分
    return 读取(对象[键],路径+'.'+键)#解析在场的值

def 定义自有(记录,键,值):#普通键
    '写入自有键，使 __proto__ 一类标识保持为普通键'
    记录[键]=值#dict 赋值不会走原型

def 读局部文本(值,路径):#字符串或语言表
    '读局部文本。对象的键必须是小写语言 id，且必须有 en'
    if isinstance(值,str):#一整句
        return 取字符串(值,路径)#不能只有空白
    对象=取对象(值,路径)#否则必须是对象
    文本={}#按语言
    for 语言,成员 in 对象.items():#每个语言
        if 语言标识.fullmatch(语言) is None:#键不是语言 id
            失败(路径+'.'+语言,'must be keyed by a lowercase language id')#规则原文
        定义自有(文本,语言,取字符串(成员,路径+'.'+语言))#该语言的文字
    if 'en' not in 文本:#没有英文
        失败(路径,'must contain en')#规则原文
    return 文本#语言表

def 声明表(值,路径,读取):#id 到声明
    '把对象读成 id 到声明的表。空 id 非法'
    结果={}#声明
    for 标识,成员 in 取对象(值,路径).items():#每个 id
        if 标识=='':#空 id
            失败(路径,'must not declare an empty id')#规则原文
        定义自有(结果,标识,读取(取对象(成员,路径+'.'+标识),路径+'.'+标识))#一条声明
    return 结果#表

def 一条声明(对象,路径):#类别或标签
    '读一条类别或标签声明'
    标题=对象['title'] if 'title' in 对象 else 未提供#标题缺席也要报规则
    return {'title':读局部文本(标题,路径+'.title')}#只有标题

def 排序键声明(对象,路径):#排序键
    '读一条排序键声明。方向只能是 asc 或 desc'
    if 对象.get('order')!='asc' and 对象.get('order')!='desc':#方向非法或缺失
        失败(路径+'.order','must be "asc" or "desc"')#规则原文
    标题=对象['title'] if 'title' in 对象 else 未提供#标题
    return {'title':读局部文本(标题,路径+'.title'),'order':对象['order']}#标题和方向

def 索引元数据(值,路径):#索引级声明
    '读索引级声明。缺席的分组填空表'
    对象={} if 值 is 未提供 else 取对象(值,路径)#缺席当空对象

    def 读类别声明(成员,位于):#类别表
        '把成员读成类别声明表'
        return 声明表(成员,位于,一条声明)#类别

    def 读标签声明(成员,位于):#标签表
        '把成员读成标签声明表'
        return 声明表(成员,位于,一条声明)#标签

    def 读排序声明(成员,位于):#排序键表
        '把成员读成排序键声明表'
        return 声明表(成员,位于,排序键声明)#排序键

    类别=可选(对象,'categories',路径,读类别声明)#类别
    标签=可选(对象,'labels',路径,读标签声明)#标签
    排序键=可选(对象,'sortKeys',路径,读排序声明)#排序键
    return {#缺席填空
        'categories':{} if 类别 is 未提供 else 类别,#类别
        'labels':{} if 标签 is 未提供 else 标签,#标签
        'sortKeys':{} if 排序键 is 未提供 else 排序键,#排序键
    }#元数据结束

def 已声明标识(值,路径,已声明):#引用必须存在
    '读一个已声明的 id。未声明的 id 按 JSON 字符串写进规则'
    标识=取字符串(值,路径)#id 本身
    if 标识 not in 已声明:#没声明
        失败(路径,'references undeclared id '+json.dumps(标识,ensure_ascii=False))#带引号的 id
    return 标识#通过

def 是有限数(值):#排序值
    '是有限数。布尔不是数'
    if isinstance(值,bool) or not isinstance(值,(int,float)):#不是数
        return False#拒绝
    return math.isfinite(值)#排除 nan 和无穷

def 插件元数据(值,路径,索引):#一个插件的市场值
    '读一个插件的市场值。缺席的关键词、标签和排序键填空'
    对象={} if 值 is 未提供 else 取对象(值,路径)#缺席当空对象

    def 读类别(成员,位于):#类别 id
        '读已声明的类别 id'
        return 已声明标识(成员,位于,索引['categories'])#必须已声明

    def 读关键词(成员,位于):#自由字符串
        '读字符串数组，保留顺序、重复和空串'
        if type(成员) is not list:#不是数组
            失败(位于,'must be an array')#规则原文
        结果=[]#关键词
        for 序号,词 in enumerate(成员):#逐个
            if not isinstance(词,str):#不是字符串
                失败(位于+'['+str(序号)+']','must be a string')#规则原文
            结果.append(词)#原样，含空串
        return 结果#保持顺序

    def 读标签(成员,位于):#标签 id
        '读已声明且不重复的标签 id'
        if type(成员) is not list:#不是数组
            失败(位于,'must be an array')#规则原文
        标识表=[]#标签
        for 序号,标签 in enumerate(成员):#逐个
            标识表.append(已声明标识(标签,位于+'['+str(序号)+']',索引['labels']))#必须已声明
        if len(set(标识表))!=len(标识表):#重复
            失败(位于,'must not repeat a label')#规则原文
        return 标识表#通过

    def 读排序值(成员,位于):#排序数
        '读已声明排序键上的有限数'
        值表={}#id 到数
        for 标识,排序值 in 取对象(成员,位于).items():#每个键
            已声明标识(标识,位于+'.'+标识,索引['sortKeys'])#必须已声明
            if not 是有限数(排序值):#不是有限数
                失败(位于+'.'+标识,'must be a finite number')#规则原文
            定义自有(值表,标识,排序值)#普通键
        return 值表#排序值

    类别=可选(对象,'category',路径,读类别)#可选
    关键词=可选(对象,'keywords',路径,读关键词)#缺席为空数组
    标签=可选(对象,'labels',路径,读标签)#缺席为空数组
    排序键=可选(对象,'sortKeys',路径,读排序值)#缺席为空表
    结果={}#按字段顺序
    if 类别 is not 未提供:#写了类别
        结果['category']=类别#放在最前
    结果['keywords']=[] if 关键词 is 未提供 else 关键词#关键词
    结果['labels']=[] if 标签 is 未提供 else 标签#标签
    结果['sortKeys']={} if 排序键 is 未提供 else 排序键#排序键
    return 结果#插件元数据

def 解析绝对(文本):#浏览器绝对网址
    '解析绝对网址。http(s) 必须有主机；坏主机抛出'
    部分=urlparse(文本)#拆开
    方案=部分.scheme.lower()#方案小写
    if 方案=='':#相对
        raise ValueError('不是绝对网址')#不能解析
    主机=''#非 http 可以没有
    端口=None#默认端口
    用户=部分.username or ''#用户
    密码=部分.password or ''#密码
    if 方案 in ('http','https'):#必须有主机
        try:
            主机=部分.hostname or ''#主机
            端口=部分.port#端口
        except ValueError as 错误:
            raise ValueError('不是绝对网址') from 错误#坏的主机或端口
        if 主机=='':#没有主机
            raise ValueError('不是绝对网址')#例如 https://[
        主机=主机.lower()#主机小写
    路径=部分.path#路径
    if 方案 in ('http','https') and 路径=='':#浏览器会补 /
        路径='/'#空路径
    return {#校验用的字段
        'protocol':方案+':',#带冒号
        'username':用户,#空串表示没有
        'password':密码,#空串表示没有
        'pathname':路径,#路径
        'href':规范形式(文本,部分,方案,主机,端口,路径),#规范链接
    }#解析结束

def 规范形式(文本,部分,方案,主机,端口,路径):#浏览器 href
    '序列化成浏览器的 href。主机小写，默认端口省略，空的查询和片段仍保留记号'
    if 方案=='file':#文件网址
        if 部分.path.startswith('/'):#绝对文件路径
            return 'file://'+部分.path#三斜杠
        return 'file:'+部分.path#其他 file
    if 方案 not in ('http','https'):#javascript 等原样
        return 文本#不做规范比较
    if 端口 is None or (方案=='https' and 端口==443) or (方案=='http' and 端口==80):#默认端口
        主机段=主机#不写端口
    else:#非默认端口
        主机段=主机+':'+str(端口)#写上端口
    用户段=''#无凭据
    if 部分.username:#有用户
        用户段=部分.username#用户
        if 部分.password is not None:#有密码
            用户段+=':'+部分.password#密码
        用户段+='@'#分隔
    链接=方案+'://'+用户段+主机段+路径#主体
    井号前=文本.split('#',1)[0]#片段之前
    if '?' in 井号前:#含空查询
        链接+='?'+部分.query#保留问号
    if '#' in 文本:#含空片段
        链接+='#'+部分.fragment#保留井号
    return 链接#规范 href

def 取源(文本):#图标是否落在索引源
    'http(s) 的源；其他方案是 null。默认端口省略'
    部分=urlparse(文本)#拆开
    方案=部分.scheme.lower()#方案
    if 方案 not in ('http','https'):#file 等
        return 'null'#不透明源
    try:
        主机=部分.hostname#主机
        端口=部分.port#端口
    except ValueError:
        return 'null'#坏网址
    if not 主机:#没有主机
        return 'null'#不透明源
    主机=主机.lower()#小写
    if 端口 is not None and not ((方案=='http' and 端口==80) or (方案=='https' and 端口==443)):#非默认端口
        return 方案+'://'+主机+':'+str(端口)#带端口
    return 方案+'://'+主机#源

def 网页网址(值,路径,协议表):#绝对 http(s)，无凭据、查询、片段
    '读绝对网址。协议必须是给出的那几个，且不能有凭据、查询或片段'
    文本=取字符串(值,路径)#先是字符串
    try:
        网址=解析绝对(文本)#绝对网址
    except ValueError:
        失败(路径,'must be an absolute URL')#规则原文，不用解析器的消息
    if 网址['protocol'] not in 协议表:#协议不对
        失败(路径,'must use '+' or '.join(协议表))#规则原文
    if 网址['username']!='' or 网址['password']!='':#有凭据
        失败(路径,'must not contain credentials')#规则原文
    if '?' in 网址['href'] or '#' in 网址['href']:#查询或片段
        失败(路径,'must not contain a query or fragment')#规则原文
    return 网址#含规范 href

def 主页网址(值,路径):#允许查询和片段
    '读主页。npm homepage 常带 #readme，所以保留片段和查询'
    文本=取字符串(值,路径)#字符串
    try:
        网址=解析绝对(文本)#必须绝对
    except ValueError:
        失败(路径,'must be an absolute URL')#规则原文
    if 网址['protocol'] not in ('https:','http:'):#只能 http(s)
        失败(路径,'must use https: or http:')#规则原文
    return 网址['href']#规范链接，保留片段

def git网址(值,路径):#规范 https 仓库
    '读 Git 仓库网址：规范 https，至少两段路径，且不是压缩包'
    网址=网页网址(值,路径,('https:',))#只允许 https，且无查询片段
    if 网址['href']!=值:#主机大小写等差异
        失败(路径,'must be a canonical URL')#规则原文
    if 仓库段.fullmatch(网址['pathname']) is None:#段数不够或有空段
        失败(路径,'must name a repository with at least two path segments')#规则原文
    if 压缩包.search(网址['pathname']) is not None:#tgz 或 tar.gz
        失败(路径,'must name a repository, not a tarball')#规则原文
    return 网址['href']#规范链接

def 包路径(值,路径):#相对目录
    '读相对目录。段只能是字母、数字和 ._@+-，不能是 . 或 ..'
    文本=取字符串(值,路径)#字符串
    for 段 in 文本.split('/'):#逐段
        if 段=='.' or 段=='..' or 路径段.fullmatch(段) is None:#非法段
            失败(路径,'must be a relative directory of letters, digits, and ._@+- segments without . or ..')#规则原文
    return 文本#原文

def 读仓库(值,路径):#展示用仓库
    '读展示用仓库。丢掉 type 等格式未定义的成员'
    对象=取对象(值,路径)#对象
    网址=网页网址(对象['url'] if 'url' in 对象 else 未提供,路径+'.url',('https:','http:'))['href']#网页
    目录=可选(对象,'directory',路径,包路径)#可选目录
    结果={'url':网址}#网址在前
    if 目录 is not 未提供:#写了目录
        结果['directory']=目录#接上
    return 结果#仓库

def 读来源(值,路径):#npm 或 git
    '读一个精确版本的安装来源'
    对象=取对象(值,路径)#对象
    种类=对象.get('type')#判别
    if 种类=='npm':#注册表
        def 读注册表(成员,位于):#可选注册表
            '读 http(s) 注册表的规范网址'
            return 网页网址(成员,位于,('https:','http:'))['href']#无凭据、查询、片段
        注册表=可选(对象,'registry',路径,读注册表)#没配置就不写
        结果={'type':'npm'}#类型在前
        if 注册表 is not 未提供:#写了注册表
            结果['registry']=注册表#规范 href
        return 结果#npm
    if 种类=='git':#提交
        提交=取字符串(对象['commit'] if 'commit' in 对象 else 未提供,路径+'.commit')#提交
        if 提交哈希.fullmatch(提交) is None:#不是 40 位小写
            失败(路径+'.commit','must be a lowercase 40-hex-digit commit SHA')#规则原文
        包目录=可选(对象,'path',路径,包路径)#可选目录
        结果={'type':'git','url':git网址(对象['url'] if 'url' in 对象 else 未提供,路径+'.url'),'commit':提交}#仓库与提交
        if 包目录 is not 未提供:#写了目录
            结果['path']=包目录#接上
        return 结果#git
    失败(路径+'.type','must be "npm" or "git"')#其他类型

def 是语义版本范围(文本):#semver.validRange 是否接受
    '文本是否是 SemVer 范围。空串表示任意版本；坏的比较器拒绝'
    文本=文本.strip()#两端空白
    if 文本=='':#node 把空范围当成任意
        return True#接受
    for 或组 in 文本.split('||'):#或
        if not 解析与组(或组):#其中一组坏了
            return False#整个范围拒绝
    return True#每组都能解析

def 解析与组(文本):#空白隔开的比较器
    '解析一组用空白隔开的比较器，含波浪、插入和连字符范围'
    剩余=文本.strip()#这一组
    if 剩余=='':#空的或组
        return False#拒绝
    while 剩余!='':#还有比较器
        if 剩余[0] in '<>=':#比较符
            匹配=比较运算符.match(剩余)#运算符
            if 匹配 is None:#不是完整运算符
                return False#拒绝
            剩余=剩余[匹配.end():]#运算符之后
            版本=部分版本.match(剩余)#版本
            if 版本 is None:#没有版本
                return False#拒绝
            剩余=剩余[版本.end():].strip()#下一个比较器
            continue#继续
        if 剩余.startswith('~>'):#~> 当波浪
            剩余=剩余[2:].lstrip()#去掉标记
        elif 剩余[0] in '~^':#波浪或插入
            剩余=剩余[1:].lstrip()#去掉标记
        else:#普通版本或连字符
            版本=部分版本.match(剩余)#左端
            if 版本 is None:#不是版本
                return False#拒绝
            之后=剩余[版本.end():]#剩下的
            连=连字符范围.match(之后)#空格-空格
            if 连 is not None:#连字符范围
                右=部分版本.match(之后[连.end():])#右端
                if 右 is None:#右端不是版本
                    return False#拒绝
                剩余=之后[连.end()+右.end():].strip()#这一组的下一个
                continue#继续
            if 之后!='' and not 之后[0].isspace():#版本后紧贴着垃圾
                return False#拒绝
            剩余=之后.strip()#下一个比较器
            continue#继续
        版本=部分版本.match(剩余)#波浪或插入后面的版本
        if 版本 is None:#没有版本
            return False#拒绝
        剩余=剩余[版本.end():].strip()#下一个比较器
    return True#这一组通过

def 读引擎(值,路径):#只留 dsh
    '读运行时要求。只保留 dsh，且不能是 workspace: 范围'
    对象=取对象(值,路径)#对象

    def 读范围(成员,位于):#dsh 范围
        '读 SemVer 范围，拒绝 workspace:'
        范围=取字符串(成员,位于)#字符串
        if 范围.startswith('workspace:'):#工作区范围
            失败(位于,'must not be a workspace: range')#规则原文
        if not 是语义版本范围(范围):#不是 SemVer 范围
            失败(位于,'must be a SemVer range')#规则原文
        return 范围#原文

    范围=可选(对象,'dsh',路径,读范围)#可选
    if 范围 is 未提供:#没写 dsh
        return {}#任意版本
    return {'dsh':范围}#只留 dsh

def 图标(值,路径,索引链接):#data 或绝对网址
    '读图标。data 网址校验 base64 与 32KiB；相对引用相对索引网址解析'
    文本=取字符串(值,路径)#字符串
    if 文本.startswith('data:'):#内联
        匹配=数据图标.fullmatch(文本)#类型与载荷
        载荷=None if 匹配 is None else 匹配.group(1)#base64
        if 载荷 is None or 载荷=='' or 基64.fullmatch(载荷) is None:#类型或编码不对
            失败(路径,'must be a base64 SVG, PNG, JPEG, or WebP data URL')#规则原文
        if 载荷.endswith('=='):#两个填充
            填充=2#减两字节
        elif 载荷.endswith('='):#一个填充
            填充=1#减一字节
        else:#无填充
            填充=0#不减
        字节数=len(载荷)/4*3-填充#解码后的字节估计
        if 字节数>最大内联图标字节:#超过 32KiB
            失败(路径,'must not exceed '+str(最大内联图标字节//1024)+' KiB of decoded bytes')#规则原文
        return 文本#原 data 网址
    try:
        绝对=urljoin(索引链接,文本)#相对索引
        解析=解析绝对(绝对)#必须能解析
    except ValueError:
        失败(路径,'must be a URL reference')#规则原文
    if 解析['protocol']!='https:' and (取源(绝对)=='null' or 取源(绝对)!=取源(索引链接)):#不是 https，也不是索引源
        失败(路径,'must resolve to https or the index origin')#规则原文
    return 解析['href']#绝对链接

def 是整数秒(值):#发布时间
    '是非布尔的整数。整值浮点收成 int'
    if isinstance(值,bool):#布尔不是整数秒
        return None#拒绝
    if isinstance(值,int):#整数
        return 值#原值
    if isinstance(值,float) and math.isfinite(值) and 值.is_integer():#1.0 这类
        return int(值)#收成整数
    return None#不是整数

def 读市场版本(值,路径):#一个版本
    '读一个精确版本：SemVer、Unix 秒、来源和引擎'
    对象=取对象(值,路径)#对象
    版本=取字符串(对象['version'] if 'version' in 对象 else 未提供,路径+'.version')#版本串
    if 语义版本.fullmatch(版本) is None:#不是精确 SemVer
        失败(路径+'.version','must be an exact SemVer version')#规则原文
    发布时间=是整数秒(对象.get('publishTimestamp',未提供) if 'publishTimestamp' in 对象 else 未提供)#秒
    if 发布时间 is None or 发布时间<0 or 发布时间>=最大发布时间戳:#不在区间
        失败(路径+'.publishTimestamp','must be an integer number of Unix seconds in [0, 10^11)')#规则原文
    来源=读来源(对象['source'] if 'source' in 对象 else 未提供,路径+'.source')#来源
    引擎=可选(对象,'engines',路径,读引擎)#可选
    return {#字段顺序
        'version':版本,#精确版本
        'publishTimestamp':发布时间,#秒
        'source':来源,#安装来源
        'engines':{} if 引擎 is 未提供 else 引擎,#缺席为空对象
    }#版本结束

def 预发布键(段):#一段预发布的比较键
    '数字段低于非数字段'
    if 段.isdigit():#纯数字
        return (0,int(段))#数值比较，且低于文字
    return (1,段)#文字按码位

def 版本序(版本):#SemVer 优先级
    'SemVer 优先级元组。构建元数据不参与；发行版高于同号预发布'
    无构建=版本.split('+',1)[0]#丢掉构建
    if '-' in 无构建:#有预发布
        核心,预发布=无构建.split('-',1)#核心与预发布
        预段=[]#逐段
        for 段 in 预发布.split('.'):#预发布段
            预段.append(预发布键(段))#比较键
        发行=0#预发布更低
    else:#发行版
        核心=无构建#没有预发布
        预段=[]#空
        发行=1#高于预发布
    号=核心.split('.')#主、次、修
    return (int(号[0]),int(号[1]),int(号[2]),发行,tuple(预段))#优先级

def 版本序键(条目):#排序键
    '供降序排列使用的优先级'
    return 版本序(条目['version'])#只看版本串

def 版本表(值,路径):#非空且降序
    '读非空版本数组，拒绝重复，并按 SemVer 优先级降序排列'
    if type(值) is not list or len(值)==0:#空或不是数组
        失败(路径,'must be a non-empty array')#规则原文
    见到=set()#已经见过的版本串
    已解析=[]#版本
    for 序号,成员 in enumerate(值):#保持输入位置以便报路径
        位于=路径+'['+str(序号)+']'#这一项
        条目=读市场版本(成员,位于)#校验
        if 条目['version'] in 见到:#重复
            失败(位于+'.version','duplicates '+条目['version'])#规则原文
        见到.add(条目['version'])#记下
        已解析.append(条目)#收下
    已解析.sort(key=版本序键,reverse=True)#优先级高的在前
    return 已解析#降序

def 读插件(值,路径,索引,索引链接):#一个插件
    '读一个插件。丢掉格式未定义的成员'
    对象=取对象(值,路径)#对象
    名称=取字符串(对象['name'] if 'name' in 对象 else 未提供,路径+'.name')#包名
    if len(名称)>包名最大长度 or 包名.fullmatch(名称) is None:#不是合法包名
        失败(路径+'.name','must be a valid npm package name')#规则原文
    标题=可选(对象,'title',路径,读局部文本)#可选
    简介=可选(对象,'description',路径,读局部文本)#可选
    def 读图标(成员,位于):#相对索引解析
        '把图标相对索引网址解析'
        return 图标(成员,位于,索引链接)#data 或绝对网址
    图标值=可选(对象,'icon',路径,读图标)#可选
    作者=可选(对象,'author',路径,取字符串)#可选
    主页=可选(对象,'homepage',路径,主页网址)#可选
    仓库=可选(对象,'repository',路径,读仓库)#可选
    结果={'name':名称}#包名在前
    if 标题 is not 未提供:#有标题
        结果['title']=标题#接上
    if 简介 is not 未提供:#有简介
        结果['description']=简介#接上
    if 图标值 is not 未提供:#有图标
        结果['icon']=图标值#已是绝对或 data
    if 作者 is not 未提供:#有作者
        结果['author']=作者#接上
    if 主页 is not 未提供:#有主页
        结果['homepage']=主页#接上
    if 仓库 is not 未提供:#有仓库
        结果['repository']=仓库#接上
    元数据值=对象['metadata'] if 'metadata' in 对象 else 未提供#缺席填空
    结果['metadata']=插件元数据(元数据值,路径+'.metadata',索引)#市场值
    版本值=对象['versions'] if 'versions' in 对象 else 未提供#必须有
    结果['versions']=版本表(版本值,路径+'.versions')#降序
    return 结果#插件

def 解析市场索引(值,索引网址):#校验格式 1
    """校验解析后的格式 1 索引。格式未定义的成员忽略并丢掉。
    缺席的元数据分组和列表填空，每个插件的版本按 SemVer 优先级降序，相对图标换成绝对网址。
    第一条被违反的规则抛市场索引错误"""
    try:
        基址=解析绝对(索引网址)#索引本身必须是绝对网址
    except ValueError:
        失败('$','index URL '+json.dumps(索引网址,ensure_ascii=False)+' must be an absolute URL')#规则原文
    对象=取对象(值,'$')#根必须是对象
    格式=对象['format'] if 'format' in 对象 else 未提供#格式
    if isinstance(格式,bool) or 格式!=1:#只能是数字 1
        失败('$.format','must be 1')#规则原文
    元数据值=对象['metadata'] if 'metadata' in 对象 else 未提供#可缺席
    元数据=索引元数据(元数据值,'$.metadata')#声明
    插件值=对象['plugins'] if 'plugins' in 对象 else 未提供#必须是数组
    if type(插件值) is not list:#不是数组
        失败('$.plugins','must be an array')#规则原文
    名称集=set()#包名
    插件表=[]#插件
    for 序号,条目 in enumerate(插件值):#默认顺序
        位于='$.plugins['+str(序号)+']'#这一项
        已解析=读插件(条目,位于,元数据,基址['href'])#校验并解析图标
        if 已解析['name'] in 名称集:#包名重复
            失败(位于+'.name','duplicates '+已解析['name'])#规则原文
        名称集.add(已解析['name'])#记下
        插件表.append(已解析)#保持输入顺序
    标题=读局部文本(对象['title'] if 'title' in 对象 else 未提供,'$.title')#标题必填
    简介=可选(对象,'description','$',读局部文本)#可选
    结果={'format':1,'title':标题}#格式和标题
    if 简介 is not 未提供:#有简介
        结果['description']=简介#插在元数据前
    结果['metadata']=元数据#声明
    结果['plugins']=插件表#插件
    return 结果#校验后的索引

def 市场安装目标(名称,版本):#pnpm 说明
    '安装一个精确版本：npm 是 name@version；Git 是钉住提交的 git+https，包目录带 path:'
    来源=版本['source']#已校验的来源
    if 来源['type']=='npm':#注册表
        结果={'spec':名称+'@'+版本['version']}#精确版本
        if 'registry' in 来源:#指定了注册表
            结果['registry']=来源['registry']#先问它
        return 结果#npm
    仓库=来源['url'] if 来源['url'].endswith('.git') else 来源['url']+'.git'#补 .git
    路径段='' if 'path' not in 来源 else '&path:/'+来源['path']#pnpm 的 path 参数
    return {'spec':'git+'+仓库+'#'+来源['commit']+路径段}#钉住提交
