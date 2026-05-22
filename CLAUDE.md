# OneCompression Management System — コーディング標準

このリポジトリ固有のルール。グローバル `~/.claude/CLAUDE.md` と合わせて遵守すること。

## EC2 実行ルール（要件書 Section 11 より）

### Rule #3: pip 依存関係の事前検証
EC2 起動前に `pip install --dry-run` で依存パッケージを検証すること。
検証失敗は HTTP 422 を返し、EC2 を起動しない。
実装: `src/ocms/ec2/preflight.py` の `pip_dry_run_validate()`

### Rule #4: 大容量 S3 転送は in-region EC2 + Transfer Acceleration
日本→us-east-1 直接転送（1.6 MB/s）を避け、S3 Transfer Acceleration を有効にすること。
エンドポイント URL に `s3-accelerate` を含めること。
実装: `src/ocms/s3/upload.py`

### Rule #5: subprocess 内で --profile を使わない
EC2 userdata や SQS daemon の subprocess 呼び出しで `--profile` を絶対に使わないこと。
IAM ロールで認証すること。
pre-commit フック `no-aws-profile-in-subprocess` で機械的に検出。

### Rule #6: pgrep は set +e / set -e でガードする
```bash
set +e
pgrep -f onecomp
set -e
```

### Rule #7: EC2 停止後の自動終了
userdata スクリプトには必ず以下を含めること:
```bash
export POLL_EXIT_WHEN_TRAINING_EC2_NOT_RUNNING=1
```

### Rule #10: STATE_DIR は絶対パスで渡す
`STATE_DIR` 環境変数は必ず絶対パスを渡すこと。

## パッケージマネージャー

- **Python**: uv
- **Node.js (W4+)**: pnpm（npm 禁止）

## Takumi Guard

- pip/uv: Takumi Guard プロキシ (`pypi.flatt.tech`) を使う
- pnpm: `.npmrc` 参照 (`npm.flatt.tech`)
- トークン (`TAKUMI_GUARD_TOKEN`) は GitHub Secrets で管理

## セキュリティ

- AWS 認証情報・HF トークンは Secrets Manager / Parameter Store で管理
- コードに直接書かない

## TDD

- テストを先に書き、RED を確認してから実装する
- `tests/unit/` は DB なしで動く
- `tests/integration/` は PostgreSQL が必要（`@pytest.mark.integration`）

## Branch & PR

- 各 Week の実装は feature ブランチで進め、CI グリーン確認後にマージ
