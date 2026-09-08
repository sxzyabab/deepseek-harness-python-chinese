"""`package.json.dsh` 共享声明。各读取方自行负责 JSON 校验与解析后的默认值。

对齐上游 `@deepseek-ai/dsh-package-manifest/types`。线协议键名保持英文。
"""
from typing import Literal,NotRequired,TypedDict#字面量、可选字段与结构类型

__all__=[#仅中文公开名
    '配置档补丁重载','组合包清单','配置档清单','客户端清单','配置树声明',
    '会话格式迁移清单','模块回退清单','清单',
]#公开面结束

配置档补丁重载=Literal['live','startup']#用户补丁在配置档存活期间热重载，或仅启动时应用

class 组合包清单(TypedDict):#组合包导出的配置层
    """组合包导出的配置层。"""
    patch:str#相对声明包根的补丁文件路径

class 配置档清单(TypedDict,total=False):#配置档目录声明的组合包合成
    """配置档目录声明的组合包合成。"""
    bundles:list[str]#有序组合包层列表，使用已安装包名
    patchReload:配置档补丁重载#用户补丁生命周期；省略则自定义配置档为 live

class 客户端清单(TypedDict):#客户端模块与构建读取的客户端声明
    """客户端模块与构建读取的客户端声明。"""
    platform:str#客户端平台标识；Web 消费方选 web
    inject:NotRequired[list[str]]#信息性包名依赖，不是 Cordis 服务注入
    immediately:NotRequired[bool]#启动第一阶段登记屏障；缺席表示共享应用批次
    external:NotRequired[list[str]]#基线之外的精确模块表请求，含 <pkg>/client 等子路径；缺席表示仅基线 external

class 配置树声明(TypedDict):#实验性镜像打包器从 CLI 包读取的一个配置目录
    """实验性镜像打包器从 CLI 包读取的一个配置目录。"""
    mount:str#镜像内非空目标路径；挂载值须唯一
    path:str#相对声明包根的非空源目录路径
    scanRoster:NotRequired[bool]#是否把该目录的 YAML 插件行纳入包名册；缺席表示 false

# `from` 为 Python 硬关键字，须用函数式 TypedDict 保留线协议键名。
会话格式迁移清单=TypedDict('会话格式迁移清单',{#磁盘上声明的相邻会话格式迁移
    'from':int,#非负源版本；负零拒绝
    'to':int,#非负目标版本，恰为 from + 1
    'export':str,#非空包导出路径，如 . 或 ./migration
    'migration':str,#迁移实现的非空具名导出
    'sourceCodec':str,#源版本编解码器的非空具名导出
    'targetCodec':str,#目标版本编解码器的非空具名导出
    'targetHeaderValidator':str,#目标头校验器的非空具名导出
    'targetRestorer':str,#目标版本恢复器的非空具名导出
})#目录生成器只发现 packages/session/session-format-vN-to-vN+1，不发现外部插件

class 模块回退清单(TypedDict):#启动器模块回退代理生成并读取的元数据
    """启动器模块回退代理生成并读取的元数据；非作者配置项。"""
    targets:dict[str,str]#包导出子路径映射到已解析目标文件 URL

class 清单(TypedDict,total=False):#npm 清单的 dsh 属性；一包可声明多种角色
    """npm 清单的 `dsh` 属性；一包可声明多种角色。不含外层 npm 清单本身。"""
    bundle:组合包清单#配置档启动器消费的组合包元数据
    profile:配置档清单#配置档启动器消费的配置档元数据
    client:客户端清单#客户端模块加载与构建元数据
    configTrees:list[配置树声明]#实验性部署镜像打包器消费的配置目录
    sessionFormatMigration:会话格式迁移清单#工作区目录生成器消费的相邻会话迁移元数据
    moduleFallback:模块回退清单#启动器生成的模块代理元数据，非作者配置项
