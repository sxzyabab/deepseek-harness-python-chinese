"""每个 ic_ds_* 图标组件共用的属性。

对齐上游 `ui-primitives/src/icons/props.ts`。公开面仅中文名。
"""

__all__=['图标属性','取尺寸','取类名']#仅中文公开名

图标属性=('size','className')#共用字段

def 取尺寸(属性,默认):#正方形边长
    """缺省用字形自身绘制尺寸。"""
    if 属性 is None:#空
        return 默认#默认
    if isinstance(属性,dict):#映射
        return 属性['size'] if 'size' in 属性 and 属性['size'] is not None else 默认#尺寸
    值=getattr(属性,'size',None)#属性
    return 默认 if 值 is None else 值#尺寸

def 取类名(属性):#布局 class
    """颜色走 currentColor。"""
    if 属性 is None:#空
        return None#无
    if isinstance(属性,dict):#映射
        return 属性.get('className')#类
    return getattr(属性,'className',None)#类
