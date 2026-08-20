"""面向模型的引用信封所用的标签安全 JSON 序列化。"""
import json#JSON序列化

def 序列化标签安全JSON(值):#把引用数据序列成不含开标签的JSON
    """序列化 JSON，同时阻止源数据拼出类似 XML 的开标签。解析结果不变，且数据中不含字面量 `<`。"""
    try:#按JSON序列化
        已序列=json.dumps(值,ensure_ascii=False,separators=(',',':'))#紧凑JSON，保留非ASCII
    except (TypeError,ValueError) as 错误:#无法序列化
        raise TypeError('session-reference data is not JSON-serializable') from 错误#无法序列化则失败
    if not isinstance(已序列,str):#必须是字符串
        raise TypeError('session-reference data is not JSON-serializable')#无法序列化则失败
    return 已序列.replace('<','\\u003c')#把字面量<转成Unicode转义
