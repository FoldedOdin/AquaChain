import boto3
lam = boto3.client('lambda', region_name='ap-south-1')
fns = lam.list_functions()['Functions']
for f in sorted(fns, key=lambda x: x['FunctionName']):
    print(f["FunctionName"])
