aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws/m3l3l1j4
docker build -t flask-imghost https://github.com/tortxof/flask-imghost.git
docker tag flask-imghost:latest public.ecr.aws/m3l3l1j4/flask-imghost:latest
docker push public.ecr.aws/m3l3l1j4/flask-imghost:latest
