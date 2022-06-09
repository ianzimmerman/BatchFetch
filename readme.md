# Step 1
Create a virtual env with python 3.8+

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

# Step 2
Rename core/apis/config.py.temp to config.py and supply API tokens

# Step 3
Run it from your venv
```
source .venv/bin/activate # if needed
python fetch.py /path/to/input.csv -c url -f project_name --api_key=XXXXXXXXXXXXXXXXXXX
```
