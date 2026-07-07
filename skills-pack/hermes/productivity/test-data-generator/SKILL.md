---
name: test-data-generator
description: 生成测试用数据（虚拟用户/客户/订单/待办等），用于填充客户台账、API接口测试、Demo数据、前端占位等。免费无key，双源冗余。
---

# test-data-generator — 测试数据生成

## 触发条件
- "帮我生成10个测试客户"
- "填充台账demo数据"
- "需要一批假用户"
- "接口测试要示例数据"
- 前端页面需要占位数据展示

## 数据源（均已实测✅ 境内可达无key）

### 源1：randomuser.me（虚拟人物，含头像/邮箱/电话/地址）
```bash
# 生成 10 个随机用户
curl -sS "https://randomuser.me/api/?results=10"

# 指定国籍（中文姓名可用 nat=cn，但对中文支持一般）
curl -sS "https://randomuser.me/api/?results=10&nat=us,gb,fr,de"

# 指定性别
curl -sS "https://randomuser.me/api/?results=5&gender=female"

# 只要特定字段（减小 payload）
curl -sS "https://randomuser.me/api/?results=5&inc=name,email,phone,location"
```

**返回字段：** name / gender / location / email / login / dob / registered / phone / cell / id / picture / nat

### 源2：JSONPlaceholder（业务对象假数据 - 帖子/评论/相册/待办/用户）
```bash
# 用户列表
curl -sS "https://jsonplaceholder.typicode.com/users"

# 待办事项（100条）
curl -sS "https://jsonplaceholder.typicode.com/todos"

# 帖子（100条）
curl -sS "https://jsonplaceholder.typicode.com/posts"

# 相册/照片/评论
curl -sS "https://jsonplaceholder.typicode.com/albums"
curl -sS "https://jsonplaceholder.typicode.com/photos"    # 5000条
curl -sS "https://jsonplaceholder.typicode.com/comments"  # 500条
```

## 主人客户台账场景（SaaS乙方常用）

生成模拟客户列表用于填充/测试台账：

```bash
python3 <<'EOF'
import json, urllib.request, random, datetime
users = json.loads(urllib.request.urlopen("https://randomuser.me/api/?results=20&nat=us,gb,fr,de,es").read())["results"]
statuses = ["活跃","试用中","即将到期","已续费","流失风险"]
for i, u in enumerate(users, 1):
    company = f"{u['name']['last']} {random.choice(['Tech','Group','Ltd','Studio'])}"
    print(f"{i}\t{company}\t{u['email']}\t{u['phone']}\t{random.choice(statuses)}\t{(datetime.date.today() + datetime.timedelta(days=random.randint(-30,180))).isoformat()}")
EOF
```

## 使用注意

1. **randomuser.me 中文姓名效果差**——需要中文姓名建议本地生成（可用 Faker 库）
2. **JSONPlaceholder 数据固定**——不是每次都不同，只适合结构测试不适合大量随机
3. **不要用于生产**——这些是明显的测试数据，禁止入库为真实客户
4. **量级限制**：randomuser 单次最多 5000 条

## 中文本地生成兜底（无网络时）
```python
from faker import Faker
fake = Faker('zh_CN')
for _ in range(10):
    print(fake.name(), fake.company(), fake.email(), fake.phone_number())
```
