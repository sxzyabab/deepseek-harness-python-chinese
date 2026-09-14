from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=[#仅中文公开名
    '配置档补丁重载','组合包清单','配置档清单','客户端清单',
    '引擎清单','清单','包清单',
]#公开面结束

配置档补丁重载=Literal['live','startup']#用户补丁在配置档存活期间热重载，或仅启动时应用

class 组合包清单(TypedDict):#组合包导出的配置层
    """组合包导出的配置层。"""
    patch:str#相对声明包根的补丁文件路径

class 配置档清单(TypedDict,total=False):#配置档目录声明的组合包合成
    """配置档目录声明的组合包合成。"""
    bundles:list#有序组合包层列表，使用已安装包名
    patchReload:配置档补丁重载#用户补丁生命周期；省略则自定义配置档为 live

class 客户端清单(TypedDict):#客户端模块与构建读取的客户端声明
    """客户端模块与构建读取的客户端声明。"""
    platform:str#客户端平台标识；Web 消费方选 web
    inject:NotRequired[list]#信息性包名依赖，不是 Cordis 服务注入
    immediately:NotRequired[bool]#启动第一阶段登记屏障；缺席表示共享应用批次
    external:NotRequired[list]#基线之外的精确模块表请求，含 <pkg>/client 等子路径；缺席表示仅基线 external

class 引擎清单(TypedDict,total=False):#package.json.engines 下的运行时版本要求
    """`package.json.engines` 下的运行时版本要求。"""
    dsh:str#兼容的 DSH 版本，SemVer 范围
    node:str#兼容的 Node.js 版本
    npm:str#兼容的 npm 版本

class 清单(TypedDict,total=False):#npm 清单的 dsh 属性；一包可声明多种角色
    """npm 清单的 `dsh` 属性；一包可声明多种角色。"""
    manifestVersion:Literal[1]#清单格式版本，独立于 npm 包与 Session 格式版本
    bundle:组合包清单#配置档启动器消费的组合包元数据
    profile:配置档清单#配置档启动器消费的配置档元数据
    client:客户端清单#客户端模块加载与构建元数据

class 包清单(TypedDict):#包身份与元数据；本地配置档读取方可接受部分声明
    """包身份与元数据。"""
    name:str#已发布 npm 包名
    version:str#已发布 npm 包版本
    description:NotRequired[str]#供发现与展示用的包摘要
    private:NotRequired[bool]#阻止 npm 发布
    dependencies:NotRequired[dict]#与本包一并安装的包
    peerDependencies:NotRequired[dict]#由消费方项目提供的包的兼容版本
    engines:NotRequired[引擎清单]#运行时要求
    dsh:NotRequired[清单]#DSH 专用作者声明
