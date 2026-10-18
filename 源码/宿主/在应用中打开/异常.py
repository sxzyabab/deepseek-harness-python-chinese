'在应用中打开主机半边的失败'
import json#穷尽失败时把未处理的值收成 JSON

__all__=['在应用中打开错误','断言穷尽']

class 在应用中打开错误(Exception):
    '在应用中打开主机半边失败'

def 断言穷尽(值):
    '定位器或启动种类没有对应分支'
    raise 在应用中打开错误('unhandled open-in-app catalog kind: '+json.dumps(值,ensure_ascii=False,separators=(',',':')))#封闭并集被伪造时才到这里
