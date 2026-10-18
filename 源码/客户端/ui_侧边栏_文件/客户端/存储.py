import re
from ..异常 import 文件树错误

__all__=['初值','自动刷新','启动','加载中','已加载','已失败','已切换','已滚动','重置','遗忘']

def _分桶(状态,标签标识):
    'start 之前没有桶。写者依赖这次播种'
    按标签=状态['byTab']
    if 标签标识 not in 按标签:
        raise 文件树错误('ui-sidebar-files: no tree for tab "'+str(标签标识)+'"')
    return 按标签[标签标识]

def 初值():
    '空的按标签分桶'
    return {'byTab':{}}

def 启动(草稿,标签标识,根):
    '根放进展开集。打开时不用再点一次'
    草稿['byTab'][标签标识]={
        'root':根,
        'levels':{},
        'expanded':[根],
        'scrollTop':0,
        'autoRefresh':True,
    }

def 自动刷新(草稿,标签标识,启用):
    '记下这一标签是否自动重读'
    _分桶(草稿,标签标识)['autoRefresh']=启用

def 加载中(草稿,标签标识,路径):
    '这一级还不是就绪时标成加载中'
    树=_分桶(草稿,标签标识)
    现=树['levels'][路径] if 路径 in 树['levels'] else None
    if 现 is None or 现.get('kind')!='ready':
        树['levels'][路径]={'kind':'loading'}

def 已加载(草稿,标签标识,路径,层级):
    '记下这一级的条目。原先已就绪时，裁掉消失的子目录'
    树=_分桶(草稿,标签标识)
    先前=树['levels'][路径] if 路径 in 树['levels'] else None
    if 先前 is not None and 先前.get('kind')=='ready':
        目录名=set()
        for 项 in 层级['entries']:
            if 项['type']=='directory':
                目录名.add(项['name'])
        for 项 in 先前['level']['entries']:
            if 项['type']!='directory' or 项['name'] in 目录名:
                continue
            已删=re.sub(r'[/\\]+$','',路径)+'/'+项['name']
            树['expanded']=[
                值 for 值 in 树['expanded']
                if 值!=已删 and not 值.startswith(已删+'/')
            ]
            树['levels']={
                键:值 for 键,值 in 树['levels'].items()
                if 键!=已删 and not 键.startswith(已删+'/')
            }
    树['levels'][路径]={'kind':'ready','level':层级}

def 已失败(草稿,标签标识,路径,失败):
    '列不出的原因。已就绪的级只叠 failure'
    树=_分桶(草稿,标签标识)
    级=树['levels'][路径] if 路径 in 树['levels'] else None
    if 级 is not None and 级.get('kind')=='ready':
        树['levels'][路径]={**级,'failure':失败}
    else:
        树['levels'][路径]={'kind':'failed','failure':失败}

def 已切换(草稿,标签标识,路径):
    '展开或折叠。收起后已加载的级仍留着'
    树=_分桶(草稿,标签标识)
    展开=树['expanded']
    if 路径 in 展开:
        展开.remove(路径)
    else:
        展开.append(路径)

def 已滚动(草稿,标签标识,滚动顶):
    '记下正文滚动偏移，单位是像素'
    _分桶(草稿,标签标识)['scrollTop']=滚动顶

def 重置(草稿,标签标识):
    '只清已加载的级，不收起目录'
    _分桶(草稿,标签标识)['levels']={}

def 遗忘(草稿,标签标识):
    '丢掉这一标签的树'
    草稿['byTab']={键:值 for 键,值 in 草稿['byTab'].items() if 键!=标签标识}
