__all__=[#仅中文公开名
    '排除','工作区排除','页面资源','镜像入口种子',
]#公开面结束

排除=[#从每个已收集树丢掉的路径
    'tests/**',#测试树
    'test/**',#测试树
    '__tests__/**',#双下划线测试树
    'coverage/**',#覆盖率
    '**/*.map',#sourcemap
    '**/*.tsbuildinfo',#tsc增量
    '**/*.tgz',#归档
    '**/*.tar',#归档
    '**/*.tar.gz',#归档
    '**/*.d.ts',#声明
    '**/*.d.mts',#声明
    '**/*.d.cts',#声明
]#排除结束

工作区排除=[#仅对workspace与vendored包额外丢掉
    'src/**',#源码
    'dist/**',#页面资源树
]#工作区排除结束

页面资源=[#属于PAGE、不属于worker加载器的镜像路径
    'node_modules/*/lib/client.js',#非作用域client
    'node_modules/@*/*/lib/client.js',#作用域client
]#页面资源结束

镜像入口种子=[#worker装配在组合roster之外直接require的说明符
    '@deepseek-ai/dsh-app-boot',#boot
    '@deepseek-ai/dsh-cmdline',#cmdline
    '@deepseek-ai/cordis',#cordis
    '@deepseek-ai/cordis-plugin-include',#include
    'js-yaml',#yaml
]#镜像入口种子结束
