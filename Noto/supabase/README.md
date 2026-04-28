# Supabase 配置

## 前置

- 在 https://supabase.com 创建新项目
- 记下 Project URL 和 service_role key（不是 anon key）

## 一次性初始化

在 Supabase Dashboard → SQL Editor 里执行 `migrations/0001_init.sql` 的全部内容。

## 关于 embedding 维度

默认 `vector(1024)` 对齐通义千问 text-embedding-v3。若你用 OpenAI text-embedding-3-small（1536 维）或其他维度，改掉这个数字并重建索引。**一旦导入数据，维度不可变，需清空 chunks 表后再改。**

## 写入 server/.env

```
NOTO_SUPABASE_URL=https://<ref>.supabase.co
NOTO_SUPABASE_SERVICE_KEY=<service_role_key>
```
