# HFRNet
HFRNet is a python package designed to process radial velocities measured by HF-RADAR to total solutions and other derived products.

[[_TOC_]]

## Important Resources
- __[Google Drive](https://drive.google.com/drive/folders/12joE1XzYbQWOT3Yez3ye7HmyPhhYnNPF)__
- __[Algorithm Support Document](https://docs.google.com/document/d/1QUiUwgeGr3LINf9lBWBIfja_m__yLKfTMWHam_f_Ooo/edit?tab=t.0#heading=h.gjdgxs)__
- __[Code Update Summary](https://docs.google.com/spreadsheets/d/1LFEU2PCXZDM0KcnGfjPqYXrtLYVtOh98xbwcV25BseE/edit?usp=sharing)__
- __[ASSISTT Delivery Schedule](https://docs.google.com/spreadsheets/d/107vHNeHh7s_z-1HO9KGt1te7pxqu-h7eMuOyrDKvQd8/edit?pli=1#gid=1641027802)__
- __[R2O Team Lookup](https://docs.google.com/spreadsheets/d/1u42Lu2QawJOKzCguXlfWYdcWOYyotDFGkkXkeyXCJCk/edit#gid=616569363)__

## Code Base Requirements
- Uses gitLFS: Yes
- Uses submodules: Yes

### System Requirements
- Unit Name: HFRNet
- Clock Time: ~5 min (depends on the process)
- Max Memory: ~15 GB
- CPU Usage: 1 CPU

### Library Packages Required
#### Needed in the Run Time Environment
- __Python__: see `conda_environment.yaml

#### Needed in the Compiled Time Environment
- N/A

### Extra Files Needed
- N/A

## Compiling the Code
- N/A


## Running the Code
Find the current Production rules in the Google Drive Folder above.

### HFRNet:
#### Command Line Interface
```bash
conda activate hfrnet_env
export PYTHONPATH=/path/to/repo/packages
python -m hfrnet.run_rtv /path/to/config.yaml
```

#### Config Yaml
```yaml
processing:
   domain: ushi
   resolution: 6km
   batch_processing: 'true'
time:
   start_date: '202301040000000'
   end_date:   '202301040000000'
production:
   site: PLAIT
   environment: INT
   version: v1r0
directory:
   algorithm_dir: /data/home004/milap.patel/Projects/HFR/hfrnet_nccfgit/hfrnet
   log: /data/home004/milap.patel/Projects/HFR/hfrnet_nccfgit/hfrnet/packages/test
   output: /data/home004/milap.patel/Projects/HFR/hfrnet_nccfgit/hfrnet/packages/test
   radial_local_dir: /data/smcd12/ASSISTT_DATA/HFRnet/SFTP/radials
   interm_local_dir: ''
   output_s3_bucket: ''
   output_intermed_s3_bucket: ''

databases:
   run_env: 'rhw' # 'aws'
   user: 'rt'
   host: ''
   port: 0
   password: 'token'
   ssl_ca: './us-east-1-bundle.pem'
   ssl_verify_identity: True
   ssl_verify_cert: True
   auth_plugin_map: {'mysql_clear_password': None}
   config_dbname: 'rtvproc'
   radial_dbname: 'hfradar'
```

#### Input Files Needed
| File Type | Desired Location in Working Directory |
| --- | --- |
| .ruv | $radial_local_dir |
| .nc | $interm_local_dir |


#### Output Files Produced
All output files will be printed to the output.txt file, which is just a dump of the output handoff object from the AIM.  This handoff object gives every output file a "Label" which is what we are describing here.
| File Type | File Token Label | Type of Output<br>(Primary, Intermediate, Diagnostic) |
| --- | --- | --- |
| output netCDF files | | Primary |
| log  |  | Diagnositc |
| intermediate netCDF files|  | Intermediate |


## Test Cases
A full suite of test cases can be found at `/data/smcd12/ASSISTT_DATA/HFRnet/test_cases`.
There are different directories for each release version; please use the most current one.  Copy the files in the `input/` directory to your working directory and then compare your outputs with those found in the `output/` directory.  Do not run your test directly in these directories.

| Test Case Path | Purpose | Config YAML specifications |
| --- | --- | --- |
| USHI_20230104 | Test case for USHI domain 2023/01/04 | test_data/config_hfr.yaml |


*(Because of markdown limitations, show configuration needs in key=value pair notation instead of yaml notation.)*

## Dependencies
### Upstream
- N/A

### Downstream
- N/A

## Appendix
- N/A
