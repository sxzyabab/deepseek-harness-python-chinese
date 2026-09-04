"""DOM 快照卫生：作用域类名折叠与 svg 指纹。

对齐上游 `client-runtime/src/snapshot.ts`。公开面仅中文名。
无 vitest 时序列化器以可调用字典暴露；注册幂等。
"""
import re#作用域类模式

__all__=['DOM快照序列化器','注册DOM快照序列化器','折叠类名值','计算指纹']#仅中文公开名

作用域类模式=re.compile(r'^_(.+)_[a-z0-9]+$')#作用域类模式
已注册=[False]#是否已注册
序列化器登记表=[]#可挂接的序列化器表

def 折叠类名值(值):#折叠类名
    """折叠一个 class 属性值中的作用域令牌。"""
    return ' '.join(#空格接合
        作用域类模式.sub(r'\1',令牌)#折回 local
        for 令牌 in 值.split()#按空白拆
        if 令牌!=''#去空
    )#返回

def 计算指纹(标记):#计算指纹
    """svg 标记上的 FNV-1a 32 位。"""
    哈希=0x811c9dc5#FNV 偏移基
    for 字符 in 标记:#逐字符
        哈希^=ord(字符)#异或
        哈希=(哈希*0x01000193)&0xffffffff#乘质数
    return f'{哈希:08x}'#十六进制

def 收集SVG(根):#收集 svg
    """子树的 svg 元素列表；无 DOM 时返回空。"""
    if not hasattr(根,'querySelectorAll'):#无 DOM
        return []#空
    列表=list(根.querySelectorAll('svg'))#后代 svg
    标签=getattr(根,'tagName','')#根标签
    if str(标签).lower()=='svg':#根亦计入
        列表.insert(0,根)#插入根
    return 列表#返回列表

def 需要归一化(根):#是否需归一化
    """序列化该子树是否需要归一化克隆。"""
    if not hasattr(根,'querySelectorAll'):#无 DOM
        return False#不需要
    节点们=[根,*根.querySelectorAll('[class]')]#带 class 节点
    for 元素 in 节点们:#扫描类
        取值=元素.getAttribute('class') if hasattr(元素,'getAttribute') else None#读 class
        if 取值 is not None and any(作用域类模式.match(令牌) for 令牌 in 取值.split()):#匹配作用域类
            return True#需要
    return any(len(getattr(svg,'childNodes',[]))>0 for svg in 收集SVG(根))#或有 svg 子节点

def 测试序列化值(值):#是否匹配
    """是否为需归一化的 DOM 元素。"""
    return hasattr(值,'querySelectorAll') and 需要归一化(值)#需归一化则匹配

def 序列化值(值,_配置=None,_缩进=None,_深度=None,_引用=None,打印机=None):#序列化
    """归一化克隆后交回打印机。"""
    克隆=值.cloneNode(True) if hasattr(值,'cloneNode') else 值#克隆
    if hasattr(克隆,'querySelectorAll'):#有 DOM
        for 元素 in [克隆,*克隆.querySelectorAll('[class]')]:#遍历带 class 节点
            原始=元素.getAttribute('class')#读原始类
            if 原始 is not None:#有类
                元素.setAttribute('class',折叠类名值(原始))#折叠类名
        for svg in 收集SVG(克隆):#遍历 svg
            子们=getattr(svg,'childNodes',[])#子节点
            if len(子们)==0:#空则跳过
                continue#跳过
            内部=getattr(svg,'innerHTML','')#内部 HTML
            svg.setAttribute('data-content',计算指纹(内部))#指纹
            if hasattr(svg,'replaceChildren'):#清空内部
                svg.replaceChildren()#清空
    if 打印机 is not None:#有打印机
        return 打印机(克隆,_配置,_缩进,_深度,_引用)#交回内置打印
    return str(克隆)#字符串回退

DOM快照序列化器={'test':测试序列化值,'serialize':序列化值}#DOM 快照序列化器

def 注册DOM快照序列化器():#注册序列化器
    """向序列化器登记表注册（幂等）。"""
    if 已注册[0]:#幂等
        return#结束
    已注册[0]=True#标记已注册
    序列化器登记表.append(DOM快照序列化器)#注册

domSnapshotSerializer=DOM快照序列化器#上游名
registerDomSnapshotSerializer=注册DOM快照序列化器#上游名
