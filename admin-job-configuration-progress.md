# Admin Job Configuration 功能开发进展

## 1. 任务背景

本次任务的目标是为 RecruitDirect 系统新增一个管理员专用的 Job Configuration 页面，用于查看和修改 Job 级别的系统配置。

当前计划支持以下四个配置项：

- Resume Process Limit
- Interview Limit
- Resume Process Model
- Interview Model

该功能整体被拆分为五个开发层次：

1. 前端页面层
2. 前端权限与路由层
3. 前端 Store / API 层
4. Java API 与业务层
5. 数据库层

目前已完成前两个层次。

---

## 2. 前期项目分析

在开始开发前，我先阅读并整理了整个项目的结构。当前系统主要由三个项目组成：

```text
recruitdirect-web      Vue 3 前端
webservice             Java Spring Boot 主后端
automateservice        Python AI 面试服务
```

另外还有：

```text
design-store           UI 设计稿和前端原型
```

本次任务主要涉及：

```text
recruitdirect-web
webservice
```

暂时不涉及 Python 实时面试服务。

根据现有系统结构，最终功能调用链计划为：

```text
JobConfiguration.vue
    ↓
Pinia Store
    ↓
Java REST API
    ↓
JobController
    ↓
JobService
    ↓
JobRepository
    ↓
Job Entity
    ↓
MySQL
```

---

## 3. 已完成工作

### 3.1 前端页面层

新增文件：

```text
src/views/admin/JobConfiguration.vue
```

该页面目前已实现以下功能：

- 输入 Job ID
- 点击按钮加载 Job Configuration
- 展示 Job 基本信息
- 编辑 Resume Process Limit
- 编辑 Interview Limit
- 编辑 Resume Process Model
- 编辑 Interview Model
- 必填字段校验
- 正整数校验
- Loading 状态
- Saving 状态
- 成功提示
- 错误提示
- 响应式页面布局

页面中展示的 Job 基本信息包括：

- Job Title
- Company
- Job Status

为了先独立验证页面逻辑，目前加载和保存使用的是 mock data，尚未连接真实后端。

当前模拟数据包括：

```text
Job Title: Software Engineer
Company: Avary
Status: ACTIVE

Resume Process Limit: 100
Interview Limit: 50
Resume Process Model: gpt-4o-mini
Interview Model: gpt-4o
```

模型字段使用了 `v-combobox`，因此既可以选择现有模型，也可以兼容后端未来返回的新模型名称。

#### 页面层验证结果

已验证：

- 页面可以正常编译
- 页面可以通过开发服务器正常打开
- Job ID 输入和加载逻辑正常
- 加载后能够展示 Job 信息和四个配置项
- 0、负数和小数不能通过 Limit 校验
- 空 Model 值不能通过校验
- 合法数据可以完成模拟保存
- Loading、Success 和 Error 状态正常
- 浏览器控制台未发现运行时错误
- 页面在不同宽度下能够正常显示

---

### 3.2 前端权限与路由层

修改文件：

```text
src/router/MainRoutes.ts
src/router/index.ts
src/layouts/full/vertical-sidebar/sidebarItem.ts
```

参考并复用了现有文件中的权限逻辑：

```text
src/layouts/full/vertical-sidebar/VerticalSidebar.vue
src/stores/authUser.ts
```

#### 正式路由

临时测试路由：

```text
/test/job-configuration
```

已经替换为正式路由：

```text
/admin/job-configuration
```

该路由增加了：

```ts
meta: {
    requiresAdmin: true
}
```

#### 侧边栏入口

在左侧菜单中新增：

```text
Job Configuration
```

该菜单项配置为：

```ts
requiresAdmin: true
```

因此只有：

```text
userData.role === "admin"
```

的用户可以看到。

#### 路由权限控制

在全局 Router Guard 中增加了 Console Admin 权限判断。

权限逻辑为：

```text
未登录
→ 跳转 /auth/login

已登录但不是 admin
→ 跳转 /interview/joblist

admin
→ 允许访问 /admin/job-configuration
```

该控制不仅隐藏菜单，也阻止非管理员直接输入 URL 访问页面。

#### 权限层验证结果

已验证管理员状态：

- 管理员可以看到 Job Configuration
- 管理员可以进入 `/admin/job-configuration`
- 其他管理员专用菜单正常显示

已通过本地角色模拟验证非管理员状态：

- Job Configuration 菜单被隐藏
- Dashboard、Interviews、Job Dashboard、Add Company 等管理员菜单也被隐藏
- 普通菜单仍正常显示
- 非管理员权限过滤逻辑能够生效

由于目前提供的普通测试账号属于 B2C Customer 认证体系，而本页面属于 Console / Hiring Client 认证体系，因此真实 Console 非管理员账号验证尚未完成。

当前非管理员验证使用的是本地模拟 Console 非管理员角色。

---

## 4. 当前修改文件

目前前端代码修改包括：

```text
modified:
src/layouts/full/vertical-sidebar/sidebarItem.ts
src/router/MainRoutes.ts
src/router/index.ts

new:
src/views/admin/JobConfiguration.vue
```

当前开发分支：

```text
admin-job-configuration
```

该分支独立于 `main`，不会直接影响其他开发人员的代码。

---

## 5. 当前完成程度

五个开发层次的当前状态：

```text
[完成] 1. 前端页面层
[完成] 2. 前端权限与路由层
[待开发] 3. 前端 Store / API 层
[待开发] 4. Java API 与业务层
[待开发] 5. 数据库层
```

当前整体完成度约为：

```text
40%
```

目前已经完成页面、菜单、路由和前端权限框架。

尚未完成的部分主要是：

- 页面接入真实 Store
- 前端调用真实 API
- Java 后端增加查询和更新接口
- Job Entity 增加字段
- 数据库增加字段和 migration
- 前后端联调
- 使用真实数据完成最终验证

---

## 6. 下一步计划

下一步将开始第三层：前端 Store / API 层。

计划包括：

- 在 `src/stores/jobList.ts` 中增加管理员配置查询方法
- 增加管理员配置更新方法
- 定义前端配置数据类型
- 将页面中的 mock load 替换为真实 Store 调用
- 将页面中的 mock save 替换为真实 Store 调用
- 统一处理接口错误
- 完成页面到 Store 层的独立验证

之后继续完成：

- Java Controller
- Java Service
- Request / Response DTO
- Job Entity
- Job Repository
- 数据库字段
- Migration SQL
- 前后端联调

---

## 7. 当前限制

目前页面仍然使用 mock data，因此当前版本只能验证：

- 页面结构
- 表单交互
- 表单校验
- 菜单权限
- 路由权限

当前版本还不能：

- 从数据库读取真实 Job Configuration
- 保存真实 Job Configuration
- 让 Resume Pipeline 使用新的 Resume Process Limit 和 Model
- 让 Interview Pipeline 使用新的 Interview Limit 和 Model

这些能力将在后续三个层次中完成。

---

## 8. 当前状态总结

目前 Admin Job Configuration 功能已经完成前端基础部分。

已完成：

- 独立管理员页面
- 四个配置项
- 表单校验
- 页面状态反馈
- 正式路由
- 管理员菜单
- 管理员路由保护
- 本地页面验证
- 管理员和模拟非管理员权限验证
- 独立 Git 分支

当前代码已准备提交到：

```text
admin-job-configuration
```

后续将继续完成 Store、Java 后端、数据库和完整联调。
