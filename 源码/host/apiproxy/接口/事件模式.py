"""事件域帧模式。对齐上游 `host/apiproxy/src/api/events.schema.ts`。公开面仅中文名。"""

__all__=['复用帧模式','宿主帧模式']#公开面

class _帧模式:#SSE 载荷槽第二级解析基类
    """帧载荷须为带 type 判别字段的映射。"""
    @staticmethod
    def parse(值):#解析帧载荷
        """type 非空字符串；其余字段宽放行。"""
        if not isinstance(值,dict):#非映射
            raise Exception('invalid event frame payload')#拒绝
        类型=值.get('type')#判别字段
        if not isinstance(类型,str) or 类型=='':#缺或空
            raise Exception('invalid event frame type')#拒绝
        return dict(值)#原样通过

class 复用帧模式(_帧模式):#MuxFrame
    """多路会话流帧载荷模式。"""
    pass#与基类相同纪律

class 宿主帧模式(_帧模式):#HostFrame
    """宿主信息流帧载荷模式。"""
    pass#与基类相同纪律
