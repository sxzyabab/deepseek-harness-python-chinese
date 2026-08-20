"""共享的浏览器平台模块说明符。

对齐上游 `web/src/platform.ts`。公开面仅中文名。播种、打包 externals 与 Vite 别名都消费本列表。
"""

__all__=['平台模块表']#仅中文公开名

平台模块表=(#平台模块说明符
    'react',
    'react/jsx-runtime',
    'react-dom',
    'react-dom/client',
    '@deepseek-ai/cordis',
    '@deepseek-ai/dsh-client-ui-slots',
    '@deepseek-ai/dsh-client-web-react',
    '@deepseek-ai/dsh-client-ui-primitives',
    '@deepseek-ai/dsh-client-ui-attachment',
    '@deepseek-ai/dsh-client-schema-form',
)#只读元组
