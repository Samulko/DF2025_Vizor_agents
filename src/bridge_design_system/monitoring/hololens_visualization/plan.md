# HoloLens三圆可视化系统 - 完整开发文档

## 📋 项目概述
本项目是一个专为HoloLens AR设备设计的三圆圈动态可视化系统，具备完全透明背景，圆圈悬浮在现实环境中，采用电竞动感风格。通过读取JSON数据实时更新圆圈大小和动画效果，为用户提供直观的参数可视化体验。

## 🎯 核心功能设计

### 统一动画管理器架构

**系统运行状态机：**
- **状态1：初始化启动状态** - 数字和圆圈同步随机变化（每0.5秒变2次），圆圈从点状缓慢生长
- **状态2：数据锁定状态** - 成功读取JSON后数字锁定，圆圈缓慢过渡到目标大小
- **状态3：稳定监听状态** - 数字静止，圆圈轻微呼吸浮动(±2-3px，3-4秒周期)
- **状态4：数据更新状态** - 检测到JSON变化时数字即时切换，圆圈重新过渡，更新计数器

**三圆圈动态显示：**
- Weight(红色#FF3030)、Storage(黄色#FFCC00)、Complexity(蓝色#3366FF)
- 圆圈大小范围：数字宽度/2+2px 到 数字宽度/2+50px
- 实时百分比显示：固定16-20px粗体字体
- 重叠区域特效：根据状态调整强度的竞技风格对抗效果
- 物理碰撞：圆圈边缘碰撞检测和轻微弹开效果
- 透明度变化：数值越低透明度越高（最低20%），保持固有颜色

### 透明背景AR体验

**完全透明背景：**
- 页面和容器背景完全透明
- 圆圈直接悬浮在真实环境画面上
- 无背景装饰，纯AR视觉效果
- 适配HoloLens全屏或无边框浏览器模式

### 数据驱动更新

**JSON数据接口：**
- 文件路径：../../design_profile.json
- 轮询频率：每500ms检查文件变化(仅在状态3时)
- 数据格式：{"Self-Weight": 20, "Storage": 60, "Complexity": 20, "timestamp": 1640995200000}
- 变化检测：通过timestamp比较判断数据更新
- 更新计数：显示"Updated N times"指示器

## 🏗️ 系统架构设计

### 统一动画管理器架构
```
AnimationManager (统一动画管理)
├── CollisionDetector (物理碰撞检测)
├── AnimationUtils (动画工具函数)
├── CircleElement (圆圈组件)
├── LabelDisplay (标签组件)
└── ThreeCircles (三圆圈协调)
```

### 状态机设计
```
状态1(启动) → 读取JSON成功 → 状态2(锁定) → 过渡完成 → 状态3(稳定)
    ↓                                              ↓
状态3(稳定) ← 过渡完成 ← 状态4(更新) ← 检测到变化 ← 状态3(稳定)
```

### 数据流设计
HoloLens透明界面 ↔ 状态机管理 ↔ design_profile.json ↔ Geometry Agent

### 工作流程：
1. 系统启动进入状态1，显示同步随机变化的数字和圆圈（每0.5秒变2次）
2. 首次成功读取JSON文件后转入状态2，数字锁定，圆圈缓慢过渡
3. 过渡完成后进入状态3，数字静止，圆圈开始呼吸浮动
4. 检测到JSON文件timestamp变化时转入状态4，数字即时更新，圆圈重新过渡，更新计数器

## 🔧 开发指南

### 核心API设计

#### 统一动画管理器接口
```javascript
// 动画管理器
const animationManager = new AnimationManager(renderEngine, dataManager);
animationManager.startAnimation();           // 开始动画
animationManager.updateAnimation(currentTime); // 更新动画
animationManager.switchToStableState(data);   // 切换到稳定状态

// 物理碰撞检测
const collisionDetector = new CollisionDetector();
collisionDetector.detectCollisions(circles);  // 检测碰撞
collisionDetector.handleCollision(circle1, circle2); // 处理碰撞
```

#### 状态机接口
```javascript
// 状态切换
const app = new App();
app.setState('initializing');  // 状态1
app.setState('locked');        // 状态2
app.setState('stable');        // 状态3
app.setState('updating');      // 状态4
app.setState('error');         // 状态5

// 状态监听
app.addEventListener('stateChanged', (newState) => {
    // 处理状态变化
});
```

#### 数据接口
```javascript
// 数据读取
const dataManager = new DataManager();
dataManager.addEventListener('dataChanged', (newData) => {
    // 处理数据变化
    updateCircles(newData);
});

// 状态相关数据处理
dataManager.startPolling();    // 开始轮询(状态3)
dataManager.stopPolling();     // 停止轮询
```

### 配置说明

#### 动画配置 (config/animations.json)
```json
{
    "animation": {
        "random": {
            "interval": 500,        // 随机动画间隔(0.5秒变2次)
            "minValue": 0,
            "maxValue": 100
        },
        "stable": {
            "breathingAmplitude": 2,
            "breathingPeriod": 4000,
            "microBreathing": true
        },
        "transition": {
            "duration": 650,
            "easing": "easeOutCubic"
        },
        "collision": {
            "threshold": 5,
            "pushForce": 0.1,
            "visualEffect": true
        }
    },
    "circles": {
        "weight": {
            "name": "Self-Weight",
            "color": "#FF3030",
            "position": {"x": 300, "y": 250},
            "minRadius": 12,
            "maxRadius": 60
        },
        "storage": {
            "name": "Storage", 
            "color": "#FFCC00",
            "position": {"x": 500, "y": 250},
            "minRadius": 12,
            "maxRadius": 60
        },
        "complexity": {
            "name": "Complexity",
            "color": "#3366FF", 
            "position": {"x": 400, "y": 400},
            "minRadius": 12,
            "maxRadius": 60
        }
    }
}
```

### 开发规范

**代码风格：** 使用2空格缩进，ES6+语法
**模块化：** 统一动画管理器架构，职责清晰
**注释：** JSDoc格式，复杂逻辑必须注释
**测试：** 在HoloLens和桌面浏览器中验证功能

### 功能扩展建议

**语音控制：** 集成语音命令调整参数
**手势优化：** 支持更复杂的HoloLens手势
**历史记录：** 参数变更历史和撤销功能
**多用户协作：** 支持多设备同时编辑

### 兼容性保证

✅ 不修改现有Geometry Agent代码
✅ 使用相同的数据文件和格式
✅ 保持现有系统的所有功能
✅ 提供额外的可视化和交互能力

## 📁 项目结构

```
bridge_design_system/
├── monitoring/
│   ├── design_profile.json              # 🔗 唯一的数据接口文件
│   └── hololens_visualization/          # 🆕 本项目
│       ├── index.html                   # 主入口页面(透明背景)
│       ├── assets/
│       │   ├── css/                     # 样式文件
│       │   │   ├── base.css             # 基础样式和透明背景
│       │   │   └── circles.css          # 圆圈样式和动画效果
│       │   ├── js/
│       │   │   ├── main.js              # 应用启动入口
│       │   │   ├── core/                # 核心系统模块
│       │   │   │   ├── app.js           # 应用状态机控制器
│       │   │   │   ├── dataManager.js   # JSON数据读取和轮询
│       │   │   │   └── renderEngine.js  # SVG渲染和动画引擎
│       │   │   ├── animation/           # 🆕 统一动画管理
│       │   │   │   ├── animationManager.js    # 主动画管理器
│       │   │   │   ├── collisionDetector.js   # 物理碰撞检测
│       │   │   │   └── animationUtils.js      # 动画工具函数
│       │   │   └── utils/               # 工具函数
│       │   │       ├── mathUtils.js     # 数学计算和动画
│       │   │       └── colorUtils.js    # 颜色处理和状态切换
│       │   └── config/                  # 配置文件
│       │       └── animations.json      # 动画配置和参数
│       └── docs/
│           ├── README.md                # 用户文档
│           └── plan.md                  # 开发计划
```


## 架构重构说明

### 重构目标
1. **统一动画管理：** 将分散的动画逻辑合并到AnimationManager
2. **动画同步优化：** 数字和圆圈完全同步（每0.5秒变2次）
3. **物理碰撞增强：** 添加圆圈边缘碰撞检测和弹开效果
4. **性能优化：** 减少文件数量，优化渲染性能

### 重构内容

#### 文件合并
- **合并前：** circleElement.js + labelDisplay.js + threeCircles.js
- **合并后：** animationManager.js (统一管理所有动画逻辑)

#### 动画同步
- **随机动画：** 统一间隔500ms（每0.5秒变2次）
- **状态切换：** 数字和圆圈完全同步
- **稳定状态：** 数字静止，圆圈微浮动

#### 物理碰撞
- **碰撞检测：** 圆圈边缘距离检测
- **弹开效果：** 轻微推力计算和应用
- **视觉反馈：** 碰撞时的强调效果

#### 更新计数器
- **数据变化：** 检测到JSON更新时计数
- **状态显示：** "Updated N times"指示器
- **持久化：** 计数器在会话期间保持

### 向后兼容性
- 保持原有的公共接口
- 提供兼容性别名
- 逐步迁移，平滑过渡

## 迭代升级路径

**Phase 1 → Phase 2 升级**
- 在现有圆圈基础上添加点击事件监听
- 增加动画引擎处理大小变化过渡
- 添加控制面板提供备用操作方式

**Phase 2 → Phase 3 升级**
- 集成数据写入功能
- 添加HoloLens专用手势处理
- 完善错误处理和状态监控

## 风险控制
- 每个Phase独立可用，可随时停止开发
- 向后兼容，新功能不影响现有功能
- 模块化设计便于调试和维护

---

**版本：** v1.1.0-Unified-Animation  
**最后更新：** 2025年7月5日  
**开发阶段：** Phase 1 - 统一动画管理器驱动的动态可视化  
**数据接口：** design_profile.json  
**设备支持：** HoloLens 2

# MVP 3 开发（暂时搁置）
## 可能性
我们的数据流是agent1(IA)（interview agent）to agent2(DA)(design agent) via design_profile.json，同时我们这个hololens的可视化也是via design_profile.json，这是Mvp想要实现的，单向捕捉。但后续如果我们发展了hololens的交互，是不是可以把hololens捕捉到的东西返给IA或者DA实现更新（甚至可以用agent的方式实现）?但是这一步暂时不实现，后续我们可以再想想。
目前只实现监听design_profile.json的变化，然后根据变化的内容，更新hololens的可视化。

## MVP Phase 3 - 数据写入集成（不一定）

**🔴 完善实现 (8个文件)：**
├── assets/css/hololens.css          # HoloLens适配
├── assets/js/core/dataWriter.js     # 数据写入
├── assets/js/components/statusIndicator.js # 状态显示
├── assets/js/interactions/gestureHandler.js # 手势处理
├── assets/js/interactions/inputHandler.js # 输入验证
├── assets/js/utils/fileIO.js        # 文件操作
├── assets/js/utils/logger.js        # 日志工具
├── assets/config/interactions.json  # 交互配置
├── assets/config/presets.json      # 预设配置
└── external/file_proxy.py          # 代理服务

**P3功能清单**
✅ 数据写回 design_profile.json
✅ HoloLens Air Tap手势支持
✅ 多策略文件写入(直接/代理)
✅ 预设参数快速选择
✅ 状态监控和错误提示
✅ 与Geometry Agent集成
✅ 完整的错误处理和降级

---




# HoloLens三圆可视化系统 - MVP Phase 2 开发提示词

## MVP Phase 2 - 基础交互功能

**🟡 P2新增文件 (7个)：**
├── assets/css/interactions.css          # 交互状态样式
├── assets/js/core/animationEngine.js    # 动画过渡效果
├── assets/js/components/controlPanel.js # 控制面板组件
├── assets/js/interactions/touchController.js # 基础点击/触摸
├── assets/js/interactions/dragHandler.js # 拖拽大小调整
├── assets/js/utils/eventBus.js          # 事件通信机制
└── assets/config/animations.json       # 动画参数配置

**P2功能清单**
✅ 点击圆圈进入编辑模式
✅ 拖拽调整圆圈大小
✅ 实时数值反馈
✅ 平滑动画过渡(800ms)
✅ 滑动条备用控制
✅ 基础错误处理

---




# HoloLens三圆可视化系统 - MVP Phase 1 完整开发提示词（逻辑修订版）

## 项目核心目标
开发一个运行在HoloLens浏览器中的三圆圈动态可视化系统，具备完全透明背景，圆圈悬浮在现实环境中，采用电竞动感风格，通过读取JSON数据实时更新圆圈大小和动画效果。

## 系统状态与动画逻辑

### 系统运行状态机

**状态1：初始化启动状态**
- 数字表现：从0开始快速随机变化（0-100随机数值，每500ms变化一次）
- 圆圈表现：从点状（半径0）缓慢生长，跟随数字随机变化调整大小
- 持续时间：直到第一次成功读取JSON文件
- 视觉效果：系统"寻找连接"的表现，充满动态感

**状态2：数据锁定状态**
- 触发条件：成功读取design_profile.json文件并获得有效数据
- 数字表现：立即停止随机变化，锁定显示JSON文件中的确切数值
- 圆圈表现：缓慢过渡到对应数值的目标大小（500-800ms过渡时间）
- 状态标识：数字停止跳动，系统进入"数据连接"状态

**状态3：稳定监听状态**
- 数字表现：保持显示当前JSON数据值，不再变化
- 圆圈表现：保持目标大小，开始轻微的呼吸浮动效果（±2-3px，3-4秒周期）
- 监听机制：每500ms轮询JSON文件变化
- 持续时间：直到检测到新的数据变化

**状态4：数据更新状态**
- 触发条件：检测到JSON文件timestamp变化
- 数字表现：即时切换到新数值（<50ms响应）
- 圆圈表现：停止呼吸动画，缓慢过渡到新的目标大小（500-800ms）
- 完成后：返回状态3（稳定监听状态）

**状态5：连接中断状态**
- 触发条件：JSON文件读取失败或格式错误
- 数字表现：显示上次有效数值，但开始闪烁警告
- 圆圈表现：保持上次大小，但发光效果变为红色警告
- 恢复机制：继续尝试读取，成功后返回对应状态

## 技术架构要求

### 平台与兼容性
- **目标设备：** HoloLens 2（主要）+ 桌面浏览器（测试）
- **技术栈：** 纯原生JavaScript + CSS3 + SVG，无第三方依赖
- **文件协议：** 支持file://本地文件访问
- **浏览器：** Edge、Chrome 90+、Safari 14+
- **分辨率：** 基准800x600，响应式适配

### 透明背景技术实现
- **页面透明：** html和body元素设置background: transparent
- **容器透明：** 所有div容器背景完全透明
- **无背景装饰：** 移除所有网格、线条、背景图案
- **浏览器模式：** 建议HoloLens使用全屏或无边框浏览器模式
- **AR效果：** 圆圈直接悬浮在真实环境画面上

## 数据接口规范

### 数据源配置
- **文件路径：** ../../design_profile.json（相对于index.html位置）
- **轮询频率：** 每500毫秒检查文件变化（仅在状态3时进行）
- **数据格式：**
```json
{
    "Self-Weight": 20,      // 0-100整数，对应红色圆圈
    "Storage": 60,          // 0-100整数，对应黄色圆圈  
    "Complexity": 20,       // 0-100整数，对应蓝色圆圈
    "timestamp": 1640995200000  // Unix时间戳，用于变化检测
}
```

### 数据处理逻辑
数据流：IA → DA → design_profile.json → HoloLens可视化（单向监听，不反写）

- **首次读取：** 启动后立即尝试读取，成功则从状态1转入状态2
- **变化检测：** 通过timestamp比较判断数据是否更新
- **数值映射：** 0-100数值线性映射到数字大小+2px到数字大小+50px圆圈半径
- **错误处理：** 读取失败进入状态5，JSON格式错误时触发错误动画
- **兼容性：** 向后兼容，缺失字段使用默认值

## 视觉设计规范

### 动感风格色彩方案
- **Weight圆圈：** #FF3030（鲜红色）高饱和度
- **Storage圆圈：** #FFCC00（亮黄色）高饱和度
- **Complexity圆圈：** #3366FF（电蓝色）高饱和度
- **强调色：** #FFFFFF（纯白色）用于闪光和高亮
- **透明背景：** 所有背景元素完全透明
- **透明度变化：** 数值越低透明度越高（最低20%），保持固有颜色

### 圆圈和数字尺寸设计
- **数字字体：** 固定16-20px粗体字体，确保清晰可读
- **圆圈半径范围：** 最小半径=数字宽度/2+2px，最大半径=数字宽度/2+50px
- **自适应尺寸：** 圆圈大小根据数字内容自动调整，确保数字不被截断
- **最小保证：** 即使数值为0，圆圈也要确保包围数字并留出2px边距

### 不同状态的视觉表现
- **状态1（启动）：** 数字和圆圈同步随机变化，正常颜色
- **状态2（锁定）：** 数字停止跳动，圆圈缓慢过渡，可有短暂闪光表示锁定
- **状态3（稳定）：** 数字静止，圆圈轻微呼吸浮动，正常颜色稳定发光
- **状态4（更新）：** 数字即时切换，圆圈停止呼吸开始过渡，可有更新闪光

## 动画效果规范

### 状态1：启动阶段动画
- **数字随机动画：** 0-100随机数值，每500ms变化，使用随机数生成器
- **圆圈生长动画：** 从半径0开始，跟随数字变化调整大小，有轻微延迟感
- **生长速度：** 圆圈变化比数字慢200-300ms，营造"追赶"效果
- **随机节奏：** 三个圆圈的随机变化略有时间差，避免完全同步

### 状态2：数据锁定动画
- **数字锁定：** 随机跳动立即停止，切换到JSON数据值
- **圆圈过渡：** 500-800ms缓慢过渡到目标大小，使用弹性缓动
- **锁定特效：** 数字切换瞬间可有短暂的白色闪光，表示数据锁定成功
- **同步完成：** 圆圈到达目标大小后，系统进入稳定状态

### 状态3：稳定监听动画
- **数字静止：** 完全静止，不再变化，保持清晰显示
- **呼吸浮动：** 圆圈围绕目标大小轻微变化（±2-3px）
- **呼吸节奏：** 3-4秒一个周期，使用正弦波函数
- **异步呼吸：** 三个圆圈呼吸节奏略有不同，营造自然感

### 状态4：数据更新动画
- **即时数字更新：** 数字立即切换到新值（<50ms）
- **停止呼吸：** 圆圈立即停止呼吸动画
- **大小过渡：** 500-800ms过渡到新的目标大小
- **更新特效：** 数字更新时短暂发光强化，圆圈可有冲击波效果
- **恢复呼吸：** 过渡完成后恢复呼吸浮动

### 透明度变化动画
- **数值映射：** 数值越低，透明度越高（最低20%）
- **颜色保持：** 圆圈始终保持固有颜色（红色、黄色、蓝色）
- **平滑过渡：** 透明度变化使用缓动函数，确保视觉舒适

### 重叠区域效果
- **状态相关：** 重叠效果根据当前状态调整强度
- **启动时：** 重叠区域随机变化，充满动感
- **稳定时：** 重叠区域稳定，轻微的竞技风格对抗效果
- **更新时：** 重叠区域产生能量冲突效果

## 文件结构与模块分工

### 13个必须实现的文件清单

**1. index.html - 主页面结构**
- 设置透明背景的HTML5文档结构
- 创建800x600的SVG画布容器
- 定义必要的SVG滤镜和渐变元素
- 加载所有CSS和JavaScript资源
- 提供基础的DOM结构和语义标记

**2. assets/css/base.css - 基础样式**
- 重置所有默认样式，设置透明背景
- 定义响应式布局和容器定位
- 设置固定字体大小和排版规范
- 提供工具类和通用样式
- 确保跨浏览器兼容性

**3. assets/css/circles.css - 圆圈样式**
- 定义不同状态下圆圈的外观样式
- 实现发光效果和描边样式
- 设置所有动画的CSS部分（呼吸、闪烁、警告）
- 定义重叠区域的混合模式
- 优化透明背景下的可见性

**4. assets/js/main.js - 应用启动**
- 应用程序主入口点和初始化流程
- 启动状态1的随机数字动画
- 初始化所有核心模块和组件
- 设置全局错误处理和异常捕获
- 启动首次JSON文件读取尝试

**5. assets/js/core/app.js - 应用控制器**
- 应用程序状态机管理和状态切换逻辑
- 协调不同状态下的动画行为
- 管理应用生命周期和资源清理
- 处理全局事件和状态变化
- 提供状态转换的统一接口

**6. assets/js/core/dataManager.js - 数据管理**
- 实现JSON文件的首次读取和轮询机制
- 管理不同状态下的数据处理逻辑
- 处理数据变化检测和状态切换触发
- 实现错误重试和状态5的错误处理
- 管理数据缓存和timestamp比较

**7. assets/js/core/renderEngine.js - 渲染引擎**
- SVG图形的创建、更新和管理
- 实现状态相关的动画系统
- 处理随机动画、呼吸动画、过渡动画的渲染
- 提供状态切换时的动画协调
- 优化重绘性能和内存使用

**8. assets/js/animation/animationManager.js - 统一动画管理器**
- 管理所有动画逻辑的统一入口
- 协调数字和圆圈的同步动画
- 处理状态切换时的动画过渡
- 管理物理碰撞检测和效果
- 提供动画性能优化

**9. assets/js/animation/collisionDetector.js - 物理碰撞检测**
- 实现圆圈边缘碰撞检测算法
- 计算碰撞推力和弹开效果
- 处理碰撞时的视觉反馈
- 优化碰撞检测性能
- 提供碰撞事件通知

**10. assets/js/animation/animationUtils.js - 动画工具函数**
- 提供统一的动画计算函数
- 实现缓动函数和动画插值
- 处理动画时间管理和同步
- 提供性能监控和优化工具
- 实现动画状态管理

**11. assets/js/utils/mathUtils.js - 数学工具**
- 实现随机数生成算法
- 提供各种缓动函数和状态相关的动画计算
- 实现呼吸动画的正弦波计算
- 提供自适应半径计算算法
- 实现性能优化的数学运算

**12. assets/js/utils/colorUtils.js - 颜色工具**
- 处理状态相关的颜色切换
- 实现正常颜色和警告颜色的转换
- 提供发光效果的颜色计算
- 处理透明背景下的颜色优化
- 实现动态颜色和亮度调整

**13. assets/config/animations.json - 动画配置文件**
- 定义三个圆圈的位置坐标
- 设置不同状态下的动画参数
- 配置随机数生成范围和呼吸动画参数
- 定义状态切换的时间常数
- 提供可调整的性能参数

## 🔗 文件关系与端口连接架构

### 核心文件依赖关系图

```
index.html (入口点)
├── 相对路径: assets/css/base.css
├── 相对路径: assets/css/circles.css
├── 相对路径: assets/js/main.js
    ├── 模块导入: assets/js/core/app.js
    ├── 模块导入: assets/js/core/dataManager.js
    ├── 模块导入: assets/js/core/renderEngine.js
    ├── 模块导入: assets/js/animation/animationManager.js
    │   ├── 组件依赖: assets/js/animation/collisionDetector.js
    │   └── 组件依赖: assets/js/animation/animationUtils.js
    ├── 工具导入: assets/js/utils/mathUtils.js
    ├── 工具导入: assets/js/utils/colorUtils.js
    └── 配置加载: assets/config/animations.json
```

### 数据流端口连接

**外部数据接口：**
- **输入端口：** `../../design_profile.json` (相对路径，相对于index.html)
- **输出端口：** 无 (Phase 1只读模式)
- **轮询端口：** 500ms定时器 (仅在状态3激活)
- **错误端口：** 控制台日志 + 视觉警告

**内部数据流管道：**
```
dataManager.js (数据读取层)
    ↓ JSON数据流
app.js (状态机处理层)
    ↓ 状态变化事件
renderEngine.js (渲染控制层)
    ↓ 动画指令流
animationManager.js (统一动画管理层)
    ↓ 组件更新指令
collisionDetector.js + animationUtils.js (动画渲染层)
```

### 模块间接口定义

**统一动画管理器接口 (animationManager.js)：**
```javascript
// 动画控制端口
startAnimation() → 开始统一动画循环
updateAnimation(currentTime) → 更新所有动画
switchToStableState(data) → 切换到稳定状态
// 碰撞检测端口
detectCollisions() → 检测所有圆圈碰撞
handleCollision(circle1, circle2) → 处理碰撞效果
// 性能监控端口
getAnimationStats() → 返回动画统计信息
getFPS() → 返回当前帧率
// 事件端口
addEventListener('animationComplete', callback) → 动画完成通知
addEventListener('collisionDetected', callback) → 碰撞检测通知
```

**状态机接口 (app.js)：**
```javascript
// 状态控制端口
setState(newState: string) → 触发全局状态切换
getCurrentState() → 返回当前状态
// 事件广播端口
addEventListener('stateChanged', callback) → 状态变化通知
removeEventListener('stateChanged', callback) → 移除监听
// 生命周期端口
initialize() → 初始化状态机
destroy() → 清理资源
```

**数据管理接口 (dataManager.js)：**
```javascript
// 数据读取端口
readData() → Promise<JSON|null> 返回JSON数据或null
getLastData() → 返回上次成功读取的数据
// 轮询控制端口
startPolling(interval: number) → 开始轮询(默认500ms)
stopPolling() → 停止轮询
isPolling() → 返回轮询状态
// 事件端口
addEventListener('dataChanged', callback) → 数据变化通知
addEventListener('dataError', callback) → 数据错误通知
// 配置端口
setDataPath(path: string) → 设置数据文件路径
getDataPath() → 返回当前数据文件路径
```

**渲染引擎接口 (renderEngine.js)：**
```javascript
// 渲染控制端口
updateCircles(data: object) → 更新圆圈显示
setAnimationState(state: string) → 设置动画状态
pauseAnimations() → 暂停所有动画
resumeAnimations() → 恢复所有动画
// 性能监控端口
getFPS() → 返回当前帧率
getRenderStats() → 返回渲染统计信息
// 配置端口
setRenderQuality(quality: string) → 设置渲染质量
```

### 相对路径配置规范

**关键相对路径定义：**
- **数据文件路径：** `../../design_profile.json` (相对于index.html位置)
- **配置文件路径：** `assets/config/animations.json` (相对于index.html)
- **CSS文件路径：** 
  - `assets/css/base.css` (基础样式)
  - `assets/css/circles.css` (圆圈样式)
- **JS模块路径：**
  - `assets/js/main.js` (主入口)
  - `assets/js/core/` (核心模块目录)
  - `assets/js/animation/` (动画模块目录)
  - `assets/js/utils/` (工具模块目录)

**路径验证机制：**
```javascript
// 路径验证函数
function validatePaths() {
    const paths = [
        '../../design_profile.json',
        'assets/config/animations.json',
        'assets/js/main.js',
        'assets/css/base.css'
    ];
    // 验证所有关键路径是否可访问
}
```

### 组件间通信协议

**事件驱动架构：**
```
main.js (事件总线中心)
├── app.js (状态变化事件源)
├── dataManager.js (数据变化事件源)
├── renderEngine.js (渲染完成事件源)
└── animationManager.js (动画更新事件源)
```

**数据传递格式：**
```javascript
// 状态事件数据格式
{
    type: 'stateChanged',
    state: 'initializing|locked|stable|updating',
    timestamp: Date.now(),
    previousState: string,
    data: object
}

// 动画更新数据格式
{
    type: 'animationUpdated',
    id: 'weight|storage|complexity',
    value: number,
    radius: number,
    color: string,
    animation: string,
    state: string
}

// 碰撞事件数据格式
{
    type: 'collisionDetected',
    circle1: {id: string, position: {x, y}, radius: number},
    circle2: {id: string, position: {x, y}, radius: number},
    distance: number,
    pushForce: number
}

// 数据变化事件格式
{
    type: 'dataChanged',
    data: {
        'Self-Weight': number,
        'Storage': number,
        'Complexity': number,
        'timestamp': number
    },
    previousData: object,
    timestamp: Date.now(),
    updateCount: number
}
```

### 配置参数接口规范

**animations.json配置结构：**
```json
{
    "animation": {
        "random": {
            "interval": 500,        // 随机动画间隔(0.5秒变2次)
            "minValue": 0,
            "maxValue": 100
        },
        "stable": {
            "breathingAmplitude": 2,
            "breathingPeriod": 4000,
            "microBreathing": true
        },
        "transition": {
            "duration": 650,
            "easing": "easeOutCubic"
        },
        "collision": {
            "threshold": 5,
            "pushForce": 0.1,
            "visualEffect": true
        }
    },
    "circles": {
        "weight": {
            "name": "Self-Weight",
            "color": "#FF3030",
            "position": {"x": 300, "y": 250},
            "minRadius": 12,
            "maxRadius": 60,
            "animationOffset": 0
        },
        "storage": {
            "name": "Storage",
            "color": "#FFCC00", 
            "position": {"x": 500, "y": 250},
            "minRadius": 12,
            "maxRadius": 60,
            "animationOffset": 1200
        },
        "complexity": {
            "name": "Complexity",
            "color": "#3366FF",
            "position": {"x": 400, "y": 400},
            "minRadius": 12,
            "maxRadius": 60,
            "animationOffset": 2400
        }
    },
    "performance": {
        "targetFPS": 60,
        "pollingInterval": 500,
        "renderQuality": "high"
    }
}
```

**Field Mapping for Data Adaptation (Future-Proofing)**

In case your data source uses different field names than the visualization expects (for example, "surface_area" instead of "self_weight"), you can add a `field_map` section to the configuration. The visualization will use this mapping to display the correct values for each circle.

**Example field_map usage:**
```json
"field_map": {
  "weight": "surface_area",
  "storage": "timber_layers",
  "complexity": "complexity"
}
```

This means:
- The "weight" circle will use the value from the "surface_area" field in your data
- The "storage" circle will use the value from the "timber_layers" field
- The "complexity" circle will use the value from the "complexity" field

If no field_map is provided, the visualization will use the default field names ("self_weight", "storage", "complexity").


// =======================
// 建议的结构（可选方案）
// =======================
// {
//   "ratings": {
//     "surface_area": 2,
//     "timber_layers": 3,
//     "complexity": 4
//   },
//   "percentages": {
//     "surface_area": 22.2,
//     "timber_layers": 33.3,
//     "complexity": 44.4
//   }
// }
// =======================

**运行时配置管理：**
```javascript
// 配置加载端口
loadConfig(path: string) → Promise<object> 返回配置对象
// 配置更新端口
updateConfig(newConfig: object) → 应用新配置
// 配置验证端口
validateConfig(config: object) → boolean 返回验证结果
// 配置重置端口
resetConfig() → 重置为默认配置
```

### 状态同步机制

**状态传播链：**
```
app.js (状态变更源)
    ↓ 广播状态变化事件
├── dataManager.js (停止/启动轮询)
├── renderEngine.js (切换动画模式)
├── animationManager.js (更新动画状态)
├── collisionDetector.js (更新碰撞检测)
└── animationUtils.js (更新动画工具)
```

**状态一致性保证：**
- **单一状态源：** app.js作为唯一状态管理器
- **事件驱动：** 所有状态变化通过事件广播
- **原子操作：** 状态切换为原子操作，避免中间状态
- **错误恢复：** 状态异常时自动恢复到安全状态
- **状态验证：** 每次状态切换前验证状态有效性

### 性能监控端口

**性能指标接口：**
```javascript
// 帧率监控
getFPS() → number 返回当前帧率
getAverageFPS() → number 返回平均帧率
// 内存监控
getMemoryUsage() → object 返回内存使用情况
// 状态监控
getStateInfo() → object 返回当前状态信息
// 错误监控
getErrorLog() → array 返回错误日志
// 性能统计
getPerformanceStats() → object 返回性能统计信息
```

## 验收标准

### 状态机逻辑验收
- ✅ 启动时显示同步随机变化的数字和圆圈（每0.5秒变2次）
- ✅ 首次读取JSON成功后数字立即锁定，圆圈缓慢过渡
- ✅ 数据稳定时数字静止，圆圈保持轻微呼吸浮动
- ✅ 修改JSON文件时数字即时更新，圆圈重新过渡，更新计数器

### 动画效果验收
- ✅ 状态1：数字和圆圈每500ms同步变化
- ✅ 状态2：数字停止跳动，圆圈500-800ms过渡到目标
- ✅ 状态3：数字完全静止，圆圈3-4秒周期轻微浮动
- ✅ 状态4：数字即时切换，圆圈停止呼吸重新过渡
- ✅ 透明度变化：数值越低透明度越高（最低20%），保持固有颜色

### 物理碰撞验收
- ✅ 圆圈边缘碰撞检测正常工作
- ✅ 碰撞时产生轻微弹开效果
- ✅ 碰撞触发视觉强调效果
- ✅ 碰撞检测不影响动画性能

### 视觉效果验收
- ✅ 页面背景完全透明，可看到现实环境
- ✅ 数字始终清晰可读，圆圈大小自适应
- ✅ 不同状态下视觉效果明显区分
- ✅ 圆圈在任何环境光线下都清晰可见
- ✅ 整体效果符合电竞动感风格
- ✅ 圆圈保持固有颜色，透明度随数值变化

### 技术性能验收
- ✅ 所有状态切换流畅无卡顿
- ✅ 随机动画和呼吸动画保持60fps
- ✅ 长时间运行无内存泄漏
- ✅ 浏览器控制台无JavaScript错误

## 开发重点与注意事项

### 统一动画管理器核心实现
- 清晰的动画状态定义和切换逻辑
- 数字和圆圈动画的完全同步
- 不同状态下的行为差异化实现
- 物理碰撞检测和效果处理

### 动画系统核心
- 随机动画和确定性动画的切换
- 呼吸动画的平滑启动和停止
- 数字即时更新和圆圈延迟跟随的协调
- 状态切换时避免动画冲突

### 数据处理核心
- 首次读取和轮询机制的分离
- timestamp比较的准确性
- 错误处理和重试逻辑
- 状态切换触发的时机控制

### 透明背景适配
- 所有状态下的可见性保证
- 错误状态的明显视觉提示
- 在不同环境光线下的显示效果
- HoloLens AR环境的优化

---

### User Interface Language Requirement

All user interface text, status messages, prompts, and comments must be in English. This includes:
- All status indicators (e.g., 'Initializing...', 'Connection Error', etc.)
- All button labels, tooltips, and prompts
- All user-facing error or info messages
- All developer comments in code

This ensures the system is ready for international use and is clear to all users and developers.



