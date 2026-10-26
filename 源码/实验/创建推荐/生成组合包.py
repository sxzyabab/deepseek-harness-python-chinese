'只接纳新名字的组合包，并且补丁只添加它自己的行'
import os,json,stat,yaml

__all__=['校验生成组合包']

运行时拓展名=('.js','.mjs','.cjs')

def 校验生成组合包(目录,名字):
    '安装进配置档之前检查模型写下的文件。不执行代码'
    清单路径=包内文件(目录,'package.json')
    文件=open(清单路径,'r',encoding='utf-8')
    try:
        清单=json.loads(文件.read())
    finally:
        文件.close()
    if not isinstance(清单,dict) or 清单.get('name')!=名字 or not isinstance(清单.get('version'),str) or len(清单['version'])==0:
        raise ValueError('Generated package identity is invalid.')
    深=清单.get('dsh')
    if not isinstance(深,dict) or not isinstance(深.get('bundle'),dict) or 深['bundle'].get('patch')!='./cordis.patch.yml':
        raise ValueError('Generated package must declare dsh.bundle.patch="./cordis.patch.yml".')
    if 'client' in 深 and not isinstance(深.get('client'),dict):
        raise ValueError('Generated package dsh.client must be an object.')
    补丁路径=包内文件(目录,清单['dsh']['bundle']['patch'])
    补丁文件=open(补丁路径,'r',encoding='utf-8')
    try:
        文本=补丁文件.read()
    finally:
        补丁文件.close()
    try:
        补丁=yaml.safe_load(文本)
    except yaml.YAMLError:
        raise ValueError('Generated patches must use plain YAML without custom tags or includes.')
    if not isinstance(补丁,list) or len(补丁)==0:
        raise ValueError('Generated bundles must add uniquely named rows from their own package.')
    标识=set()
    for 操作 in 补丁:
        if not isinstance(操作,dict) or set(操作.keys())!={'insert'}:
            raise ValueError('Generated bundles must add uniquely named rows from their own package.')
        插入=操作['insert']
        if not isinstance(插入,list) or len(插入)==0:
            raise ValueError('Generated bundles must add uniquely named rows from their own package.')
        for 行 in 插入:
            if not isinstance(行,dict) or not isinstance(行.get('id'),str) or len(行['id'])==0 or not isinstance(行.get('name'),str) or len(行['name'])==0:
                raise ValueError('Generated bundles must add uniquely named rows from their own package.')
            if 'group' in 行 and 行['group'] is not False:
                raise ValueError('Generated bundles must add uniquely named rows from their own package.')
            if not 行['id'].startswith(名字+':') or 行['id'] in 标识 or (行['name']!=名字 and not 行['name'].startswith(名字+'/')):
                raise ValueError('Generated bundles must add uniquely named rows from their own package.')
            标识.add(行['id'])
            if 清单.get('exports') is None:
                目标=(清单.get('main') or './index.js') if 行['name']==名字 else './'+行['name'][len(名字)+1:]
            else:
                目标=导出入口(清单,行['name'])
            if 目标 is None or os.path.splitext(目标)[1] not in 运行时拓展名:
                raise ValueError('Build and export the runtime entry for '+行['name']+' before installation.')
            入口=包内文件(目录,目标)
            if not stat是文件(入口):
                raise ValueError('The runtime entry for '+行['name']+' must be a built file.')
    if 清单['dsh'].get('client') is not None and not 是已构建文件(目录,导出入口(清单,名字+'/client')):
        raise ValueError('Build and export the "./client" entry before installation.')
    校验链接(os.path.realpath(目录),目录)

def stat是文件(路径):
    '不跟随链接。链接本身不是已构建的文件'
    return stat.S_ISREG(os.lstat(路径).st_mode)

def 是已构建文件(目录,目标):
    '相对入口是不是包内已有的 JavaScript 文件'
    if 目标 is None or os.path.splitext(目标)[1] not in 运行时拓展名:
        return False
    try:
        入口=包内文件(目录,目标)
    except (OSError,ValueError):
        return False
    try:
        return stat是文件(入口)
    except OSError:
        return False

def 导出入口(清单,说明符):
    'exports 把包说明符映射到的第一个文件。没有匹配时没有入口'
    try:
        名字=清单['name']
        相对='.' if 说明符==名字 else './'+说明符[len(名字)+1:]
        return 解开导出(清单.get('exports'),相对,True)
    except Exception:
        return None

def 解开导出(节点,相对,在根):
    '条件导出取 import、require、default、node 里的第一个字符串'
    if isinstance(节点,str):
        return 节点 if not 在根 or 相对=='.' else None
    if isinstance(节点,list):
        for 项 in 节点:
            命中=解开导出(项,相对,在根)
            if isinstance(命中,str):
                return 命中
        return None
    if isinstance(节点,dict):
        if 在根 and any(isinstance(键,str) and 键.startswith('.') for 键 in 节点):
            if 相对 not in 节点:
                return None
            return 解开导出(节点[相对],相对,False)
        for 键 in ('import','require','default','node'):
            if 键 in 节点:
                return 解开导出(节点[键],相对,False)
        return None
    return None

def 校验链接(根,目录):
    '相对链接在组合包被拷出工作区之后仍然要能工作'
    for 项 in os.scandir(目录):
        if 项.is_symlink():
            链接=os.readlink(项.path)
            if os.path.isabs(链接):
                raise ValueError('Generated bundle links must be relative and stay inside the bundle.')
            包内文件(根,os.path.normpath(os.path.join(os.path.dirname(项.path),链接)))
        elif 项.is_dir(follow_symlinks=False):
            校验链接(根,项.path)

def 包内文件(目录,文件):
    '真实路径必须留在保留目录里'
    根=os.path.realpath(目录)
    路径=os.path.realpath(os.path.join(目录,文件))
    if not 路径.startswith(根+os.sep):
        raise ValueError('Generated bundle files must remain inside their reserved directory.')
    return 路径
