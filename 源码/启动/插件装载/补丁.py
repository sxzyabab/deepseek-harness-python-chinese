"""保留注释风格的配置档插件启停补丁编辑。"""
import os
import yaml
from ...依赖.include import 插件列表读取器,插件列表写出器
from ...工具.原子写入 import 原子写文件
from ..app启动 import 加载可选补丁

__all__=['写插件启用']

def 写插件启用(文件名,编号,模块名,启用):
    """替换最后一条匹配覆盖，或在已有插入之后追加。返回文件是否变化。"""
    try:
        文件=open(文件名,'r',encoding='utf-8')
        try:
            文本=文件.read()
        finally:
            文件.close()
    except FileNotFoundError:
        文本='[]\n'
    except OSError as 错误:
        if getattr(错误,'errno',None)!=2:
            raise
        文本='[]\n'
    try:
        文档=yaml.load(文本,Loader=插件列表读取器)
    except yaml.YAMLError as 错误:
        raise 错误
    if not isinstance(文档,list):
        raise Exception('配置档补丁必须是 YAML 序列')
    加载可选补丁('dsh',文件名)
    目标下标=None
    for 下标 in range(len(文档)-1,-1,-1):
        项=文档[下标]
        if not isinstance(项,dict):
            continue
        if 项.get('id')!=编号:
            continue
        if 'insert' in 项:
            continue
        期望名=项.get('name')
        if 期望名 and 期望名!=模块名:
            continue
        目标下标=下标
        break
    if 目标下标 is not None:
        if 文档[目标下标].get('disabled')==(not 启用):
            return False
        文档[目标下标]['disabled']=not 启用
    else:
        文档.append({'id':编号,'disabled':not 启用})
    写出=yaml.dump(文档,Dumper=插件列表写出器,allow_unicode=True,sort_keys=False)
    原子写文件(文件名,写出 if 写出.endswith('\n') else 写出+'\n',{'mode':0o600})
    return True
