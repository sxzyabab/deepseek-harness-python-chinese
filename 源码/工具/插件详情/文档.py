'插件详情文档的选择：显示语言里 locale 的 meta.detail 指向的 Markdown，否则是包的 README；以及文档旁边的图片'
import json#locale 文件
import posixpath#图片路径按 POSIX 折叠，不随宿主分隔符变化
import re#语言、路径与 front matter
from urllib.parse import unquote_to_bytes#百分号解码
from typing import Literal,TypedDict#文档记录
from .文件 import 详情失败,拼接路径#失败与相对路径

__all__=[#仅中文公开名
    '语言链','取markdown','包文档','读包文档','详情图片',
]#公开面结束

语言标识=re.compile(r'^[a-z]{2,8}(?:-[a-z0-9]{1,8})*\Z',re.ASCII)#小写 BCP 47
地区名=re.compile(r'^([a-z]{2,3})-([a-z]{2})\Z',re.ASCII)#两字母地区
方案=re.compile(r'^[A-Za-z][A-Za-z\d+.-]*:',re.ASCII)#URL scheme
markdown后缀=re.compile(r'\.(?:md|markdown)\Z',re.ASCII|re.IGNORECASE)#Markdown 后缀
前导物料=re.compile(r'^---\r?\n.*?\r?\n---[ \t]*(?:\r?\n|\Z)',re.ASCII|re.DOTALL)#开头的 YAML front matter
查询片段=re.compile(r'[?#].*\Z',re.ASCII|re.DOTALL)#图片地址上的查询和片段
百分号坏=re.compile(r'%(?![0-9A-Fa-f]{2})',re.ASCII)#不是两位十六进制的百分号
未提供=object()#键缺席，区别于 JSON null

图片类型={#小写后缀到媒体类型
    '.png':'image/png',
    '.jpg':'image/jpeg',
    '.jpeg':'image/jpeg',
    '.gif':'image/gif',
    '.webp':'image/webp',
    '.avif':'image/avif',
    '.svg':'image/svg+xml',
}#只服务这几种

def 语言链(语言):#文档按这个顺序挑选
    '文档选用的语言：该语言、每个更短的前缀，然后是英文。不是语言 id 时抛出'
    标识=语言.lower()#比较用小写
    if 语言标识.fullmatch(标识) is None:#不是语言 id
        raise ValueError('Not a language id: '+语言)#原文保留，调用方按这句比对
    段=标识.split('-')#语言和地区
    链=[]#从最长到最短
    下标=0#丢掉的尾段数
    while 下标<len(段):#每个前缀
        链.append('-'.join(段[:len(段)-下标]))#当前前缀
        下标+=1#再短一截
    链.append('en')#最后是英文
    结果=[]#去重且保持顺序
    for 项 in 链:#逐个
        if 项 not in 结果:#还没有
            结果.append(项)#按首次出现
    return 结果#最具体的在前

def 详情路径(值,标签):#校验 meta.detail
    '校验 locale 的 meta.detail：相对包内、以 / 分隔、以 Markdown 结尾的路径。缺席时没有返回'
    if 值 is 未提供:#文件没写这个字段
        return None#换下一种语言
    if not isinstance(值,str) or 值.strip()=='':#空或不是字符串
        raise 详情失败('invalid',标签+' must be a non-empty string')#规则原文
    if '\\' in 值 or 方案.match(值) is not None:#反斜杠或 scheme
        raise 详情失败('invalid',标签+' must be a relative path inside the package')#规则原文
    for 段 in 值.split('/'):#逐段
        if 段=='' or 段=='.' or 段=='..':#空段、. 或 ..
            raise 详情失败('invalid',标签+' must be a relative path inside the package')#规则原文
    if markdown后缀.search(值) is None:#不是 Markdown
        raise 详情失败('invalid',标签+' must name a Markdown file')#规则原文
    return 值#通过

def 地区大写(语言):#zh-cn 同时试 zh-CN
    '两字母地区改成大写；对不上的名字原样返回'
    匹配=地区名.fullmatch(语言)#语言-地区
    if 匹配 is None:#不是这种形式
        return 语言#只有原名
    return 匹配.group(1)+'-'+匹配.group(2).upper()#地区大写

def 地区详情(文件,目录,语言表,最大字节,信号):#沿语言链找 meta.detail
    '沿语言链读 locale/<语言>.json，返回第一个声明的 meta.detail'
    for 语言 in 语言表:#最具体的优先
        名称集=[]#小写名，以及两字母地区的大写名
        for 名 in (语言,地区大写(语言)):#两种拼写
            if 名 not in 名称集:#去重
                名称集.append(名)#保持顺序
        for 名 in 名称集:#先小写，再大写地区
            路径=拼接路径(目录,'locale/'+名+'.json')#locale 文件
            字节=文件.读取(路径,最大字节,信号)#读文件
            if 字节 is None:#没有这份
                continue#试下一个拼写
            try:
                解析=json.loads(字节.decode('utf-8',errors='replace'))#对齐 TextDecoder 的替换
            except json.JSONDecodeError as 错误:
                raise 详情失败('invalid',路径+': '+str(错误)) from 错误#坏的 locale 文件
            if type(解析) is dict and 'meta' in 解析:#有 meta
                元=解析['meta']#可能不是对象
            else:
                元=未提供#null、数组或没有 meta
            if type(元) is dict and 'detail' in 元:#写了 detail
                详情值=元['detail']#交给校验，null 也会失败
            else:
                详情值=未提供#这份 locale 没有详情
            详情=详情路径(详情值,路径+': meta.detail')#校验
            if 详情 is not None:#声明了合法路径
                return 详情#用它
            break#文件在，但没有详情：不再试同一语言的另一种大小写
    return None#链上没有语言声明详情

def 取markdown(字节):#解码文档
    '把 Markdown 解成 UTF-8 文本，去掉字节顺序标记和开头的 YAML front matter'
    文本=字节.decode('utf-8',errors='replace')#畸形字节换成 U+FFFD
    if 文本.startswith('\ufeff'):#BOM
        文本=文本[1:]#去掉
    return 前导物料.sub('',文本,count=1)#只去掉开头那一块

class 包文档(TypedDict):#一份包的详情文档
    '一份包的详情文档'
    origin:Literal['locale','readme']#locale 是 meta.detail 指向的文件，readme 是包的 README
    path:str#文档在文件来源里的 / 分隔路径
    markdown:str#取markdown 解码后的文本

def 读包文档(文件,目录,语言表,最大字节,信号):#选详情文档
    '读包的详情文档：语言链上第一个 meta.detail 指向的 Markdown，否则 README。两者都没有时没有返回'
    详情=地区详情(文件,目录,语言表,最大字节,信号)#locale
    if 详情 is not None:#有声明
        路径=拼接路径(目录,详情)#相对文件根
        字节=文件.读取(路径,最大字节,信号)#读被点名的文件
        if 字节 is None:#点名的文件不存在
            raise 详情失败('invalid',f'{路径}，由 meta.detail 指定，不存在')#不改去读 README
        return {'origin':'locale','path':路径,'markdown':取markdown(字节)}#locale 文档
    自述=文件.读自述(目录,最大字节,信号)#退到 README
    if 自述 is None:#也没有
        return None#包没有详情
    return {'origin':'readme','path':自述['path'],'markdown':取markdown(自述['bytes'])}#README 文档

def 解码组件(文本):#decodeURIComponent
    '按百分号解码。损坏的转义或非法 UTF-8 抛出'
    if 百分号坏.search(文本) is not None:#不是两位十六进制
        raise ValueError('百分号转义损坏')#这份目标不指向文件
    try:
        return unquote_to_bytes(文本).decode('utf-8')#按 UTF-8 严格解码
    except UnicodeDecodeError as 错误:
        raise ValueError('百分号转义损坏') from 错误#半截序列

def 详情图片(文档,写成):#文档里写的图片目标
    '解析文档写出的图片目标。相对该文档；以 / 开头则相对文件根。查询和片段忽略。坏目标、跑出根或其他类型没有返回'
    try:
        解码=解码组件(查询片段.sub('',写成))#先去掉查询和片段
    except ValueError:
        return None#坏的百分号不指向文件
    if '\\' in 解码 or '\0' in 解码:#反斜杠或空字符
        return None#拒绝
    if 解码.startswith('/'):#相对文件根
        合并=解码[1:]#去掉开头的 /
    else:#相对文档
        合并=posixpath.join(posixpath.dirname(文档),解码)#接在文档目录后
    路径=posixpath.normpath(合并)#折叠 . 与 ..
    if 路径=='.' or 路径.startswith('../') or 路径=='..' or posixpath.isabs(路径):#根自己或跑出去
        return None#不是图片
    媒体=图片类型.get(posixpath.splitext(路径)[1].lower())#按小写后缀
    if 媒体 is None:#不是那六种
        return None#不服务
    return {'path':路径,'mediaType':媒体}#路径保持原来的大小写
