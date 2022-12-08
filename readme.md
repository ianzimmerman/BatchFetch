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
## Run it from your venv
```
source .venv/bin/activate # if needed
python fetch.py /path/to/input.csv -c Address -f project_name
```

## Modes:
```
    -c : column in CSV file with URL or Keyword in it
    -t or --text : Optional (Runs as default). Run natural language processing and extract metadata from URL supplied in column -c. Default Mode.
    -s or --seo  : Optional (Not run unless flagged). Get keyword data for each URL supplied in column -c. Keywords & Monthly volumes, (creates 2 output files)
    -k or --keywords : (Not run unless flagged). Expects a phrase in column -c and extracts volumes from SEMRush exclusive of -t and -s
```

## Options:
```
    -d or --delay : Time (in seconds) to wait between requests. Default: 1.5
    -o or --offset : Number of rows to skip in CSV. Default: 0
    -l or --limit : Max rows to process. Default: 100,000
```

## Examples
```
    # Run a test on the first 100 rows with no delay:
    python fetch.py /path/to/input.csv -c Address -f "My Project" -t -s -d 0 -l 100

    # Fetch Rows 101-200:
    python fetch.py /path/to/input.csv -c Address -f "My Project" -o 100 -l 100  
```


# Warnings
SEO and Keyword flags require an SEMRush API Key