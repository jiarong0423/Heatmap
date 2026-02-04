# Heatmap

## Setup

建議建立虛擬環境並安裝相依套件：

```bash
# 建立並啟用虛擬環境（Linux / macOS）
python3 -m venv .venv
source .venv/bin/activate

# 升級 pip 並安裝依賴
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

若你在 dev container（或 codespace）內，直接執行：

```bash
python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt
```

安裝完成後，你可以在 Python 程式中匯入套件，例如 `yfinance`, `pandas` 等。
