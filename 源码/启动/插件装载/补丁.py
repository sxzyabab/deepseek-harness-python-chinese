"""保留注释风格的配置档插件启停补丁编辑。"""
import os#路径
import yaml#补丁 YAML
from ...依赖.include import 插件列表读取器,插件列表写出器#!!js 方言
from ...工具.原子写入 import 原子写文件#原子写回
from ..app启动 import 加载可选补丁#校验可读

__all__=['写插件启用']#仅中文公开名

def 写插件启用(文件名,编号,模块名,启用):
    """替换最后一条匹配覆盖，或在已有插入之后追加。返回文件是否变化。"""
    try:#读
        文件=open(文件名,'r',encoding='utf-8')#打开
        try:#读全文
            文本=文件.read()#原文
        finally:#关
            文件.close()#关闭
    except FileNotFoundError:#缺失
        文本='[]\n'#空序列
    except OSError as 错误:#其它
        if getattr(错误,'errno',None)!=2:#非 ENOENT
            raise#原样
        文本='[]\n'#空序列
    try:#解析
        文档=yaml.load(文本,Loader=插件列表读取器)#含 !!js
    except yaml.YAMLError as 错误:#畸形
        raise 错误#原样
    if not isinstance(文档,list):#须为序列
        raise Exception('Profile patch must be a YAML sequence')#拒绝
    加载可选补丁('dsh',文件名)#与上游一样先校验可读
    目标下标=None#最后匹配覆盖下标
    for 下标 in range(len(文档)-1,-1,-1):#自末向前
        项=文档[下标]#当前项
        if not isinstance(项,dict):#非映射
            continue#跳过
        if 项.get('id')!=编号:#id 不配
            continue#跳过
        if 'insert' in 项:#插入层
            continue#跳过
        期望名=项.get('name')#覆盖上的模块名
        if 期望名 and 期望名!=模块名:#名限定不配
            continue#跳过
        目标下标=下标#命中
        break#最后一条
    if 目标下标 is not None:#已有覆盖
        if 文档[目标下标].get('disabled')==(not 启用):#已是目标态
            return False#无变化
        文档[目标下标]['disabled']=not 启用#写 disabled
    else:#追加覆盖
        文档.append({'id':编号,'disabled':not 启用})#新覆盖
    写出=yaml.dump(文档,Dumper=插件列表写出器,allow_unicode=True,sort_keys=False)#写回
    原子写文件(文件名,写出 if 写出.endswith('\n') else 写出+'\n',{'mode':0o600})#原子替换
    return True#已变化
