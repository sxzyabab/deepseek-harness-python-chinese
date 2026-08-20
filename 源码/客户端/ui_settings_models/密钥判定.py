"""浏览器侧对已键入 API 密钥的判定。

对齐上游 `ui-settings-models/src/client/apiKey.ts`。公开面仅中文名。
"""
import re#正则

__all__=['合法密钥模式','环境行模式','是否引号包裹','密钥失败','apiKeyFailure']#仅中文公开名

合法密钥模式=re.compile(r'^[\x21-\x7E]+$')#可打印 ASCII（不含空格）
环境行模式=re.compile(r'^[A-Z][A-Z0-9_]*=[^=]')#全大写 NAME= 后跟非 =

def 是否引号包裹(值):#值是否被一对匹配引号包住
    """首尾同为引号且长度>1。"""
    if len(值)==0:#空
        return False#否
    首=值[0]#首字符
    if 首 not in ('"',"'",'`'):#非引号
        return False#否
    return len(值)>1 and 值.endswith(首)#同引号收尾

def 密钥失败(草稿):#判定密钥输入当前值
    """空字段表示沿用已存密钥；只含空白或非法字符则失败文案键。"""
    if len(草稿)==0:#空字段
        return None#沿用
    值=草稿.strip()#去空白
    if len(值)==0:#只含空白
        return 'keyBlank'#空白失败
    if 环境行模式.search(值) or 是否引号包裹(值):#环境行或引号
        return 'keyIllegalCharacters'#非法
    if 合法密钥模式.search(值) is None:#非可打印 ASCII
        return 'keyIllegalCharacters'#非法
    return None#通过

apiKeyFailure=密钥失败#上游名
