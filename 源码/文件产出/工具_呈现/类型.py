"""present 工具产出的耐久文件交付类型面。

公开面仅中文名。线协议字段 path / description 与事件名 deliverables/presented 保持英文。

已呈现文件：跨包 dict，键为 path（必填字符串）与可选 description。

会话事件 deliverables/presented：载荷为 { turn, callId, files }，files 为已呈现文件列表。
"""
__all__=['已呈现文件字段']#仅中文公开名

#已呈现文件的线协议字段：path 必填，description 可选。
已呈现文件字段=('path','description')
