## 最简单发送一封纯文本邮件

```python
import smtplib
from email.message import EmailMessage

msg = EmailMessage()
msg["Subject"] = "测试邮件"
msg["From"] = "你@example.com"
msg["To"] = "接收@example.com"
msg.set_content("这是一封通过 smtplib 发送的邮件")

with smtplib.SMTP("smtp.example.com", 587) as smtp:
    smtp.starttls()  # 开启TLS加密
    smtp.login("你@example.com", "密码或授权码")
    smtp.send_message(msg)
```

### 465端口（SSL 连接）示例

```python
with smtplib.SMTP_SSL("smtp.qq.com", 465) as smtp:
    smtp.login("你的QQ@qq.com", "授权码")
    smtp.send_message(msg)
```

### 发送 HTML 邮件

```python
msg.set_content("这是备选纯文本")
msg.add_alternative("""
<h2>你好</h2>
<p>这是一封<b>HTML邮件</b></p>
""", subtype="html")
```

### 发送带附件的邮件

```python
with open("test.pdf", "rb") as f:
    msg.add_attachment(f.read(), maintype="application",
                       subtype="pdf", filename="test.pdf")

```

### 发送 HTML + 内嵌图片 (CID)
```python
msg.add_alternative("""
<html>
  <body>
    <h3>这是一张内嵌图片</h3>
    <img src="cid:img_001">
  </body>
</html>
""", subtype="html")

with open("pic.jpg", "rb") as f:
    msg.get_payload()[1].add_related(
        f.read(), "image", "jpeg", cid="img_001"
    )

```

## 三合一邮件模板（✅ HTML + 纯文本兜底 + 内嵌 CID 图片 + 普通附件）

### ✅ 结构说明

```
mixed
 ├─ related
 │   └─ alternative
 │        ├─ text/plain
 │        └─ text/html  ← 内含 <img src="cid:img1">
 │   └─ image/png  ← CID 内嵌图片
 └─ attachment.pdf ← 普通附件
```

### Python 代码示例

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email.header import Header

# ---------- 你的邮件配置 ----------
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
USERNAME = "你的邮箱@qq.com"
PASSWORD = "你的授权码"  # 不是邮箱密码，是SMTP授权码
TO = "收件邮箱@example.com"

# ---------- 构建 MIME 结构 ----------
msg = MIMEMultipart("mixed")
msg["Subject"] = Header("测试邮件：HTML + CID图片 + 附件", "utf-8")
msg["From"] = USERNAME
msg["To"] = TO

# related（HTML + 内嵌资源）
related = MIMEMultipart("related")

# alternative（纯文本 + HTML）
alternative = MIMEMultipart("alternative")
text = MIMEText("这是纯文本备胎内容，若HTML不支持会显示此内容", "plain", "utf-8")

html = MIMEText("""
<html>
  <body>
    <h2 style="color:#4CAF50">这是一封带内嵌图片 + 附件的邮件</h2>
    <p>下面是内嵌图片（CID方式，不是附件）：</p>
    <img src="cid:img1" width="300">
  </body>
</html>
""", "html", "utf-8")

alternative.attach(text)
alternative.attach(html)

# 读取内嵌图片并设置 CID
with open("image.png", "rb") as f:
    image = MIMEImage(f.read())
    image.add_header("Content-ID", "<img1>")  # HTML里用 cid:img1 访问
    image.add_header("Content-Disposition", "inline", filename="image.png")

related.attach(alternative)
related.attach(image)

# 普通附件
with open("file.pdf", "rb") as f:
    attachment = MIMEApplication(f.read())
    attachment.add_header("Content-Disposition", "attachment", filename="report.pdf")

# 组合到最外层
msg.attach(related)
msg.attach(attachment)

# ---------- 发送邮件 ----------
with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
    smtp.login(USERNAME, PASSWORD)
    smtp.sendmail(USERNAME, TO, msg.as_string())

print("✅ 发送成功")

```