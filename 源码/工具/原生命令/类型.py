"""浏览器安全的原生文件关联元数据。"""
import re

图标形态=re.compile(r'^data:image/(?:png|svg\+xml);base64,[A-Za-z0-9+/=]+$')

def 解析原生文件应用程序(值):
    """校验从原生命令或已认证宿主收到的文件关联元数据。"""
    if not isinstance(值,list):
        raise ValueError('Invalid native application list')
    应用程序表=[]
    for 条目 in 值:
        if (not isinstance(条目,dict)
            or 'id' not in 条目 or 'name' not in 条目 or 'default' not in 条目 or 'icon' not in 条目
            or not isinstance(条目['id'],str) or len(条目['id'])==0
            or not isinstance(条目['name'],str) or not isinstance(条目['default'],bool)
            or not (条目['icon'] is None or (isinstance(条目['icon'],str) and 图标形态.match(条目['icon'])))):
            raise ValueError('Invalid native application entry')
        应用程序表.append({'id':条目['id'],'name':条目['name'],'default':条目['default'],'icon':条目['icon']})
    return 应用程序表

__all__=['解析原生文件应用程序']
