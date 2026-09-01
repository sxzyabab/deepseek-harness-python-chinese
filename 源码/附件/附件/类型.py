"""耐久附件词汇。对齐上游 attachment/src/types.ts。"""
__all__=[#仅中文公开名
    '图像媒体类型','图像附件引用','图像附件限额','编码图像附件',
    '保存图像附件','已存储图像附件','图像请求策略','请求图像附件',
]#公开面结束

图像媒体类型=('image/png','image/jpeg','image/webp','image/gif')#版本一路径接受的栅格格式

图像附件引用字段=(#耐久可序列化规范化图像引用
    'attachmentId',#不透明存储标识
    'mediaType',#经验证媒体类型
    'bytes',#编码字节长度
    'width',#内在宽
    'height',#内在高
)#引用字段结束

图像附件限额字段=(#部署解析限额
    'maxImageBytes',#单图最大编码字节
    'maxImagesPerMessage',#单消息最大图像数
    'maxMessageImageBytes',#单消息聚合图像字节
    'maxImagePixels',#单图最大像素
    'maxImageDimension',#单边最大像素
    'mediaTypes',#接受的媒体类型元组
)#限额字段结束

编码图像附件字段=(#线上 base64 上传
    'mediaType',#声明媒体类型
    'data',#规范 base64 数据
)#编码字段结束

保存图像附件字段=(#验证并提交一张图
    'data',#字节
    'mediaType',#声明媒体类型
)#保存字段结束

已存储图像附件字段=(#校验后读回
    'ref',#引用
    'data',#字节
)#已存储字段结束

图像请求策略字段=(#路由请求图像策略
    'maxPixels',#投影后最大宽乘高
    'maxBytes',#编码字节目标
)#策略字段结束

请求图像附件字段=(#缓存请求版本
    'variantId',#变体标识
    'attachment',#源规范化附件引用
    'data',#请求字节
    'mediaType',#媒体类型
    'bytes',#字节数
    'width',#宽
    'height',#高
    'depth',#样本深度
    'space',#色彩空间
    'hasAlpha',#是否保留 alpha
)#请求图像字段结束
