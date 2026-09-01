"""各接受调用方时区的线边界共享的时间词汇。只做校验与规范化：本库不格式化、也不拥有失败词汇——各边界自行声明并抛出拒绝。"""
import re#IANA 区名模式
__all__=['规范化客户端时区']#仅中文公开名

_iana时区=re.compile(r'^[A-Za-z][A-Za-z0-9_+.-]*(?:\/[A-Za-z0-9_+.-]+)+$')#严格浏览器区配置：UTC 或 IANA Area/Location

def 规范化客户端时区(值):#校验并规范化一条 IANA 时区
    """在线边界校验并规范化一条调用方上报的 IANA 时区。规范名是后续读者需要的：区身份会存到耐久记录里，再由别的进程解析，因此这里接受的别名不能与读者推导出的区相等。"""
    if not isinstance(值,str) or len(值)==0 or 值!=值.strip() or (值!='UTC' and not _iana时区.fullmatch(值)):#空白、未 trim 或形态不对
        return None#不可用
    try:#用 zoneinfo 解析规范名
        from zoneinfo import ZoneInfo#IANA 时区
        规范=ZoneInfo(值).key#规范键
    except Exception:#不支持的名字
        return None#解析拒绝
    if 规范!='UTC' and not _iana时区.fullmatch(规范):#规范结果仍须符合形态
        return None#不可用
    return 规范#规范区名
