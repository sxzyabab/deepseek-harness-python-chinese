"""包管理器操作后的已装配置依赖及其组合包激活。"""
import os#路径
from .配置档 import 读配置清单,解析组合包目录,写配置清单#清单读写与组合包目录

__all__=['读配置插件','写配置组合包','对账配置插件']#仅中文公开名

def 可选清单(二进制名,包目录):
    """读清单；失败当缺失。"""
    try:#读
        return 读配置清单(二进制名,包目录)#清单
    except Exception:#读失败
        return None#缺失

def 组合包清单(位置,名):
    """用与配置加载相同的安装优先序解析激活元数据。位置为 dict。"""
    try:#解析目录
        包目录=解析组合包目录(位置['binName'],名,位置['installAnchor'],位置['profileDir'])#目录
    except Exception:#未解析
        return None#普通包
    return 可选清单(位置['binName'],包目录)#清单

def 读配置插件(位置):
    """读已装版本与组合包声明。位置为 dict。"""
    清单=读配置清单(位置['binName'],位置['profileDir'])#配置清单
    组合包=((清单.get('dsh') or {}).get('profile') or {}).get('bundles') or []#活动组合包
    依赖表=[]#依赖行
    for 名,规格 in (清单.get('dependencies') or {}).items():#逐依赖
        已装=可选清单(位置['binName'],os.path.join(位置['profileDir'],'node_modules',名))#已装元数据
        版本=已装['version'] if 已装 is not None and isinstance(已装.get('version'),str) else 规格#版本或规格
        包清单=组合包清单(位置,名)#组合包元数据
        是组合包=包清单 is not None and ((包清单.get('dsh') or {}).get('bundle') or {}).get('patch') is not None#是否组合包
        依赖表.append({'name':名,'version':版本,'bundle':是组合包,'enabled':名 in 组合包})#行
    return {'manifest':清单,'dependencies':依赖表}#清单与依赖

def 写配置组合包(配置目录,清单,组合包列表):
    """写组合包列表同时保留其余元数据。"""
    更新=dict(清单)#拷贝
    dsh=dict(清单.get('dsh') or {})#dsh
    配置=dict(dsh.get('profile') or {})#profile
    配置['bundles']=list(组合包列表)#组合包
    dsh['profile']=配置#写回
    更新['dsh']=dsh#写回
    写配置清单(配置目录,更新)#落盘
    return 更新#已写清单

def 对账配置插件(选项):
    """成功包管理器操作后对账已装组合包声明。选项为 dict。"""
    之后=读配置插件(选项)#操作后
    前名=set(依赖['name'] for 依赖 in 选项['before']['dependencies'])#操作前名
    后名=set(依赖['name'] for 依赖 in 之后['dependencies'])#操作后名
    组合包名=set(依赖['name'] for 依赖 in 之后['dependencies'] if 依赖['bundle'])#组合包名
    if 选项.get('preserveDisabled'):#保留禁用
        禁用=set(依赖['name'] for 依赖 in 选项['before']['dependencies'] if 依赖['bundle'] and not 依赖['enabled'])#禁用集
    else:#不保留
        禁用=set()#空
    先前=((之后['manifest'].get('dsh') or {}).get('profile') or {}).get('bundles') or []#先前列表
    组合包=[名 for 名 in 先前 if not (名 in 前名 or 名 in 后名) or 名 in 组合包名]#保留模板与仍是组合包的
    for 依赖 in 之后['dependencies']:#新组合包自动激活
        if 依赖['bundle'] and 依赖['name'] not in 禁用 and 依赖['name'] not in 组合包:#可激活
            组合包.append(依赖['name'])#追加
    变更=len(组合包)!=len(先前) or any(组合包[下标]!=先前[下标] for 下标 in range(len(组合包)))#是否变更
    清单=写配置组合包(选项['profileDir'],之后['manifest'],组合包) if 变更 else 之后['manifest']#写或复用
    依赖表=[{**依赖,'enabled':依赖['name'] in 组合包} for 依赖 in 之后['dependencies']]#同步启用
    新普通=[依赖['name'] for 依赖 in 之后['dependencies'] if not 依赖['bundle'] and 依赖['name'] not in 前名]#新普通依赖
    return {'plugins':{'manifest':清单,'dependencies':依赖表},'addedPlainDependencies':新普通}#对账结果
