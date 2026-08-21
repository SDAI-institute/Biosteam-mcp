# Environment setup

The tutorials run on **Python 3.11** in the existing **`envShilab`** conda env.

## 1. Activate the env

```powershell
conda activate envShilab
python --version   # expect Python 3.11.x
```

## 2. Install the stack

```powershell
cd "D:\01code\Projects\SDAI- Ecosystem\Biosteam"
pip install -r environment/requirements.txt
```

This pulls a large tree â€” `biosteam` brings `thermosteam` + `chemicals`, and `qsdsan`
builds on `biosteam`. Expect a few minutes on first install.

