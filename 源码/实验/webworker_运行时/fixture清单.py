"""浏览器可读的内置 Preview 文件系统 overlay 目录。

对齐上游 `webworker-runtime/src/fixture-manifest.ts`。公开面仅中文名。
"""
import re#id形态校验

__all__=[#仅中文公开名
    '预览fixture清单版本','预览fixture清单文件','解析预览fixture清单',
]#公开面结束

预览fixture清单版本=1#写在基础VFS镜像旁的manifest格式版本
预览fixture清单文件='fixtures.json'#相对基础镜像解析的叶名
标识形态=re.compile(r'^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$')#fixture id形态

def 收窄记录(值):#对象收窄为普通字典
    """把未知值收窄为普通对象记录，否则返回 None。"""
    if isinstance(值,dict) and not isinstance(值,list):#是否普通对象
        return 值#收窄为记录
    return None#非对象

def 解析预览fixture清单(值):#解析并校验
    """在静态 fixture 目录控制 Worker 获取之前校验它。

    参数:
        值: 已解析的 JSON 响应。
    返回:
        带唯一 id 与非空 overlay 列表的分离 manifest。
    """
    记录=收窄记录(值)#顶层记录
    if 记录 is None or 记录.get('version')!=预览fixture清单版本 or not isinstance(记录.get('fixtures'),list):#版本或列表非法
        raise Exception(f'preview fixture manifest must use version {预览fixture清单版本}')#拒绝
    条目们=[]#输出列表
    已见标识=set()#已见id
    for 原始 in 记录['fixtures']:#逐条校验
        条目=收窄记录(原始)#条目记录
        if 条目 is None:#非对象
            raise Exception('preview fixture manifest contains an invalid fixture entry')#拒绝条目
        标识=条目.get('id')#id字段
        标签=条目.get('label')#标签
        说明=条目.get('description')#说明
        覆盖层=条目.get('overlays')#overlay原始
        覆盖地址们=[层 for 层 in 覆盖层 if isinstance(层,str) and len(层)>0] if isinstance(覆盖层,list) else []#非空串
        if (not isinstance(标识,str) or not 标识形态.match(标识)#id形态
            or 标识=='none' or 标识=='webfs'#保留名
            or not isinstance(标签,str) or len(标签)==0#标签
            or not isinstance(说明,str) or len(说明)==0#说明
            or not isinstance(覆盖层,list) or len(覆盖层)==0 or len(覆盖地址们)!=len(覆盖层)):#overlay
            raise Exception('preview fixture manifest contains an invalid fixture entry')#拒绝条目
        if 标识 in 已见标识:#重复id
            raise Exception(f'preview fixture manifest repeats id "{标识}"')#拒绝
        已见标识.add(标识)#记入集合
        条目们.append({'id':标识,'label':标签,'description':说明,'overlays':覆盖地址们})#追加合法条目
    默认=记录.get('defaultFixture')#默认字段
    if 默认 is not None and (not isinstance(默认,str) or 默认 not in 已见标识):#默认非法
        raise Exception('preview fixture manifest defaultFixture does not name a fixture')#拒绝
    return {'version':预览fixture清单版本,'defaultFixture':默认,'fixtures':条目们}#返回manifest
