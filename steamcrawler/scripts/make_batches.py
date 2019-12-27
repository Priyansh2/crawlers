import os,re,sys,json
from random import shuffle
review_urls_path = os.getcwd().split("scripts")[0].strip()+'output/review_urls'
if not os.listdir(review_urls_path):
	print(f'Empty dir!! {review_urls_path}')
	print("\nClosing program...\n")
	sys.exit()
files= [(os.path.join(review_urls_path,file),file) for file in os.listdir(review_urls_path)]
print(len(files))
t = int(len(files)/10)
output_dir=review_urls_path.split("review_urls")[0]+"batches"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
prefix = "batch"
def chunkify(lst,n):
	return [lst[i::n] for i in range(n)]
chunks = chunkify(files,t)
s=0
for chunk in chunks:
	s+=len(chunk)
	assert len(list(set(chunk)))-len(chunk)==0
assert s==len(files)

i=1
for chunk in chunks:
	new_file_dir=os.path.join(output_dir,prefix+str(i))
	if not os.path.exists(new_file_dir):
			os.makedirs(new_file_dir)
	for old_file_path,file_name in chunk:
		os.rename(old_file_path,os.path.join(new_file_dir,file_name))
	i+=1