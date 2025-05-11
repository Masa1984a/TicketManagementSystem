# スクリプトの開始を通知
Write-Host "--- DevContainer 起動・接続スクリプト ---"

# --- Step 1: Podman machine の起動 ---
Write-Host "Podman machine 'claudeVM' を起動しています..."
try {
    # Podman machine start はすでに起動していれば何もしません
    # -q オプションで出力を抑制
    podman machine start claudeVM -q
    Write-Host "Podman machine 起動済みまたは起動しました。"
} catch {
    Write-Error "Podman machine の起動に失敗しました: $($_.Exception.Message)"
    exit 1 # エラーが発生したらスクリプトを終了
}

# --- Step 2: デフォルトコネクションの設定 ---
Write-Host "デフォルトの Podman コネクションを 'claudeVM' に設定しています..."
try {
    podman system connection default claudeVM
    Write-Host "デフォルトコネクションを設定しました。"
} catch {
    # このコマンドはすでに設定されている場合や、machine が起動していない場合に失敗する可能性があります
    # 致命的ではない場合もあるので警告として扱う
    Write-Warning "デフォルトの Podman コネクション設定に失敗しました (既に設定済みか machine の問題かもしれません): $($_.Exception.Message)"
    # ここではスクリプトを終了しない
}

# --- Step 3: DevContainer の起動 ---
Write-Host "現在のフォルダで DevContainer を起動しています..."
try {
    # devcontainer up はコンテナをビルド/起動し、必要なツールをインストールします
    # 実行中は標準出力に進捗が表示されます
    devcontainer up --workspace-folder . --docker-path podman
    Write-Host "DevContainer の起動処理が完了しました。"
} catch {
    Write-Error "DevContainer の起動に失敗しました: $($_.Exception.Message)"
    exit 1 # エラーが発生したらスクリプトを終了
}

# --- Step 4: DevContainer のコンテナIDを取得 ---
Write-Host "DevContainer のコンテナIDを検索しています..."
$currentFolder = (Get-Location).Path
# devcontainer up が設定するラベルを使ってコンテナを特定
# `podman ps` の出力から ID だけを抽出
# .Trim() で取得した文字列の不要な空白を削除
$containerId = $(podman ps --filter "label=devcontainer.local_folder=$currentFolder" --format "{{.ID}}").Trim()

if (-not $containerId) {
    Write-Error "現在のフォルダ ('$currentFolder') に対応する DevContainer のコンテナIDが見つかりませんでした。"
    Write-Error "'devcontainer up' が正常に完了し、コンテナが起動しているか確認してください。"
    exit 1 # コンテナが見つからない場合はスクリプトを終了
}
Write-Host "コンテナIDが見つかりました: $containerId"

# --- Step 5 & 6: コンテナ内でコマンドを実行し、インタラクティブシェルに入る ---
Write-Host "コンテナ ($containerId) 内で 'claude' コマンドを実行し、その後 zsh セッションを開始します..."
try {
    # podman exec -it はインタラクティブなセッションを開始します
    # zsh -c 'claude; exec zsh' の意味:
    #   zsh を非対話モードで起動し、以下のコマンドを実行
    #   'claude;' -> claude コマンドを実行
    #   'exec zsh' -> 現在のプロセス (非対話 zsh) を対話式 zsh に置き換える
    # これにより、claude コマンドが実行された後、自動的にインタラクティブな zsh プロンプトが表示されます。
    podman exec -it $containerId zsh -c 'claude; exec zsh'

    # このコマンドが実行されると、現在のPowerShellセッションはコンテナ内の zsh が終了するまで待機します。
    Write-Host "インタラクティブセッションが終了しました。"

} catch {
    Write-Error "コンテナ内でのコマンド実行に失敗しました: $($_.Exception.Message)"
    exit 1 # エラーが発生したらスクリプトを終了
}

# スクリプトの終了を通知
Write-Host "--- スクリプト完了 ---"