'校验后的插件市场索引记录。title 与 description 是局部文本：字符串，或含 en 的语言表。包清单未导出 LocalizedText'
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=[#仅中文公开名
    '市场声明','市场排序键声明','市场索引元数据','市场插件元数据','市场仓库',
    '市场npm来源','市场git来源','市场来源','市场引擎','市场版本','市场插件','市场索引','市场安装目标',
]#公开面结束

class 市场声明(TypedDict):#市场声明的类别或标签
    '市场声明的类别或标签：不透明 id 的展示标题'
    title:str|dict#局部文本

class 市场排序键声明(TypedDict):#市场声明的排序键
    '市场声明的排序键：展示标题与初始方向'
    title:str|dict#局部文本
    order:Literal['asc','desc']#初始方向

class 市场索引元数据(TypedDict):#市场定义的声明
    '市场定义的声明；缺席的分组是空表'
    categories:dict#类别 id 到声明
    labels:dict#标签 id 到声明
    sortKeys:dict#排序键 id 到声明

class 市场插件元数据(TypedDict):#一个插件的市场定义值
    '一个插件的市场定义值；类别、标签与排序键 id 必须已在索引中声明'
    category:NotRequired[str]#类别 id
    keywords:list#自由字符串；缺席输入变成空数组
    labels:list#标签 id
    sortKeys:dict#排序键 id 到有限数

class 市场仓库(TypedDict):#源码发布位置，只用于展示
    '插件源码的发布位置；只用于展示，从不是安装来源'
    url:str#仓库网页的绝对 http(s) 网址，无凭据、查询或片段
    directory:NotRequired[str]#仓库内的相对 POSIX 目录；缺席表示仓库根

class 市场npm来源(TypedDict):#从 npm 安装
    '从 npm 安装的一个精确版本'
    type:Literal['npm']#npm
    registry:NotRequired[str]#http(s) 注册表；缺席表示安装客户端已配置的注册表

class 市场git来源(TypedDict):#从 Git 提交安装
    '从 Git 提交安装的一个精确版本'
    type:Literal['git']#git
    url:str#规范的 https 仓库网址
    commit:str#小写 40 位十六进制提交
    path:NotRequired[str]#相对 POSIX 包目录；缺席表示仓库根

市场来源=市场npm来源|市场git来源#一个精确版本的安装来源

class 市场引擎(TypedDict,total=False):#运行时要求
    '一个版本的运行时要求'
    dsh:str#该版本能跑的 DSH SemVer 范围；缺席表示任意 DSH 版本

class 市场版本(TypedDict):#一个可安装版本
    '插件的一个可安装版本'
    version:str#精确 SemVer，在该插件内唯一
    publishTimestamp:int#version 的发布时间，Unix 秒
    source:市场来源#安装来源
    engines:市场引擎#运行时要求

class 市场插件(TypedDict):#一个可安装组合包
    '一个可安装组合包及其列出的版本'
    name:str#npm 包名，在索引内唯一
    title:NotRequired[str|dict]#局部文本
    description:NotRequired[str|dict]#局部文本
    icon:NotRequired[str]#data 网址或已解析的绝对网址
    author:NotRequired[str]#作者
    homepage:NotRequired[str]#关于插件的绝对 http(s) 网址
    repository:NotRequired[市场仓库]#源码仓库网页与包目录，只用于展示
    metadata:市场插件元数据#市场定义值
    versions:list#非空，按 SemVer 优先级降序

class 市场索引(TypedDict):#一份格式 1 索引
    '一份校验过的格式 1 索引；格式未定义的成员已丢掉'
    format:Literal[1]#格式版本
    title:str|dict#局部文本
    description:NotRequired[str|dict]#局部文本
    metadata:市场索引元数据#声明
    plugins:list#插件，保持索引的默认顺序

class 市场安装目标(TypedDict):#安装一个精确版本的参数
    '安装一个精确版本的参数'
    spec:str#pnpm add 接受的安装说明
    registry:NotRequired[str]#首先询问的注册表；缺席表示安装客户端已配置的注册表
