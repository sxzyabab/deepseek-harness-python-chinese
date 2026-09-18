"""启动器拥有的配置档位置与组合输入。"""
from os.path import join as 拼接#路径拼接
from .配置档 import 组合条目,加载配置目录,配置补丁文件名#配置档组合与加载
from . import 加载可选补丁#可选补丁加载

__all__=['解析遥测补丁','读配置档补丁']#仅中文公开名

遥测行标识='session-telemetry-otel'#遥测行 id

def 解析遥测补丁(禁用环境,有行):
    """把遥测退出开关收成启动补丁。任意非空即禁用。"""
    if (禁用环境 if 禁用环境 is not None else '')=='' or not 有行:#未设或无行
        return None#不需要
    return {'id':遥测行标识,'disabled':True}#硬禁用该行

def 读配置档补丁(二进制名,上下文,初始配置=None):
    """读取当前组合包与用户层，并叠上启动时覆盖。上下文为 dict。"""
    if 初始配置 is None:#省略则读盘
        配置=加载配置目录(二进制名,上下文['dir'],上下文['installAnchor'],{'userLayer':False})#加载
    else:#复用
        配置=初始配置#已加载
    补丁=[]#有序补丁
    for 层 in 配置['layers']:#组合包层
        补丁.extend(层['patches'])#展平
    if 初始配置 is not None:#有初始用户层
        补丁.extend(初始配置['patches'])#用户层
    else:#读用户文件
        用户=加载可选补丁(二进制名,上下文['patchPath'])#可选
        if 用户 is not None:#有
            补丁.extend(用户)#追加
    主目录补丁=加载可选补丁(二进制名,拼接(上下文['home'],配置补丁文件名))#主目录层
    if 主目录补丁 is not None:#有
        补丁.extend(主目录补丁)#追加
    补丁.extend(上下文['overlays'] if 'overlays' in 上下文 else [])#命令行覆盖
    遥测=解析遥测补丁(上下文.get('telemetryDisabledEnv'),any(行.get('id')==遥测行标识 for 行 in 组合条目([补丁])))#遥测补丁
    if 遥测 is not None:#需要
        补丁.append(遥测)#追加禁用
    return 补丁#有序补丁
