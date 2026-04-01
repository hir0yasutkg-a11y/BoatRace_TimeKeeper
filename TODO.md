# Project TODO: ボートレース予測ダッシュボード

このファイルは、Hiroyasu（コヤマ）さん、Antigravity、Claude Codeの共同タスクボードです。
誰でも自由に項目を更新・追記・修正できます。

## 🏗️ 開発フェーズ: 実装・調整中

### 🔌 Claude Code 連携基盤 (Antigravity 担当)
- [x] `.claudeignore` の作成
- [x] `.claude/settings.json` の作成
- [x] `CLAUDE.md`（運用マニュアル）の作成
- [x] `TODO.md`（共有タスクボード）の作成

### 🛠️ バックエンド: スクレイピング強化 (Claude Code 担当予定)
- [ ] 丸亀（Marugame）競艇場の展示タイム・選手コメントの安定取得
  - [ ] 課題: HTMLセレクターが変動している可能性の調査
  - [ ] 対策: より堅牢なパースロジックの導入
- [ ] 節分（Tournament Day）判定ロジックのリファクタリング
  - [ ] 動的な開催日判定ができるように修正

### 🎨 フロントエンド: ユーザー体験向上
- [ ] スタートラインシミュレーターのデータ連携 (Mock -> 実データ)
- [ ] 予測アルゴリズムの可視化 (なぜその予測になったか)

## 🚧 Current Blockers / AI Notes

- **Antigravity Node**: Claude Code向けに連携設定を完了しました。Claude、準備ができたらバックエンドの「丸亀データ取得」から着手してください。
- **Claude Code Node**: (ここに現在の課題や詰まったポイントを記述)

## 📝 ログ・備忘録
- 2026-03-31: Claude Codeとの連携基盤を確立。「3回エラー詰まりルール」を導入。
