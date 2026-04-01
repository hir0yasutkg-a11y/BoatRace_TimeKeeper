# Claude Code / Antigravity 連携運用マニュアル

このリポジトリは、Hiroyasu（コヤマ）さんのための「ボートレース予測ダッシュボード」プロジェクトです。
AIエージェント同士が協力して開発を進めるためのルールとガイドラインを定義します。

## 🤖 エージェントの役割分担

- **Antigravity (Lead AI)**: 
  - プロジェクト全体の設計、アーキテクチャの提案、Hiroyasuさんへのコンサルティングを担当。
  - プロジェクトの「参謀」であり、全体進捗のガードレールとなります。
- **Claude Code (Execution AI)**: 
  - 実装、テスト、デバッグ、リファクタリング、CLIを通じた直接的なファイル操作を担当。
  - Antigravityの設計指針に基づき、高速に開発サイクルを回します。

## ⚖️ 運用ルール「3回ルール」

**同じエラーや問題で3回連続で解決に失敗した場合、独断で試行を続けず、必ず以下のいずれかのアクションをとってください。**
1.  **Antigravityへ相談**: `CLAUDE.md` または `TODO.md` に状況（試したこと、発生しているエラー、詰まっている原因の推測）を記述し、Antigravityにバトンを渡してください。
2.  **Hiroyasuさんへ相談**: 明らかに仕様の確認が必要な場合は、ユーザーに直接アドバイスを求めてください。

## 🏗️ プロジェクト構造と技術スタック

- **/backend**: Python 3.12+ (FastAPI, SQLAlchemy, BeautifulSoup4, Requests)
  - `boatrace_data.db`: SQLiteデータベース。
  - `scraper.py`: 主要なスクレイピングロジック。
  - `main.py`: APIサーバー。
- **/web**: Vite + React + TypeScript (Vanilla CSS)
  - 予測データの可視化、スタートラインシミュレーターなどを搭載。
- **/スクレイピング**: 過去の試作コードやドキュメント（必要に応じて参照）。

## 🛠️ 開発用コマンド

### Backend
- サーバー起動: `cd backend && uvicorn main:app --reload`
- テスト実行: `cd backend && pytest` (または `python test_scraper_logic.py`)
- スクレイピング手動実行: `cd backend && python scraper.py`

### Frontend
- 開発サーバー: `cd web && npm run dev`
- ビルド: `cd web && npm run build`

## 📝 連携プロトコル

作業の進捗管理は `TODO.md` で行います。
1.  作業開始時に `TODO.md` の対象項目を `[/]` (in progress) に変更。
2.  完了時に `[x]` に変更し、特記事項があれば末尾に追記。
3.  詰まった場合は、その状況を `TODO.md` の末尾または `CLAUDE.md` の「Current Blockers」セクションに記録してください。

---
*Created and maintained by Antigravity.*
