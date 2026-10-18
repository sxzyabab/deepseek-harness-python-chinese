'远程访问控制的资源。global 没有身份，其它种类各有一个线上标识。资源之间互不蕴含'
远程访问资源种类=('global',)#内建种类。声明的种类在运行时并入
全局资源={'kind':'global'}#没有身份的全局资源

def 是全局资源(资源):
    '是不是内建的全局资源'
    return isinstance(资源,dict) and 资源.get('kind')=='global' and 'id' not in 资源#只有种类

def 资源于(种类,标识=None):
    '按种类拼一条资源。global 不带标识'
    if 种类=='global':#内建
        return {'kind':'global'}#无标识
    return {'kind':种类,'id':标识}#声明种类的一个身份
