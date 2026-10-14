import importlib.resources as 包资源
import re as 正则

__all__=['读样式','挂到根']

def 读样式(文件名):
    '读同目录样式。打不开时只报样式读不到，不含路径'
    try:
        return 包资源.files(__package__).joinpath(文件名).read_text(encoding='utf-8')
    except OSError:
        raise OSError('样式读不到') from None

def 去注释(原文):
    '去掉块注释，避免注释里的花括号打断规则'
    出=[]
    下标=0
    长度=len(原文)
    while 下标<长度:
        if 原文.startswith('/*',下标):
            止=原文.find('*/',下标+2)
            if 止<0:
                break
            下标=止+2
            continue
        出.append(原文[下标])
        下标+=1
    return ''.join(出)

def 挂到根(原文,根):
    '类选择器只作用在给定根下'
    文=去注释(原文)
    def 换(匹配):
        选择器=匹配.group(1).strip()
        体=匹配.group(2)
        if 选择器.startswith('@'):
            return 选择器+'{'+体+'}'
        条=[]
        for 片 in 选择器.split(','):
            片=片.strip()
            if 片=='':
                continue
            条.append('.'+根+' '+片)
            条.append('.'+根+片)
        if len(条)==0:
            return ''
        return ', '.join(条)+'{'+体+'}'
    return 正则.sub(r'([^{]+)\{([^}]*)\}',换,文)
