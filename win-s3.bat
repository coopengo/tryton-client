FOR %%I in (.\coog-*) 	DO (
	aws --region "eu-central-1" s3 cp %%I s3://coog-client/
)
pause>nul
