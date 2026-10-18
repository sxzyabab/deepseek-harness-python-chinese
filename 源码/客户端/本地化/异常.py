class 本地化错误(Exception):
    '语言标识、回退链或词表登记不符合上游约定'

def 抛非法语言标识(标识):
    'id 不是 BCP 47 风格标签'
    raise 本地化错误('locale id "'+标识+'" is not a BCP 47-style tag')

def 抛回退未登记(标识):
    '回退语言还没登记'
    raise 本地化错误('locale fallback "'+标识+'" is not registered')
